"""Turns a raw Wikimedia recentchange payload into our own WikiEditEvent.

Structural filtering only (type/namespace) — never business logic. See
architecture-plan.md principle #1: the producer never decides what counts
as "suspicious", only what counts as "a content edit worth passing on".
"""

from wikiguard_py.domain.models import WikiEditEvent

CONTENT_NAMESPACE = 0


def normalize_recentchange(raw: dict) -> WikiEditEvent | None:
    if raw.get("type") != "edit":
        return None

    namespace = raw.get("namespace")
    if namespace != CONTENT_NAMESPACE:
        return None

    wiki = raw["wiki"]
    revision_id = raw["revision"]["new"]
    old_length = raw["length"]["old"]
    new_length = raw["length"]["new"]

    return WikiEditEvent(
        event_id=f"{wiki}:{revision_id}",
        page_title=raw["title"],
        wiki=wiki,
        user=raw.get("user", "unknown"),
        byte_change=new_length - old_length,
        is_bot=raw.get("bot", False),
        namespace=namespace,
        revision_id=revision_id,
        timestamp=raw["timestamp"],
    )
