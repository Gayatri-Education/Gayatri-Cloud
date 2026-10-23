"""Test tenant isolation and query boundaries in repository pattern."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Course, Organization
from app.db.repositories.base import BaseTenantRepository


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
async def test_tenant_isolation_prevents_cross_tenant_access(test_session: AsyncSession):
    """Verify that a repository scoped to Tenant A cannot view or manipulate Tenant B entities."""
    # 1. Create two distinct tenants
    org_a = Organization(name="Tenant Alpha", slug="tenant-alpha")
    org_b = Organization(name="Tenant Beta", slug="tenant-beta")
    test_session.add_all([org_a, org_b])
    await test_session.flush()

    repo_a = BaseTenantRepository(Course, test_session, organization_id=org_a.id)
    repo_b = BaseTenantRepository(Course, test_session, organization_id=org_b.id)

    # 2. Create courses for each tenant
    course_a = await repo_a.create(code="BIO-101", title="Biology Alpha")
    course_b = await repo_b.create(code="CHEM-101", title="Chemistry Beta")
    await test_session.commit()

    # 3. Verify Tenant A cannot retrieve Tenant B's course
    fetched_from_a = await repo_a.get_by_id(course_b.id)
    assert fetched_from_a is None, "Tenant A repository must not retrieve Tenant B record"

    # 4. Verify Tenant B cannot retrieve Tenant A's course
    fetched_from_b = await repo_b.get_by_id(course_a.id)
    assert fetched_from_b is None, "Tenant B repository must not retrieve Tenant A record"

    # 5. Verify list_all only returns records belonging to the scoped tenant
    courses_a = await repo_a.list_all()
    assert len(courses_a) == 1
    assert courses_a[0].id == course_a.id
    assert courses_a[0].title == "Biology Alpha"

    courses_b = await repo_b.list_all()
    assert len(courses_b) == 1
    assert courses_b[0].id == course_b.id
    assert courses_b[0].title == "Chemistry Beta"


@pytest.mark.asyncio
async def test_tenant_repository_requires_organization_id(test_session: AsyncSession):
    """Verify ValueError is raised if organization_id is missing or empty."""
    with pytest.raises(ValueError, match="organization_id must be provided"):
        BaseTenantRepository(Course, test_session, organization_id="")


@pytest.mark.asyncio
async def test_tenant_scoped_soft_delete(test_session: AsyncSession):
    """Verify soft_delete operates exclusively within tenant boundaries."""
    org_a = Organization(name="Tenant Alpha", slug="tenant-alpha-sd")
    org_b = Organization(name="Tenant Beta", slug="tenant-beta-sd")
    test_session.add_all([org_a, org_b])
    await test_session.flush()

    repo_a = BaseTenantRepository(Course, test_session, organization_id=org_a.id)
    repo_b = BaseTenantRepository(Course, test_session, organization_id=org_b.id)

    course_b = await repo_b.create(code="HIST-101", title="History Beta")
    await test_session.commit()

    # Tenant A attempts to soft delete Tenant B's course
    success = await repo_a.soft_delete(course_b.id)
    assert success is False, "Tenant A must not be able to soft delete Tenant B record"

    # Course B must still be intact and visible to Tenant B
    still_exists = await repo_b.get_by_id(course_b.id)
    assert still_exists is not None
    assert still_exists.is_deleted is False

    # Tenant B legitimately soft deletes its own course
    success_b = await repo_b.soft_delete(course_b.id)
    assert success_b is True

    # Now it is no longer returned in active list
    assert await repo_b.get_by_id(course_b.id) is None
