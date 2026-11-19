# ADR-0001: Kafka as the ingestion→processing decoupling layer

## Status
Accepted

## Context
The producer (Wikipedia SSE listener) and the rule engine (consumer) must be
decoupled: the producer must never block on business-logic processing, and
the pipeline must tolerate consumer crashes/restarts without losing events.
Some buffering/log mechanism is needed between them.

## Decision
Apache Kafka (via `aiokafka`), single local broker (KRaft mode) for
development.

## Alternatives considered
- **Redis Streams**: would reuse infrastructure already needed for the
  sliding-window rule (Redis is required regardless), and is operationally
  lighter (no separate broker). At this project's volume it would have been
  technically sufficient. Rejected as a deliberate scope choice: the project
  is designed around a distributed log — key-based partitioning, consumer
  groups, rebalancing across consumers — and Redis Streams has consumer
  groups but no partitions, so key-based routing and rebalancing would not
  be part of the design.
- **In-process `asyncio.Queue`**: simplest option, but not persistent (a
  crash loses everything in the queue) and cannot be distributed across
  multiple consumer processes. Rejected — it rules out horizontal scaling
  entirely.

## Consequences
Requires running/understanding a real Kafka broker locally (Docker Compose).
In exchange, the project demonstrates partitioning, consumer groups, and
horizontal consumer scaling at the infrastructure level — the actual
mechanics of a distributed log, not just an API that happens to look like
one.
