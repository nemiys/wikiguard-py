"""Tests for process_message — the per-event logic extracted from run()'s
Kafka loop (see consumer/main.py). Runs against real evaluators, real
Redis (db=1, isolated from the live app's db=0 — same convention as
test_stats.py), and real Postgres for any alert record_alert writes
(cleaned up by hand, since record_alert opens its own session).
"""

import pytest
from redis.asyncio import Redis
from sqlalchemy import delete, select

from wikiguard_py.consumer.main import process_message
from wikiguard_py.domain.evaluators import ThresholdEvaluator, WindowCountEvaluator
from wikiguard_py.domain.models import WikiEditEvent
from wikiguard_py.persistence.database import async_session_factory
from wikiguard_py.persistence.models import FiredAlertModel
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


@pytest.fixture
async def redis_client():
    # Same db=1 isolation as test_stats.py — never the live app's db=0.
    # record_event_stats (called inside process_message) writes the same
    # global stats keys test_stats.py asserts on, so this must clean up
    # after itself the same way, or it leaks state into those tests.
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


def make_event(**overrides) -> WikiEditEvent:
    defaults = {
        "event_id": "hewiki:123",
        "page_title": "zz_process_message_page",
        "wiki": "hewiki",
        "server_name": "he.wikipedia.org",
        "user": "some_user",
        "byte_change": 100,
        "is_bot": False,
        "namespace": 0,
        "revision_id": 123,
        "timestamp": 1_700_000_000,
    }
    defaults.update(overrides)
    return WikiEditEvent(**defaults)


async def fetch_alerts_for(page_title):
    async with async_session_factory() as session:
        result = await session.execute(
            select(FiredAlertModel).where(FiredAlertModel.page_title == page_title)
        )
        return list(result.scalars())


async def cleanup_alerts_for(page_title):
    async with async_session_factory() as session:
        await session.execute(
            delete(FiredAlertModel).where(FiredAlertModel.page_title == page_title)
        )
        await session.commit()


async def test_bot_edit_produces_no_alert(redis_client):
    page_title = "zz_process_message_bot"
    evaluator = ThresholdEvaluator(rule_id=1, byte_threshold=1)
    try:
        await process_message(
            make_event(page_title=page_title, is_bot=True, byte_change=9000),
            [evaluator],
            redis_client,
        )
        assert await fetch_alerts_for(page_title) == []
    finally:
        await cleanup_alerts_for(page_title)


async def test_threshold_evaluator_triggers_alert(redis_client):
    page_title = "zz_process_message_threshold"
    evaluator = ThresholdEvaluator(rule_id=42, byte_threshold=500)
    try:
        await process_message(
            make_event(page_title=page_title, byte_change=9000), [evaluator], redis_client
        )
        alerts = await fetch_alerts_for(page_title)
        assert len(alerts) == 1
        assert alerts[0].rule_type == "ThresholdEvaluator"
        assert alerts[0].rule_id == 42
        assert alerts[0].edit_count is None
    finally:
        await cleanup_alerts_for(page_title)


async def test_window_count_evaluator_triggers_alert_with_edit_count(redis_client):
    page_title = "zz_process_message_window"
    evaluator = WindowCountEvaluator(
        redis=redis_client, rule_id=7, window_seconds=60, edit_count_threshold=1
    )
    try:
        await process_message(make_event(page_title=page_title), [evaluator], redis_client)
        alerts = await fetch_alerts_for(page_title)
        assert len(alerts) == 1
        assert alerts[0].rule_type == "WindowCountEvaluator"
        assert alerts[0].edit_count == 1
    finally:
        await cleanup_alerts_for(page_title)


async def test_no_matching_rule_produces_no_alert(redis_client):
    page_title = "zz_process_message_no_match"
    evaluator = ThresholdEvaluator(rule_id=1, byte_threshold=9999)
    try:
        await process_message(
            make_event(page_title=page_title, byte_change=10), [evaluator], redis_client
        )
        assert await fetch_alerts_for(page_title) == []
    finally:
        await cleanup_alerts_for(page_title)


async def test_every_processed_event_increments_total_events(redis_client):
    before = int(await redis_client.get(TOTAL_EVENTS_KEY) or 0)
    await process_message(make_event(), [], redis_client)
    after = int(await redis_client.get(TOTAL_EVENTS_KEY) or 0)
    assert after - before >= 1
