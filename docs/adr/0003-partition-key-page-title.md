# ADR-0003: Kafka partition key = page_title

## Status
Accepted

## Context
The `wiki-edit-events` topic needs a partition key. Kafka guarantees message
order only *within* a single partition, never across partitions. The
Window-Count rule (edit-war detection) counts edits per page within a rolling
time window, so it depends on seeing that page's edits in the right order.

## Decision
`key = page_title`. The topic runs with 3 partitions — enough for real
parallel consumption and a meaningful consumer-group rebalance, without the
operational overhead a much larger partition count would add at this scale.

## Alternatives considered
- `event_id`: has no business meaning for routing — using it as the key would
  scatter one page's edits across partitions essentially at random, breaking
  the ordering guarantee the Window-Count rule needs. `event_id`'s only job
  is deduplication (see ADR-0004); it plays no role in partitioning.
- `user`: would be the right key for a *per-user* pattern (e.g. "same user
  vandalizing many pages"), not the current per-page scope. Not chosen
  because no such rule exists yet — see Consequences.

## Consequences
All edits to the same page are guaranteed to be processed in order by a
single consumer. A future per-user rule does not require touching Kafka at
all — it is implemented as a new evaluator in the consumer, keyed by `user`
in Redis instead of `page`; Kafka ordering is not required for that rule's
correctness because the sliding-window computation in Redis is timestamp-
based, not arrival-order-based.
