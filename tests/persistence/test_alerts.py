"""Tests for record_alert — writes directly to the real database through
its own session (see persistence/alerts.py), so it can't use the
tests/api rollback fixture. Each test cleans up the row it inserted by
hand, scoped by a unique page_title marker.
"""

from sqlalchemy import delete, select

from wikiguard_py.persistence.alerts import record_alert
from wikiguard_py.persistence.database import async_session_factory
from wikiguard_py.persistence.models import FiredAlertModel


async def fetch_by_page_title(page_title):
    async with async_session_factory() as session:
        result = await session.execute(
            select(FiredAlertModel).where(FiredAlertModel.page_title == page_title)
        )
        return result.scalars().one()


async def cleanup_by_page_title(page_title):
    async with async_session_factory() as session:
        await session.execute(
            delete(FiredAlertModel).where(FiredAlertModel.page_title == page_title)
        )
        await session.commit()


async def test_record_alert_without_edit_count():
    page_title = "zz_record_alert_no_edit_count"
    try:
        await record_alert(
            rule_type="threshold",
            rule_id=1,
            page_title=page_title,
            wiki="enwiki",
            server_name="en.wikipedia.org",
            user="SomeUser",
            byte_change=9000,
        )
        alert = await fetch_by_page_title(page_title)
        assert alert.byte_change == 9000
        assert alert.edit_count is None
    finally:
        await cleanup_by_page_title(page_title)


async def test_record_alert_with_edit_count():
    page_title = "zz_record_alert_with_edit_count"
    try:
        await record_alert(
            rule_type="window_count",
            rule_id=2,
            page_title=page_title,
            wiki="enwiki",
            server_name="en.wikipedia.org",
            user="SomeUser",
            byte_change=100,
            edit_count=7,
        )
        alert = await fetch_by_page_title(page_title)
        assert alert.edit_count == 7
    finally:
        await cleanup_by_page_title(page_title)
