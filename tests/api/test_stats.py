"""Tests for GET /stats — reads Redis directly, not Postgres.

Uses the same isolation convention as tests/consumer/test_stats.py: a
separate Redis *database* (db=1), fully apart from the live app's db=0,
so these tests can set exact values and never touch real demo data.
"""

import time

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from wikiguard_py.main import app
from wikiguard_py.redis_client import get_redis
from wikiguard_py.stream_stats import (
    BIGGEST_EDIT_KEY,
    BOT_EVENTS_KEY,
    EDITOR_COUNTS_KEY,
    HUMAN_EVENTS_KEY,
    LAST_EVENT_AT_KEY,
    PAGE_COUNT_DELIMITER,
    PAGE_COUNTS_KEY,
    THROUGHPUT_KEY,
    TOTAL_EVENTS_KEY,
    TREND_BUCKET_PREFIX,
    WIKI_COUNTS_KEY,
)


@pytest.fixture
async def redis_client():
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


@pytest.fixture
async def stats_client(redis_client):
    async def override_get_redis():
        return redis_client

    app.dependency_overrides[get_redis] = override_get_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def test_empty_state_all_zero_or_empty(stats_client):
    response = await stats_client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 0
    assert body["bot_events"] == 0
    assert body["human_events"] == 0
    assert body["events_last_60s"] == 0
    assert body["last_event_seconds_ago"] is None
    assert body["top_wikis"] == []
    assert body["top_pages"] == []
    assert body["top_editors"] == []
    assert body["biggest_edit"] is None
    assert len(body["activity_trend"]) == 30


async def test_total_events_reflects_redis_value(stats_client, redis_client):
    await redis_client.set(TOTAL_EVENTS_KEY, 42)
    body = (await stats_client.get("/stats")).json()
    assert body["total_events"] == 42


async def test_bot_and_human_events_reflect_redis_values(stats_client, redis_client):
    await redis_client.set(BOT_EVENTS_KEY, 3)
    await redis_client.set(HUMAN_EVENTS_KEY, 7)
    body = (await stats_client.get("/stats")).json()
    assert body["bot_events"] == 3
    assert body["human_events"] == 7


async def test_events_last_60s_counts_entries_within_window(stats_client, redis_client):
    now = time.time()
    await redis_client.zadd(THROUGHPUT_KEY, {"a": now - 10, "b": now - 20})
    body = (await stats_client.get("/stats")).json()
    assert body["events_last_60s"] == 2


async def test_events_last_60s_excludes_entries_outside_window(stats_client, redis_client):
    now = time.time()
    await redis_client.zadd(THROUGHPUT_KEY, {"old": now - 120})
    body = (await stats_client.get("/stats")).json()
    assert body["events_last_60s"] == 0


async def test_last_event_seconds_ago_computed_from_last_event_at(stats_client, redis_client):
    await redis_client.set(LAST_EVENT_AT_KEY, time.time() - 5)
    body = (await stats_client.get("/stats")).json()
    assert body["last_event_seconds_ago"] is not None
    assert 4.5 <= body["last_event_seconds_ago"] <= 15


async def test_top_wikis_ordered_by_count_desc(stats_client, redis_client):
    await redis_client.zadd(WIKI_COUNTS_KEY, {"small.wikipedia.org": 2, "big.wikipedia.org": 9})
    body = (await stats_client.get("/stats")).json()
    assert [w["server_name"] for w in body["top_wikis"]] == [
        "big.wikipedia.org",
        "small.wikipedia.org",
    ]
    assert body["top_wikis"][0]["event_count"] == 9


async def test_top_pages_parses_delimiter(stats_client, redis_client):
    member = f"en.wikipedia.org{PAGE_COUNT_DELIMITER}Some Page"
    await redis_client.zadd(PAGE_COUNTS_KEY, {member: 5})
    body = (await stats_client.get("/stats")).json()
    assert body["top_pages"] == [
        {"server_name": "en.wikipedia.org", "page_title": "Some Page", "event_count": 5}
    ]


async def test_top_editors_ordered_by_count_desc(stats_client, redis_client):
    await redis_client.zadd(EDITOR_COUNTS_KEY, {"Alice": 1, "Bob": 4})
    body = (await stats_client.get("/stats")).json()
    assert [e["user"] for e in body["top_editors"]] == ["Bob", "Alice"]


async def test_biggest_edit_reflects_redis_hash_when_set(stats_client, redis_client):
    await redis_client.hset(
        BIGGEST_EDIT_KEY,
        mapping={
            "page_title": "Big Page",
            "server_name": "en.wikipedia.org",
            "user": "SomeUser",
            "byte_change": -9000,
        },
    )
    body = (await stats_client.get("/stats")).json()
    assert body["biggest_edit"] == {
        "page_title": "Big Page",
        "server_name": "en.wikipedia.org",
        "user": "SomeUser",
        "byte_change": -9000,
    }


async def test_activity_trend_reflects_current_minute_bucket(stats_client, redis_client):
    current_minute = int(time.time() // 60)
    await redis_client.set(f"{TREND_BUCKET_PREFIX}:{current_minute}", 6)
    body = (await stats_client.get("/stats")).json()
    assert len(body["activity_trend"]) == 30
    assert body["activity_trend"][-1] == 6
