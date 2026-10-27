"""Project-wide test fixtures."""

import pytest

from wikiguard_py.persistence.database import create_tables, engine

_tables_ready = False


@pytest.fixture(autouse=True)
async def _ensure_tables_exist():
    """In local dev, create_tables() has already run via the live app's
    own startup. In CI, the Postgres service container starts with no
    schema at all — nothing else in the test suite creates it. create_all
    only adds missing tables, so this is a safe no-op against the dev DB.
    A plain module-level flag (not a session-scoped fixture, which would
    hit a pytest-asyncio event-loop scope mismatch with function-scoped
    tests) keeps this to a single real check per test run."""
    global _tables_ready
    if not _tables_ready:
        await create_tables()
        _tables_ready = True
    yield


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
