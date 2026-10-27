"""Shared fixtures for API tests — every test runs inside a transaction
that's rolled back afterward, so CRUD tests never leave rows behind in
the real dev database."""

from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from wikiguard_py.main import app
from wikiguard_py.persistence.database import engine, get_session
from wikiguard_py.persistence.models import FiredAlertModel


@pytest.fixture
async def session():
    async with engine.connect() as connection:
        await connection.begin()
        async_session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        yield async_session
        await async_session.close()
        await connection.rollback()


@pytest.fixture
async def client(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def make_alert(session):
    """fired_alerts has no POST endpoint (read-only API) — tests that need
    alert rows insert them directly through this same rollback-bound
    session, not through persistence.alerts.record_alert (which opens its
    own session against the real database and would not be rolled back)."""

    async def _make_alert(**overrides):
        defaults = {
            "rule_type": "threshold",
            "rule_id": 1,
            "page_title": "Test Page",
            "wiki": "enwiki",
            "server_name": "en.wikipedia.org",
            "user": "TestUser",
            "byte_change": 100,
            "edit_count": None,
            "fired_at": datetime.now(UTC).replace(tzinfo=None),
        }
        defaults.update(overrides)
        alert = FiredAlertModel(**defaults)
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        return alert

    return _make_alert
