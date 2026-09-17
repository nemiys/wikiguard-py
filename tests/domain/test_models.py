import pytest
from pydantic import ValidationError

from wikiguard_py.domain.models import WikiEditEvent


def test_valid_event_is_constructed(make_event):
    event = make_event(byte_change=500)
    assert event.byte_change == 500


def test_wrong_type_is_rejected():
    with pytest.raises(ValidationError):
        WikiEditEvent(
            event_id="hewiki:123",
            page_title="עמוד ראשי",
            wiki="hewiki",
            user="some_user",
            byte_change="not a number",
            is_bot=False,
            namespace=0,
            revision_id=123,
            timestamp=1_700_000_000,
        )
