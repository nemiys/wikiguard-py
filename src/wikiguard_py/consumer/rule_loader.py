"""Builds the current list of active evaluators from Postgres.

Bridges persistence (DB rows) and domain (evaluator objects) — this is
exactly the kind of translation that doesn't belong in either of those
packages alone.
"""

from redis.asyncio import Redis
from sqlalchemy import select

from wikiguard_py.domain.evaluators import ThresholdEvaluator, WindowCountEvaluator
from wikiguard_py.persistence.database import async_session_factory
from wikiguard_py.persistence.models import ThresholdRuleModel, WindowCountRuleModel


async def load_evaluators(redis: Redis) -> list[ThresholdEvaluator | WindowCountEvaluator]:
    async with async_session_factory() as session:
        threshold_rows = (
            await session.execute(select(ThresholdRuleModel).where(ThresholdRuleModel.is_active))
        ).scalars()
        window_rows = (
            await session.execute(
                select(WindowCountRuleModel).where(WindowCountRuleModel.is_active)
            )
        ).scalars()

        evaluators: list[ThresholdEvaluator | WindowCountEvaluator] = [
            ThresholdEvaluator(rule_id=row.id, byte_threshold=row.byte_threshold)
            for row in threshold_rows
        ]
        evaluators += [
            WindowCountEvaluator(
                redis=redis,
                rule_id=row.id,
                window_seconds=row.window_seconds,
                edit_count_threshold=row.edit_count_threshold,
            )
            for row in window_rows
        ]
        return evaluators
