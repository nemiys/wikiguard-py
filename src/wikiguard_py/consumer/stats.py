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

    # Simple read-then-write "keep the bigger one" — not atomic, so two
    # consumer replicas could theoretically race. Acceptable for a
    # display-only "fun fact": a wrong value self-corrects on the next
    # bigger edit, and this is never read for a business decision.
    current_biggest = await redis.hget(BIGGEST_EDIT_KEY, "byte_change")

    # Every write below goes out in one round trip. Not a transaction: these are
    # independent display counters, and a half-applied batch is harmless.
    pipe = redis.pipeline(transaction=False)
    pipe.incr(TOTAL_EVENTS_KEY)
    pipe.incr(BOT_EVENTS_KEY if event.is_bot else HUMAN_EVENTS_KEY)
    pipe.zincrby(WIKI_COUNTS_KEY, 1, event.server_name)
    pipe.zincrby(PAGE_COUNTS_KEY, 1, f"{event.server_name}{PAGE_COUNT_DELIMITER}{event.page_title}")
    pipe.set(LAST_EVENT_AT_KEY, now)

    # Same sliding-window idiom as WindowCountEvaluator (domain/evaluators.py):
    # add, trim anything older than the window, refresh the safety TTL.
    pipe.zadd(THROUGHPUT_KEY, {f"{event.event_id}:{now}": now})
    pipe.zremrangebyscore(THROUGHPUT_KEY, "-inf", now - THROUGHPUT_WINDOW_SECONDS)
    pipe.expire(THROUGHPUT_KEY, THROUGHPUT_WINDOW_SECONDS * 2)

    # Bots dominate edit volume (seen in real traffic) — excluded so "top
    # editors" reflects actual human activity, not whichever bot runs most.
    if not event.is_bot:
        pipe.zincrby(EDITOR_COUNTS_KEY, 1, event.user)

    # One counter per wall-clock minute, each expiring on its own after the
    # trend window — lets the API read back a 30-point trend with one MGET,
    # without ever storing individual events.
    minute_key = f"{TREND_BUCKET_PREFIX}:{int(now // 60)}"
    pipe.incr(minute_key)
    pipe.expire(minute_key, TREND_WINDOW_MINUTES * 60 + 60)

    if current_biggest is None or abs(event.byte_change) > abs(int(current_biggest)):
        pipe.hset(
            BIGGEST_EDIT_KEY,
            mapping={
                "page_title": event.page_title,
                "server_name": event.server_name,
                "user": event.user,
                "byte_change": str(event.byte_change),
            },
        )
    await pipe.execute()
