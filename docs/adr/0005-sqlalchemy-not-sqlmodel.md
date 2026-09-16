# ADR-0005: SQLAlchemy 2.0 async + separate Pydantic schemas, not SQLModel

## Status
Accepted

## Context
Rules and fired alerts need a persistence layer (Postgres) and an API
contract (FastAPI request/response bodies). These two representations of the
"same" data are not required to be identical — a DB row can carry internal
fields (e.g. timestamps, flags) that should never be exposed through the API
as-is.

## Decision
Two separate class definitions per entity: a SQLAlchemy 2.0 async ORM model
(the DB table) and Pydantic schemas (the API contract), with explicit
conversion between them.

## Alternatives considered
- **SQLModel**: a single class serves as both the ORM model and the Pydantic
  schema. Less code, but couples the DB shape to the API shape by
  construction — harder to keep an internal-only DB field out of the API
  response without extra work. Also a smaller ecosystem/less commonly asked
  about in interviews than plain SQLAlchemy.

## Consequences
More boilerplate (two class definitions + a conversion step) in exchange for
a clean, independently-evolvable boundary between "what's stored" and "what's
exposed" — and fluency in the ORM most commonly expected in Python backend
interviews.
