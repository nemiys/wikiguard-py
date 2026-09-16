# ADR-0002: Kafka as the ingestion→processing decoupling layer

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
  lighter (no separate broker). Rejected only because the explicit, stated
  purpose of this project is to learn and demonstrate Kafka as a high-scale
  message queue — this is a deliberate scope choice, not a technical
  necessity.
- **In-process `asyncio.Queue`**: simplest option, but not persistent (a
  crash loses everything in the queue) and cannot be distributed across
  multiple consumer processes. Rejected — defeats the "high scale" learning
  goal entirely.

## Consequences
Requires running/understanding a real Kafka broker locally (Docker Compose).
In exchange, the project can genuinely demonstrate partitioning, consumer
groups, and horizontal consumer scaling — the core interview-relevant skill
this project exists to build.
