import pytest
from redis.asyncio import Redis

from wikiguard_py.consumer.stats import record_event_stats
from wikiguard_py.domain.models import WikiEditEvent
from wikiguard_py.stream_stats import (
    BIGGEST_EDIT_KEY,
    BOT_EVENTS_KEY,
    EDITOR_COUNTS_KEY,
    HUMAN_EVENTS_KEY,
    LAST_EVENT_AT_KEY,
    PAGE_COUNTS_KEY,
    THROUGHPUT_KEY,
    TOTAL_EVENTS_KEY,
    TREND_BUCKET_PREFIX,
    WIKI_COUNTS_KEY,
)


def make_event(**overrides) -> WikiEditEvent:
    defaults = dict(
        event_id="hewiki:123",
        page_title="עמוד ראשי",
        wiki="hewiki",
        server_name="he.wikipedia.org",
        user="some_user",
        byte_change=100,
        is_bot=False,
        namespace=0,
        revision_id=123,
        timestamp=1_700_000_000,
    )
    defaults.update(overrides)
    return WikiEditEvent(**defaults)


@pytest.fixture
async def redis_client():
    # Unlike WindowCountEvaluator's per-rule keys (safely isolated by a
    # "test-" rule_id prefix), these stats keys are global — there's no way
    # to namespace them per-test without changing what they mean in
    # production. So tests run against a separate Redis *database* (db=1)
    # instead, fully isolated from the real app's db=0 — deleting these
    # keys here can never wipe out live demo data.
    client = Redis(host="localhost", port=6380, db=1, decode_responses=True)
    yield client
    keys = (
        TOTAL_EVENTS_KEY,
        BOT_EVENTS_KEY,
        HUMAN_EVENTS_KEY,
        THROUGHPUT_KEY,
        WIKI_COUNTS_KEY,
        PAGE_COUNTS_KEY,
        LAST_EVENT_AT_KEY,
        EDITOR_COUNTS_KEY,
        BIGGEST_EDIT_KEY,
    )
    for key in keys:
        await client.delete(key)
    async for key in client.scan_iter(f"{TREND_BUCKET_PREFIX}:*"):
        await client.delete(key)
    await client.aclose()


async def test_total_events_increments(redis_client):
    # These keys are global and shared with whatever is really running
    # against this Redis (consumer/dev server) — asserting on *deltas*
    # rather than absolute values keeps the test correct even if real
    # traffic is being recorded concurrently.
    before = int(await redis_client.get(TOTAL_EVENTS_KEY) or 0)
    await record_event_stats(redis_client, make_event())
    await record_event_stats(redis_client, make_event(event_id="hewiki:124", revision_id=124))
    after = int(await redis_client.get(TOTAL_EVENTS_KEY) or 0)
    # >= rather than == : INCR only ever goes up, so concurrent real traffic
    # can add to the delta but never hide our own two increments.
    assert after - before >= 2


async def test_bot_and_human_counted_separately(redis_client):
    bot_before = int(await redis_client.get(BOT_EVENTS_KEY) or 0)
    human_before = int(await redis_client.get(HUMAN_EVENTS_KEY) or 0)
    await record_event_stats(redis_client, make_event(is_bot=True))
    await record_event_stats(redis_client, make_event(is_bot=False, event_id="hewiki:124"))
    assert int(await redis_client.get(BOT_EVENTS_KEY)) - bot_before >= 1
    assert int(await redis_client.get(HUMAN_EVENTS_KEY)) - human_before >= 1


async def test_throughput_window_trims_old_entries(redis_client, monkeypatch):
    times = iter([1_700_000_000.0, 1_700_000_200.0])
    monkeypatch.setattr("wikiguard_py.consumer.stats.time.time", lambda: next(times))

    old_event = make_event()
    await record_event_stats(redis_client, old_event)
    old_member = f"{old_event.event_id}:1700000000.0"

    # 200 seconds later — outside the 60-second throughput window, so the
    # first entry should already be evicted by the time this one is added.
    # Checking this specific member (not zcard) keeps the test correct even
    # with real concurrent traffic sharing the same key.
    await record_event_stats(redis_client, make_event(event_id="hewiki:124", revision_id=124))
    assert await redis_client.zscore(THROUGHPUT_KEY, old_member) is None


async def test_bot_edit_excluded_from_editor_counts(redis_client):
    await record_event_stats(redis_client, make_event(is_bot=True, user="SomeBot"))
    assert await redis_client.zscore(EDITOR_COUNTS_KEY, "SomeBot") is None


async def test_human_edit_counted_in_editor_counts(redis_client):
    await record_event_stats(redis_client, make_event(is_bot=False, user="SomeHuman"))
    assert await redis_client.zscore(EDITOR_COUNTS_KEY, "SomeHuman") == 1.0


async def test_trend_buckets_separate_minutes(redis_client, monkeypatch):
    # Two events a minute apart land in different per-minute buckets.
    times = iter([1_700_000_000.0, 1_700_000_060.0])
    monkeypatch.setattr("wikiguard_py.consumer.stats.time.time", lambda: next(times))

    await record_event_stats(redis_client, make_event())
    await record_event_stats(redis_client, make_event(event_id="hewiki:124", revision_id=124))

    first_minute_key = f"{TREND_BUCKET_PREFIX}:{1_700_000_000 // 60}"
    second_minute_key = f"{TREND_BUCKET_PREFIX}:{1_700_000_060 // 60}"
    assert await redis_client.get(first_minute_key) == "1"
    assert await redis_client.get(second_minute_key) == "1"


async def test_biggest_edit_updates_only_when_larger(redis_client):
    await record_event_stats(redis_client, make_event(byte_change=500, page_title="Small"))
    await record_event_stats(redis_client, make_event(byte_change=-100, page_title="Smaller"))
    assert await redis_client.hget(BIGGEST_EDIT_KEY, "page_title") == "Small"

    await record_event_stats(redis_client, make_event(byte_change=-900, page_title="Biggest"))
    assert await redis_client.hget(BIGGEST_EDIT_KEY, "page_title") == "Biggest"
    assert await redis_client.hget(BIGGEST_EDIT_KEY, "byte_change") == "-900"
