"""Rule evaluators — pure decision logic, no I/O.

A "rule" here is not yet the Postgres-backed AlertRule from Stage 5 — that
model doesn't exist yet. This is the minimal shape the evaluator needs to
make a decision, decoupled from how rules are eventually stored.
"""

from wikiguard_py.domain.models import WikiEditEvent


class ThresholdEvaluator:
    def __init__(self, byte_threshold: int) -> None:
        self.byte_threshold = byte_threshold

    def evaluate(self, event: WikiEditEvent) -> bool:
        return abs(event.byte_change) >= self.byte_threshold
