"""Test synthetic seed fixtures."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.fixtures import seed_synthetic_tenants


@pytest.fixture
async def test_session() -> AsyncSession:
    """Provides a fresh isolated in-memory database session."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_seed_synthetic_tenants_creates_expected_entities(test_session: AsyncSession):
    """Verify that seed_synthetic_tenants creates entities cleanly without errors."""
    data = await seed_synthetic_tenants(test_session)

    assert "org_alpha" in data
    assert "org_beta" in data
    assert "student_alpha" in data
    assert "teacher_alpha" in data
    assert "course_alpha" in data

    assert data["org_alpha"].name == "Alpha Academy"
    assert data["org_beta"].name == "Beta High School"
    assert data["student_alpha"].email == "student.alpha@example.internal"
