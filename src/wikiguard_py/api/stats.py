"""HTTP read access to live stream statistics — reads Redis directly, not
Postgres: this data is transient display state, not a durable business record.
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
# decode_responses=True the client is actually constructed with — this cast
# documents that gap once, instead of silencing mypy at every call site below.
def _as_str_pairs(pairs: object) -> list[tuple[str, float]]:
    return cast(list[tuple[str, float]], pairs)


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
    current_minute = int(now // 60)
    trend_minutes = range(current_minute - TREND_WINDOW_MINUTES + 1, current_minute + 1)
    trend_keys = [f"{TREND_BUCKET_PREFIX}:{minute}" for minute in trend_minutes]

    # Every read in one round trip, answered in the order it was queued.
    pipe = redis.pipeline(transaction=False)
    pipe.mget([TOTAL_EVENTS_KEY, BOT_EVENTS_KEY, HUMAN_EVENTS_KEY, LAST_EVENT_AT_KEY])
    pipe.zcount(THROUGHPUT_KEY, now - THROUGHPUT_WINDOW_SECONDS, "+inf")
    pipe.zrevrange(WIKI_COUNTS_KEY, 0, TOP_N - 1, withscores=True)
    pipe.zrevrange(PAGE_COUNTS_KEY, 0, TOP_N - 1, withscores=True)
    pipe.zrevrange(EDITOR_COUNTS_KEY, 0, TOP_N - 1, withscores=True)
    pipe.mget(trend_keys)
    pipe.hgetall(BIGGEST_EDIT_KEY)
    (
        counters,
        events_last_60s,
        wiki_pairs,
        page_pairs,
        editor_pairs,
        raw_trend,
        biggest_edit_data,
    ) = await pipe.execute()

    total_raw, bot_raw, human_raw, last_event_at = counters
    total_events = int(total_raw or 0)
    bot_events = int(bot_raw or 0)
    human_events = int(human_raw or 0)
    last_event_seconds_ago = now - float(last_event_at) if last_event_at else None

    top_wikis = [
        WikiActivity(server_name=server_name, event_count=int(count))
        for server_name, count in _as_str_pairs(wiki_pairs)
    ]

    top_pages = []
    for member, count in _as_str_pairs(page_pairs):
        server_name, page_title = member.split(PAGE_COUNT_DELIMITER, 1)
        top_pages.append(
            PageActivity(server_name=server_name, page_title=page_title, event_count=int(count))
        )

    top_editors = [
        EditorActivity(user=user, event_count=int(count))
        for user, count in _as_str_pairs(editor_pairs)
    ]

    activity_trend = [int(count) if count else 0 for count in raw_trend]

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
