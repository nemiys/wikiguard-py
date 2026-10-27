"""Pydantic schema tests — Create/Update/Read for both rule types.

Pure validation, no database involved.
"""

from wikiguard_py.persistence.schemas import (
    ThresholdRuleCreate,
    ThresholdRuleUpdate,
    WindowCountRuleCreate,
    WindowCountRuleUpdate,
)


def test_threshold_rule_create_defaults_is_active_true():
    rule = ThresholdRuleCreate(byte_threshold=500)
    assert rule.is_active is True


def test_threshold_rule_create_respects_explicit_is_active():
    rule = ThresholdRuleCreate(byte_threshold=500, is_active=False)
    assert rule.is_active is False


def test_threshold_rule_update_all_fields_default_none():
    update = ThresholdRuleUpdate()
    assert update.byte_threshold is None
    assert update.is_active is None


def test_window_count_rule_create_defaults_is_active_true():
    rule = WindowCountRuleCreate(window_seconds=60, edit_count_threshold=5)
    assert rule.is_active is True


def test_window_count_rule_create_respects_explicit_is_active():
    rule = WindowCountRuleCreate(window_seconds=60, edit_count_threshold=5, is_active=False)
    assert rule.is_active is False


def test_window_count_rule_update_all_fields_default_none():
    update = WindowCountRuleUpdate()
    assert update.window_seconds is None
    assert update.edit_count_threshold is None
    assert update.is_active is None
