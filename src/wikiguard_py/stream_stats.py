"""Redis key layout for live stream statistics.

Shared between the writer (consumer, on every processed event — see
consumer/stats.py) and the reader (API GET /stats — see api/stats.py), so
both sides agree on key names without duplicating the strings. Transient
display data only — never the durable record of anything (see
architecture-plan.md principle 7).
"""

TOTAL_EVENTS_KEY = "stats:total_events"
BOT_EVENTS_KEY = "stats:bot_events"
HUMAN_EVENTS_KEY = "stats:human_events"
WIKI_COUNTS_KEY = "stats:wiki_counts"
PAGE_COUNTS_KEY = "stats:page_counts"
LAST_EVENT_AT_KEY = "stats:last_event_at"
THROUGHPUT_KEY = "stats:throughput"
EDITOR_COUNTS_KEY = "stats:editor_counts"
BIGGEST_EDIT_KEY = "stats:biggest_edit"
TREND_BUCKET_PREFIX = "stats:trend:minute"

THROUGHPUT_WINDOW_SECONDS = 60
TREND_WINDOW_MINUTES = 30
PAGE_COUNT_DELIMITER = "|"
