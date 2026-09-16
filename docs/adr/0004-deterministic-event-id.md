# ADR-0004: event_id = "{wiki}:{revision_id}", not a random UUID

## Status
Accepted

## Context
Each event needs a unique identifier, independent of its Kafka partition key
(see ADR-0003). Wikimedia's EventStreams feed is global — it interleaves
every Wikimedia project (enwiki, hewiki, wikidata, commons, ...) on one
connection. MediaWiki's own `revision_id` is only unique *within* a single
wiki, not across the whole feed.

## Decision
`event_id = f"{wiki}:{revision_id}"` — deterministic, built from fields
already present on the source event.

## Alternatives considered
- **Random UUID per event** (generated fresh at publish time): always unique,
  simple. Rejected because it is not idempotent — if the producer retries a
  publish after a crash/timeout before receiving a Kafka ack, the same real
  edit gets a *different* UUID each time, making downstream deduplication
  impossible.
- **`revision_id` alone**: rejected — not globally unique. `enwiki` and
  `hewiki` can both mint the same numeric revision id independently, so two
  unrelated edits from different wikis could collide.

## Consequences
The same underlying edit always produces the same `event_id`, even across
retries — enabling deduplication downstream if/when it's needed. No
collision risk across wikis, since `wiki` disambiguates the otherwise
per-wiki-scoped `revision_id`.
