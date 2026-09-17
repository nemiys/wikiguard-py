"""Shared test helpers for the domain layer tests."""

import pytest

from wikiguard_py.domain.models import WikiEditEvent


@pytest.fixture
def make_event():
    """Factory for a valid WikiEditEvent, with any field overridable."""

    def _make(**overrides) -> WikiEditEvent:
        defaults = dict(
            event_id="hewiki:123",
            page_title="עמוד ראשי",
            wiki="hewiki",
            user="some_user",
            byte_change=100,
            is_bot=False,
            namespace=0,
            revision_id=123,
            timestamp=1_700_000_000,
        )
        defaults.update(overrides)
        return WikiEditEvent(**defaults)

    return _make
