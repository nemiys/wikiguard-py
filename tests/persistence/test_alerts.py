"""Tests for record_alert — writes directly to the real database through
its own session (see persistence/alerts.py), so it can't use the
tests/api rollback fixture. Each test cleans up the row it inserted by
hand, scoped by a unique page_title marker.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text

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


async def test_fired_at_is_utc_even_when_the_database_is_not():
    """fired_at has no timezone, and every reader (the API filters, the dashboard) treats it
    as UTC. A hosted Postgres may run in another timezone: the value must not follow it."""
    page_title = "zz_fired_at_timezone"
    try:
        async with async_session_factory() as session:
            await session.execute(text("SET TIME ZONE 'Asia/Jerusalem'"))
            session.add(
                FiredAlertModel(
                    rule_type="threshold",
                    rule_id=1,
                    page_title=page_title,
                    wiki="enwiki",
                    server_name="en.wikipedia.org",
                    user="SomeUser",
                    byte_change=1,
                )
            )
            await session.commit()
        alert = await fetch_by_page_title(page_title)
        utc_now = datetime.now(UTC).replace(tzinfo=None)
        assert abs(alert.fired_at - utc_now) < timedelta(minutes=1)
    finally:
        await cleanup_by_page_title(page_title)


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
