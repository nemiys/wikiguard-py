from wikiguard_py.domain.evaluators import ThresholdEvaluator


def test_change_below_threshold_does_not_fire(make_event):
    evaluator = ThresholdEvaluator(byte_threshold=500)
    event = make_event(byte_change=100)
    assert evaluator.evaluate(event) is False


def test_change_above_threshold_fires(make_event):
    evaluator = ThresholdEvaluator(byte_threshold=500)
    event = make_event(byte_change=800)
    assert evaluator.evaluate(event) is True


def test_change_exactly_at_threshold_fires(make_event):
    evaluator = ThresholdEvaluator(byte_threshold=500)
    event = make_event(byte_change=500)
    assert evaluator.evaluate(event) is True


def test_large_negative_change_fires(make_event):
    """A mass deletion is just as suspicious as a mass addition."""
    evaluator = ThresholdEvaluator(byte_threshold=500)
    event = make_event(byte_change=-800)
    assert evaluator.evaluate(event) is True
