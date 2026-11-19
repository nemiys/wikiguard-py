"""The stream client against a fake EventStreams server, no network."""

import httpx

from wikiguard_py.producer.wikimedia_stream import stream_recentchanges_with_retry


def sse_body(*events: tuple[str, str]) -> bytes:
    return "".join(f"id: {event_id}\ndata: {data}\n\n" for event_id, data in events).encode()


async def test_a_reconnect_resumes_from_the_last_event_received():
    """The first connection delivers two events and drops. The reconnect must send the id
    of the second one as Last-Event-ID, or the edits made while it was down are lost."""
    requests: list[httpx.Request] = []
    bodies = [
        sse_body(("[1]", '{"n": 1}'), ("[2]", '{"n": 2}')),
        sse_body(("[3]", '{"n": 3}')),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=bodies[len(requests) - 1]
        )

    received = []
    stream = stream_recentchanges_with_retry(transport=httpx.MockTransport(handler))
    async for event in stream:
        received.append(event["n"])
        if len(received) == 3:
            break
    await stream.aclose()

    assert received == [1, 2, 3]
    assert "last-event-id" not in requests[0].headers
    assert requests[1].headers["last-event-id"] == "[2]"


async def test_events_without_data_are_skipped_but_still_move_the_position():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = b"id: [7]\ndata: \n\n" if len(requests) == 1 else sse_body(("[8]", '{"n": 8}'))
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body)

    stream = stream_recentchanges_with_retry(transport=httpx.MockTransport(handler))
    first = await anext(stream)
    await stream.aclose()

    assert first == {"n": 8}
    assert requests[1].headers["last-event-id"] == "[7]"
