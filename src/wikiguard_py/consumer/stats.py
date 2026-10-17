"""Records live stream statistics — called once per event the consumer
processes, independent of whether any rule fires. This is what lets the
dashboard prove the system is alive even when alerts (rare by nature) are
quiet.
"""

import time

from wikiguard_py.domain.models import WikiEditEvent
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


async def record_event_stats(redis, event: WikiEditEvent) -> None:
    now = time.time()

    await redis.incr(TOTAL_EVENTS_KEY)
    await redis.incr(BOT_EVENTS_KEY if event.is_bot else HUMAN_EVENTS_KEY)
    await redis.zincrby(WIKI_COUNTS_KEY, 1, event.server_name)
    await redis.zincrby(
        PAGE_COUNTS_KEY, 1, f"{event.server_name}{PAGE_COUNT_DELIMITER}{event.page_title}"
    )
    await redis.set(LAST_EVENT_AT_KEY, now)

    # Same sliding-window idiom as WindowCountEvaluator (domain/evaluators.py):
    # add, trim anything older than the window, refresh the safety TTL.
    await redis.zadd(THROUGHPUT_KEY, {f"{event.event_id}:{now}": now})
    await redis.zremrangebyscore(THROUGHPUT_KEY, "-inf", now - THROUGHPUT_WINDOW_SECONDS)
    await redis.expire(THROUGHPUT_KEY, THROUGHPUT_WINDOW_SECONDS * 2)

    # Bots dominate edit volume (seen in real traffic) — excluded so "top
    # editors" reflects actual human activity, not whichever bot runs most.
    if not event.is_bot:
        await redis.zincrby(EDITOR_COUNTS_KEY, 1, event.user)

    # One counter per wall-clock minute, each expiring on its own after the
    # trend window — lets the API read back a 30-point trend with one MGET,
    # without ever storing individual events.
    minute_key = f"{TREND_BUCKET_PREFIX}:{int(now // 60)}"
    await redis.incr(minute_key)
    await redis.expire(minute_key, TREND_WINDOW_MINUTES * 60 + 60)

    # Simple read-then-write "keep the bigger one" — not atomic, so two
    # consumer replicas (Stage 8) could theoretically race. Acceptable for a
    # display-only "fun fact": a wrong value self-corrects on the next
    # bigger edit, and this is never read for a business decision.
    current_biggest = await redis.hget(BIGGEST_EDIT_KEY, "byte_change")
    if current_biggest is None or abs(event.byte_change) > abs(int(current_biggest)):
        await redis.hset(
            BIGGEST_EDIT_KEY,
            mapping={
                "page_title": event.page_title,
                "server_name": event.server_name,
                "user": event.user,
                "byte_change": str(event.byte_change),
            },
        )
