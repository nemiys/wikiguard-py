import pytest


@pytest.fixture
def make_raw_change():
    """Factory for a valid raw Wikimedia recentchange payload, any field overridable."""

    def _make(**overrides) -> dict:
        defaults = {
            "type": "edit",
            "namespace": 0,
            "title": "עמוד ראשי",
            "wiki": "hewiki",
            "user": "some_user",
            "bot": False,
            "revision": {"old": 100, "new": 123},
            "length": {"old": 500, "new": 600},
            "timestamp": 1_700_000_000,
        }
        defaults.update(overrides)
        return defaults

    return _make
