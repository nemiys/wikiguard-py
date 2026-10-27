"""Project-wide test fixtures."""

import pytest

from wikiguard_py.persistence.database import engine


@pytest.fixture(autouse=True)
async def _dispose_engine_after_test():
    """pytest-asyncio gives each test its own event loop, but asyncpg
    connections are bound to the loop they were opened on. Any test that
    touches Postgres (directly, or through load_evaluators/record_alert,
    which open their own sessions) can leave a connection in the engine's
    pool that the next test's loop can't reuse — disposing after every
    test, project-wide, avoids chasing this per test file."""
    yield
    await engine.dispose()
