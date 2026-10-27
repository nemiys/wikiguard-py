"""HTTP read access to live stream statistics — reads Redis directly, not
Postgres (see architecture-plan.md principle 7: this data is transient
display state, not a durable business record).
"""

import time
from typing import cast

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis

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
    THROUGHPUT_WINDOW_SECONDS,
    TOTAL_EVENTS_KEY,
    TREND_BUCKET_PREFIX,
    TREND_WINDOW_MINUTES,
    WIKI_COUNTS_KEY,
)

router = APIRouter(prefix="/stats", tags=["stats"])

TOP_N = 5


# redis-py's stubs don't narrow responses to str based on the
# decode_responses=True the client is actually constructed with — these
# two casts document that gap once, instead of silencing mypy separately
# at every call site below.
async def _zrevrange_str(redis: Redis, key: str, start: int, end: int) -> list[tuple[str, float]]:
    pairs = await redis.zrevrange(key, start, end, withscores=True)
    return cast(list[tuple[str, float]], pairs)


async def _hgetall_str(redis: Redis, key: str) -> dict[str, str]:
    data = await redis.hgetall(key)
    return cast(dict[str, str], data)


class WikiActivity(BaseModel):
    server_name: str
    event_count: int


class PageActivity(BaseModel):
    server_name: str
    page_title: str
    event_count: int


class EditorActivity(BaseModel):
    user: str
    event_count: int


class BiggestEdit(BaseModel):
    page_title: str
    server_name: str
    user: str
    byte_change: int


class StreamStats(BaseModel):
    total_events: int
    events_last_60s: int
    last_event_seconds_ago: float | None
    bot_events: int
    human_events: int
    top_wikis: list[WikiActivity]
    top_pages: list[PageActivity]
    top_editors: list[EditorActivity]
    activity_trend: list[int]
    biggest_edit: BiggestEdit | None


@router.get("", response_model=StreamStats)
async def get_stats(redis: Redis = Depends(get_redis)) -> StreamStats:
    now = time.time()

    total_events = int(await redis.get(TOTAL_EVENTS_KEY) or 0)
    bot_events = int(await redis.get(BOT_EVENTS_KEY) or 0)
    human_events = int(await redis.get(HUMAN_EVENTS_KEY) or 0)
    events_last_60s = await redis.zcount(
        THROUGHPUT_KEY, now - THROUGHPUT_WINDOW_SECONDS, "+inf"
    )

    last_event_at = await redis.get(LAST_EVENT_AT_KEY)
    last_event_seconds_ago = now - float(last_event_at) if last_event_at else None

    top_wikis = [
        WikiActivity(server_name=server_name, event_count=int(count))
        for server_name, count in await _zrevrange_str(redis, WIKI_COUNTS_KEY, 0, TOP_N - 1)
    ]

    top_pages = []
    for member, count in await _zrevrange_str(redis, PAGE_COUNTS_KEY, 0, TOP_N - 1):
        server_name, page_title = member.split(PAGE_COUNT_DELIMITER, 1)
        top_pages.append(
            PageActivity(server_name=server_name, page_title=page_title, event_count=int(count))
        )

    top_editors = [
        EditorActivity(user=user, event_count=int(count))
        for user, count in await _zrevrange_str(redis, EDITOR_COUNTS_KEY, 0, TOP_N - 1)
    ]

    current_minute = int(now // 60)
    trend_minutes = range(current_minute - TREND_WINDOW_MINUTES + 1, current_minute + 1)
    trend_keys = [f"{TREND_BUCKET_PREFIX}:{minute}" for minute in trend_minutes]
    raw_trend = await redis.mget(trend_keys)
    activity_trend = [int(count) if count else 0 for count in raw_trend]

    biggest_edit_data = await _hgetall_str(redis, BIGGEST_EDIT_KEY)
    biggest_edit = (
        BiggestEdit(
            page_title=biggest_edit_data["page_title"],
            server_name=biggest_edit_data["server_name"],
            user=biggest_edit_data["user"],
            byte_change=int(biggest_edit_data["byte_change"]),
        )
        if biggest_edit_data
        else None
    )

    return StreamStats(
        total_events=total_events,
        events_last_60s=events_last_60s,
        last_event_seconds_ago=last_event_seconds_ago,
        bot_events=bot_events,
        human_events=human_events,
        top_wikis=top_wikis,
        top_pages=top_pages,
        top_editors=top_editors,
        activity_trend=activity_trend,
        biggest_edit=biggest_edit,
    )
