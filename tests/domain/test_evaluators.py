from wikiguard_py.domain.evaluators import ThresholdEvaluator


async def test_change_below_threshold_does_not_fire(make_event):
    evaluator = ThresholdEvaluator(rule_id=1, byte_threshold=500)
    event = make_event(byte_change=100)
    assert await evaluator.evaluate(event) is False


async def test_change_above_threshold_fires(make_event):
    evaluator = ThresholdEvaluator(rule_id=1, byte_threshold=500)
    event = make_event(byte_change=800)
    assert await evaluator.evaluate(event) is True


async def test_change_exactly_at_threshold_fires(make_event):
    evaluator = ThresholdEvaluator(rule_id=1, byte_threshold=500)
    event = make_event(byte_change=500)
    assert await evaluator.evaluate(event) is True


async def test_large_negative_change_fires(make_event):
    """A mass deletion is just as suspicious as a mass addition."""
    evaluator = ThresholdEvaluator(rule_id=1, byte_threshold=500)
    event = make_event(byte_change=-800)
    assert await evaluator.evaluate(event) is True
