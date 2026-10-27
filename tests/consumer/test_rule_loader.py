"""Tests for load_evaluators — loads active rules from Postgres, skips
inactive ones. Rows are created/cleaned up directly against the real
database (load_evaluators opens its own session, same as record_alert),
scoped by id so cleanup is exact.
"""

from wikiguard_py.consumer.rule_loader import load_evaluators
from wikiguard_py.domain.evaluators import ThresholdEvaluator, WindowCountEvaluator
from wikiguard_py.persistence.database import async_session_factory
from wikiguard_py.persistence.models import ThresholdRuleModel, WindowCountRuleModel


async def make_threshold_rule(**overrides):
    defaults = {"byte_threshold": 500, "is_active": True}
    defaults.update(overrides)
    async with async_session_factory() as session:
        rule = ThresholdRuleModel(**defaults)
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule


async def make_window_count_rule(**overrides):
    defaults = {"window_seconds": 60, "edit_count_threshold": 5, "is_active": True}
    defaults.update(overrides)
    async with async_session_factory() as session:
        rule = WindowCountRuleModel(**defaults)
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule


async def delete_threshold_rule(rule_id):
    async with async_session_factory() as session:
        rule = await session.get(ThresholdRuleModel, rule_id)
        await session.delete(rule)
        await session.commit()


async def delete_window_count_rule(rule_id):
    async with async_session_factory() as session:
        rule = await session.get(WindowCountRuleModel, rule_id)
        await session.delete(rule)
        await session.commit()


async def test_loads_active_threshold_rule():
    rule = await make_threshold_rule(byte_threshold=777, is_active=True)
    try:
        evaluators = await load_evaluators(redis=None)
        matching = [
            e for e in evaluators if isinstance(e, ThresholdEvaluator) and e.rule_id == rule.id
        ]
        assert len(matching) == 1
        assert matching[0].byte_threshold == 777
    finally:
        await delete_threshold_rule(rule.id)


async def test_skips_inactive_threshold_rule():
    rule = await make_threshold_rule(is_active=False)
    try:
        evaluators = await load_evaluators(redis=None)
        assert not any(
            isinstance(e, ThresholdEvaluator) and e.rule_id == rule.id for e in evaluators
        )
    finally:
        await delete_threshold_rule(rule.id)


async def test_loads_active_window_count_rule():
    rule = await make_window_count_rule(window_seconds=120, edit_count_threshold=9, is_active=True)
    try:
        evaluators = await load_evaluators(redis=None)
        matching = [
            e for e in evaluators if isinstance(e, WindowCountEvaluator) and e.rule_id == rule.id
        ]
        assert len(matching) == 1
        assert matching[0].window_seconds == 120
        assert matching[0].edit_count_threshold == 9
    finally:
        await delete_window_count_rule(rule.id)


async def test_skips_inactive_window_count_rule():
    rule = await make_window_count_rule(is_active=False)
    try:
        evaluators = await load_evaluators(redis=None)
        assert not any(
            isinstance(e, WindowCountEvaluator) and e.rule_id == rule.id for e in evaluators
        )
    finally:
        await delete_window_count_rule(rule.id)


async def test_loads_both_rule_types_together():
    threshold_rule = await make_threshold_rule(is_active=True)
    window_rule = await make_window_count_rule(is_active=True)
    try:
        evaluators = await load_evaluators(redis=None)
        assert any(
            isinstance(e, ThresholdEvaluator) and e.rule_id == threshold_rule.id for e in evaluators
        )
        assert any(
            isinstance(e, WindowCountEvaluator) and e.rule_id == window_rule.id for e in evaluators
        )
    finally:
        await delete_threshold_rule(threshold_rule.id)
        await delete_window_count_rule(window_rule.id)
