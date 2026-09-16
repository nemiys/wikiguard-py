# ADR-0001: Separate repo for the Python port, not a branch of wiki-guard

## Status
Accepted

## Context
wiki-guard (Java/Spring Boot) already exists as a finished bootcamp portfolio
project. We want a Python implementation of the same idea (real-time Wikipedia
edit-integrity monitoring), built deliberately from first principles rather
than ported line-by-line, with Kafka as the primary learning focus.

## Decision
`wikiguard-py` is its own git repository, sibling to `wiki-guard` under the
same parent folder — not a branch or subfolder of the existing Java repo.

## Alternatives considered
- Branch inside `wiki-guard`: rejected — would mix Java and Python history in
  one commit log, and blur two distinct portfolio pieces into one.
- Subfolder inside `wiki-guard` on `main`: same problem, plus couples the two
  projects' lifecycles (deploy, docs, CI) for no benefit.

## Consequences
Two independent commit histories, each one telling its own story end-to-end.
The Java code is read only as a point reference during implementation (see
project `CLAUDE.md`), never copied wholesale — including this ADR/Notion
documentation process itself, which was designed fresh for this project.
