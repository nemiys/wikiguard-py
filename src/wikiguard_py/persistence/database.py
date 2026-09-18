"""Async SQLAlchemy setup — the Postgres connection every model builds on."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://wikiguard:wikiguard@localhost:5433/wikiguard"

engine = create_async_engine(DATABASE_URL)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def create_tables() -> None:
    # Local import: a model only registers itself onto Base.metadata once its
    # module has actually been imported somewhere. Importing it here — not at
    # the top of this file, which would be circular (models.py imports Base
    # from here) — guarantees create_all sees every model, regardless of
    # what the caller happened to import first.
    from wikiguard_py.persistence import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
