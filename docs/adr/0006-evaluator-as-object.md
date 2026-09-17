# ADR-0006: Rule evaluators are objects with a shared `evaluate()` interface, not a value + function

## Status
Accepted

## Context
`ThresholdEvaluator` (Stage 1) decides whether a single edit's byte-change
crosses a configured threshold. Stage 4 will add `WindowCountEvaluator` — a
second rule type that decides whether a page has been edited too many times
within a time window, backed by Redis. Both rule types will eventually run
inside the same consumer loop (Stage 3+), which needs to check every active
rule against every incoming event without knowing, ahead of time, how many
rule types exist or what data each one needs internally.

## Decision
Each rule type is a class holding its own configuration/state (e.g.
`ThresholdEvaluator.byte_threshold`, or `WindowCountEvaluator`'s window
length + Redis client), exposing one shared method: `evaluate(event) ->
bool`. The consumer loop depends only on that shared interface, never on how
a specific rule type reaches its answer internally.

## Alternatives considered
- **A plain value + a standalone function** (e.g. `byte_threshold = 300` and
  `def is_suspicious(byte_threshold, event): ...`): works for a single rule
  type with a single parameter, but breaks down the moment a second rule
  type needs a different set of parameters (window length, count threshold,
  a Redis connection) — the consumer would need to know each rule type's
  specific parameter list to call it correctly, defeating the point of
  running an arbitrary list of active rules generically.
- **One function/class with a branch per rule type**
  (`if rule.type == "threshold": ... elif rule.type == "window_count":
  ...`): keeps a single entry point, but means every new rule type requires
  editing that shared function, and mixes each rule type's internal logic
  into one place instead of keeping them independent and independently
  testable (as Stage 1's evaluator tests already are).

## Consequences
Adding a new rule type (Window-Count in Stage 4, and any future rule) means
writing a new class in `domain/evaluators.py` with an `evaluate(event) ->
bool` method — the consumer loop (`consumer/main.py`) does not change at
all. Stage 5's dynamic rule loading from Postgres can build a mixed list of
different evaluator objects and treat them uniformly, regardless of type.
