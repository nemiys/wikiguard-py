# ADR-0007: One table per rule type; fired_alerts references rules loosely

## Status
Accepted

## Context
Stage 5 needed to persist two structurally different rule types
(`ThresholdEvaluator`'s single `byte_threshold`; `WindowCountEvaluator`'s
`window_seconds` + `edit_count_threshold`), plus a permanent record of
every alert that actually fires. `architecture-plan.md` left the exact
schema open, naming wiki-guard's single-table-inheritance approach as one
option to consider changing.

## Decision
Two decisions, made together:
1. Each rule type gets its own table (`threshold_rules`,
   `window_count_rules`) with exactly the columns it needs — no shared
   table with columns that are only meaningful for some rows.
2. `fired_alerts` references the rule that fired it via two plain columns,
   `rule_type` (string) and `rule_id` (int) — not a database-enforced
   foreign key, since there is no single rules table for a foreign key to
   point at.

## Alternatives considered
- **A single shared `alert_rules` table** (wiki-guard's
  single-table-inheritance approach), with nullable columns per
  rule-type-specific field: simpler to query "all active rules" in one
  statement, but every new rule type means a migration adding more
  nullable columns to a table shared by every existing rule type, and
  Postgres cannot enforce "if rule_type=threshold, byte_threshold must be
  set."
- **A shared `rules` registry table** (id, rule_type only), with each
  type-specific table's id also being a foreign key into it (class-table
  inheritance), giving `fired_alerts` a real, enforced foreign key: true
  referential integrity, but a third table and an extra join purely to
  support that integrity — disproportionate to this project's actual scale
  (a handful of rules, not a high-write multi-tenant system).

## Consequences
Adding a new rule type later means a new table and a new evaluator class
(`domain/evaluators.py`) — neither touches the two existing rule tables or
`fired_alerts` at all. `fired_alerts`' `rule_type`/`rule_id` columns are
populated entirely by application code (`consumer/main.py`,
`persistence/alerts.py`); nothing in Postgres itself catches a `rule_id`
that doesn't actually exist in its `rule_type`'s table — a deliberate
simplification acceptable at this project's scale, worth revisiting if that
ever stops being true.
