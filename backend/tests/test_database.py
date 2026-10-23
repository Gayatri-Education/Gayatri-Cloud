"""Test schema constraints, transactions, and model integrity."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import (
    CanonicalLearningState,
    Course,
    CourseOffering,
    CourseVersion,
    Organization,
    UserAccount,
)


@pytest.fixture
async def test_session() -> AsyncSession:
    """Provides a fresh isolated in-memory database session for each test."""
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
async def test_user_account_creation_and_unique_constraint(test_session: AsyncSession):
    """Verify UserAccount creation and duplicate email rejection."""
    user1 = UserAccount(email="learner1@example.internal", full_name="Learner One")
    test_session.add(user1)
    await test_session.commit()

    assert user1.id is not None
    assert user1.is_active is True
    assert user1.is_deleted is False

    # Attempt duplicate email
    user2 = UserAccount(email="learner1@example.internal", full_name="Duplicate Learner")
    test_session.add(user2)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()


@pytest.mark.asyncio
async def test_transaction_rollback_guarantee(test_session: AsyncSession):
    """Verify that failed transactions roll back without partial data retention."""
    user = UserAccount(email="atomic@example.internal", full_name="Atomic Tester")
    test_session.add(user)
    await test_session.flush()

    # Intentionally trigger an error by attempting to insert invalid data in the same transaction
    try:
        # Invalid duplicate user
        dup_user = UserAccount(email="atomic@example.internal", full_name="Atomic Tester Dup")
        test_session.add(dup_user)
        await test_session.commit()
    except IntegrityError:
        await test_session.rollback()

    # Verify atomic user was rolled back
    from sqlalchemy import select

    res = await test_session.execute(
        select(UserAccount).where(UserAccount.email == "atomic@example.internal")
    )
    assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_soft_delete_lifecycle(test_session: AsyncSession):
    """Verify soft-delete flag behavior."""
    org = Organization(name="Test Org", slug="test-org")
    test_session.add(org)
    await test_session.commit()

    assert org.is_deleted is False
    org.is_deleted = True
    await test_session.commit()

    assert org.is_deleted is True


@pytest.mark.asyncio
async def test_canonical_learning_state_unique_constraint(test_session: AsyncSession):
    """Verify unique constraint on (student_id, offering_id, concept_id)."""
    org = Organization(name="School", slug="school")
    user = UserAccount(email="student@school.internal", full_name="Student")
    test_session.add_all([org, user])
    await test_session.flush()

    course = Course(organization_id=org.id, code="MATH101", title="Math 101")
    test_session.add(course)
    await test_session.flush()

    ver = CourseVersion(course_id=course.id, version_tag="v1.0", status="published")
    test_session.add(ver)
    await test_session.flush()

    offering = CourseOffering(course_version_id=ver.id, organization_id=org.id, term="T1")
    test_session.add(offering)
    await test_session.flush()

    state1 = CanonicalLearningState(
        student_id=user.id,
        offering_id=offering.id,
        concept_id="limits_and_continuity",
        mastery_score=0.85,
    )
    test_session.add(state1)
    await test_session.commit()

    # Attempt to add duplicate state for the same student + offering + concept
    state2 = CanonicalLearningState(
        student_id=user.id,
        offering_id=offering.id,
        concept_id="limits_and_continuity",
        mastery_score=0.90,
    )
    test_session.add(state2)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()
