"""Core domain data — the normalized shape of a single Wikipedia edit.

This model is produced by the Producer (Stage 2) and consumed by the
Consumer/Rule Engine (Stage 3+). It carries no business logic itself —
just the facts about one edit.
"""

from pydantic import BaseModel


class WikiEditEvent(BaseModel):
    event_id: str
    page_title: str
    wiki: str
    server_name: str
    user: str
    byte_change: int
    is_bot: bool
    namespace: int
    revision_id: int
    timestamp: int
