# ADR-0007: One Window-Count alert per page per window

## Status
Accepted

## Context
`WindowCountEvaluator` returned true for every edit while a page's count stayed at or
above the threshold. One edit war of 12 edits inside the window, with a threshold of 5,
wrote 8 rows to `fired_alerts` for the same page and the same episode. The alert history
and the alert-rate chart counted edits of an edit war, not edit wars.

## Decision
The edit that crosses the threshold raises the alert; the rest of the same burst is counted
but raises nothing. After an alert, the evaluator sets a marker key
`rule:{rule_id}:{page_title}:alerted` with `SET NX` and a lifetime of one window. While the
marker exists, the page does not alert again for that rule. `SET NX` succeeds for exactly
one caller, so the rule holds even if two consumers ever see the same page.

## Alternatives considered
- **Keep one alert per edit**: simplest, and shows the length of a burst, but floods the
  history with duplicates. The length is still available: the alert records `edit_count`
  at the moment it fired, and the live count stays in Redis.
- **Deduplicate when reading** (group alerts by page and time in the API): keeps every row,
  but every reader has to repeat the grouping, and the table grows for nothing.
- **Update one alert row with the latest count**: shows the final length of the burst, but
  turns an append-only history into rows that change after they were written.

## Consequences
- An edit war that lasts longer than one window raises one alert per window, which is the
  intended signal: it is still going.
- Each Window-Count rule adds at most one extra small key per page in Redis, which expires
  by itself.
