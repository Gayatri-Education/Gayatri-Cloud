"""Async Database Engine, Session Factory, and Dependency Injection."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger("gayatri.cloud.db")


def create_engine_for_url(db_url: str | None = None) -> AsyncEngine:
    """Create an asynchronous SQLAlchemy engine with dialect-appropriate pooling."""
    url = db_url or settings.DATABASE_URL

    if url.startswith("sqlite"):
        # SQLite in-memory or file configuration for deterministic local tests
        return create_async_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool if ":memory:" in url else NullPool,
            echo=settings.DEBUG,
        )

    # PostgreSQL configuration (RDS / asyncpg)
    return create_async_engine(
        url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )


# Global engine and session factory
engine = create_engine_for_url()
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an isolated async database session.

    Guarantees rollback on unhandled exceptions and proper cleanup.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_models(target_engine: AsyncEngine | None = None) -> None:
    """Initialize all schema tables in target database (primarily for test environments)."""
    eng = target_engine or engine
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
