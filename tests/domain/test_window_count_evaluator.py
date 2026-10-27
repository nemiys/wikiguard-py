import pytest
from redis.asyncio import Redis

from wikiguard_py.domain.evaluators import WindowCountEvaluator


@pytest.fixture
async def redis_client():
    client = Redis(host="localhost", port=6380, decode_responses=True)
    yield client
    async for key in client.scan_iter("rule:test-*"):
        await client.delete(key)
    await client.aclose()


async def test_count_below_threshold_does_not_fire(redis_client, make_event):
    evaluator = WindowCountEvaluator(
        redis=redis_client, rule_id="test-below", window_seconds=60, edit_count_threshold=5
    )
    event = make_event(page_title="Test Page A", timestamp=1_700_000_000)
    assert await evaluator.evaluate(event) is False


async def test_count_reaches_threshold_fires(redis_client, make_event):
    evaluator = WindowCountEvaluator(
        redis=redis_client, rule_id="test-reaches", window_seconds=60, edit_count_threshold=3
    )
    base_ts = 1_700_000_000
    result = False
    for i in range(3):
        event = make_event(
            page_title="Test Page B", event_id=f"hewiki:{i}", revision_id=i, timestamp=base_ts + i
        )
        result = await evaluator.evaluate(event)
    assert result is True
    assert evaluator.last_count == 3


async def test_old_edits_fall_out_of_window(redis_client, make_event):
    evaluator = WindowCountEvaluator(
        redis=redis_client, rule_id="test-window", window_seconds=60, edit_count_threshold=2
    )
    old_event = make_event(
        page_title="Test Page C", event_id="hewiki:1", revision_id=1, timestamp=1_700_000_000
    )
    await evaluator.evaluate(old_event)

    # 200 seconds later, outside the 60-second window — the old edit should
    # already be evicted, leaving only this one in the count.
    new_event = make_event(
        page_title="Test Page C", event_id="hewiki:2", revision_id=2, timestamp=1_700_000_200
    )
    assert await evaluator.evaluate(new_event) is False


async def test_edit_exactly_at_window_edge_still_counts(redis_client, make_event):
    """zremrangebyscore trims strictly older than the cutoff ("(cutoff" is
    exclusive) — an edit exactly `window_seconds` old is the oldest one
    still inside the window, not outside it."""
    evaluator = WindowCountEvaluator(
        redis=redis_client, rule_id="test-edge", window_seconds=60, edit_count_threshold=2
    )
    base_ts = 1_700_000_000
    old_event = make_event(
        page_title="Test Page Edge", event_id="hewiki:1", revision_id=1, timestamp=base_ts
    )
    await evaluator.evaluate(old_event)

    edge_event = make_event(
        page_title="Test Page Edge", event_id="hewiki:2", revision_id=2, timestamp=base_ts + 60
    )
    assert await evaluator.evaluate(edge_event) is True
    assert evaluator.last_count == 2


async def test_different_pages_counted_separately(redis_client, make_event):
    """Guards against the wiki-guard bug: a global key without the page in
    it would let unrelated pages share one counter."""
    evaluator = WindowCountEvaluator(
        redis=redis_client, rule_id="test-scope", window_seconds=60, edit_count_threshold=2
    )
    base_ts = 1_700_000_000
    event_page_x = make_event(
        page_title="Page X", event_id="hewiki:1", revision_id=1, timestamp=base_ts
    )
    event_page_y = make_event(
        page_title="Page Y", event_id="hewiki:2", revision_id=2, timestamp=base_ts + 1
    )
    await evaluator.evaluate(event_page_x)
    result = await evaluator.evaluate(event_page_y)
    assert result is False
