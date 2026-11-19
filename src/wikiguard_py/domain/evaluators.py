"""Rule evaluators — decision logic behind a shared evaluate() interface.

Evaluators hold only what they need to make a decision, decoupled from how
rules are stored in Postgres.

evaluate() is async on every evaluator, even ones (like ThresholdEvaluator)
that never actually await anything — see ADR-0005: the consumer holds a
mixed list of evaluator types and calls them identically, so the interface
has to be uniform even where a given implementation doesn't need it.
"""

from redis.asyncio import Redis

from wikiguard_py.domain.models import WikiEditEvent


class ThresholdEvaluator:
    def __init__(self, rule_id: int, byte_threshold: int) -> None:
        self.rule_id = rule_id
        self.byte_threshold = byte_threshold

    async def evaluate(self, event: WikiEditEvent) -> bool:
        return abs(event.byte_change) >= self.byte_threshold


class WindowCountEvaluator:
    """Flags a page with too many edits within a rolling time window
    ("edit war" detection) — unlike ThresholdEvaluator, this rule needs
    memory across events, kept in Redis. The key is scoped by rule_id AND
    page, never rule_id alone — a global, page-less key would share one
    counter across all of Wikipedia and trip constantly under real edit
    volume.
    """

    def __init__(
        self,
        redis: Redis,
        rule_id: int | str,
        window_seconds: int,
        edit_count_threshold: int,
    ) -> None:
        self.redis = redis
        self.rule_id = rule_id
        self.window_seconds = window_seconds
        self.edit_count_threshold = edit_count_threshold
        self.last_count = 0

    async def evaluate(self, event: WikiEditEvent) -> bool:
        key = f"rule:{self.rule_id}:{event.page_title}:window"
        cutoff = event.timestamp - self.window_seconds

        await self.redis.zadd(key, {event.event_id: event.timestamp})
        await self.redis.zremrangebyscore(key, "-inf", f"({cutoff}")
        await self.redis.expire(key, self.window_seconds * 2)
        count = await self.redis.zcard(key)
        self.last_count = count

        if count < self.edit_count_threshold:
            return False
        # One alert per page per window (ADR-0007): the rest of the same burst is still
        # counted, but only the edit that crosses the threshold raises an alert. SET NX
        # succeeds for exactly one caller until the marker expires.
        alerted_key = f"rule:{self.rule_id}:{event.page_title}:alerted"
        first = await self.redis.set(alerted_key, event.event_id, nx=True, ex=self.window_seconds)
        return bool(first)
