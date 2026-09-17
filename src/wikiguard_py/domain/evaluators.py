"""Rule evaluators — decision logic behind a shared evaluate() interface.

A "rule" here is not yet the Postgres-backed AlertRule from Stage 5 — that
model doesn't exist yet. This is the minimal shape each evaluator needs to
make a decision, decoupled from how rules are eventually stored.

evaluate() is async on every evaluator, even ones (like ThresholdEvaluator)
that never actually await anything — see ADR-0006: the consumer holds a
mixed list of evaluator types and calls them identically, so the interface
has to be uniform even where a given implementation doesn't need it.
"""

from redis.asyncio import Redis

from wikiguard_py.domain.models import WikiEditEvent


class ThresholdEvaluator:
    def __init__(self, byte_threshold: int) -> None:
        self.byte_threshold = byte_threshold

    async def evaluate(self, event: WikiEditEvent) -> bool:
        return abs(event.byte_change) >= self.byte_threshold


class WindowCountEvaluator:
    """Flags a page with too many edits within a rolling time window
    ("edit war" detection) — unlike ThresholdEvaluator, this rule needs
    memory across events, kept in Redis. The key is scoped by rule_id AND
    page, never rule_id alone — a global, page-less key would share one
    counter across all of Wikipedia and trip constantly under real edit
    volume (the documented bug in wiki-guard's SlidingWindowService that
    this avoids).
    """

    def __init__(
        self,
        redis: Redis,
        rule_id: str,
        window_seconds: int,
        edit_count_threshold: int,
    ) -> None:
        self.redis = redis
        self.rule_id = rule_id
        self.window_seconds = window_seconds
        self.edit_count_threshold = edit_count_threshold

    async def evaluate(self, event: WikiEditEvent) -> bool:
        key = f"rule:{self.rule_id}:{event.page_title}:window"
        cutoff = event.timestamp - self.window_seconds

        await self.redis.zadd(key, {event.event_id: event.timestamp})
        await self.redis.zremrangebyscore(key, "-inf", f"({cutoff}")
        await self.redis.expire(key, self.window_seconds * 2)
        count = await self.redis.zcard(key)

        return count >= self.edit_count_threshold
