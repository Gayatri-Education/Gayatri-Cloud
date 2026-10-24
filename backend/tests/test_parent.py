"""Tests for Phase P14: Parent and Guardian domain, privacy controls, and APIs."""

from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rbac import RoleEnum, TenantContext
from app.db.base import Base
from app.db.models.course import Course, CourseEnrollment, CourseOffering, CourseVersion
from app.db.models.identity import UserAccount
from app.db.models.organization import (
    GuardianRelationship,
    Membership,
    Organization,
    RoleAssignment,
)
from app.db.models.teacher import ClassAnnouncement
from app.db.models.tutoring import (
    Assessment,
    AssessmentAttempt,
    CanonicalLearningState,
    ConversationTurn,
    TutorSession,
)
from app.domain.parent.service import ParentService


@pytest.fixture
async def db_session():
    """Provides isolated in-memory test database session."""
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


@pytest.fixture
async def parent_fixture(db_session: AsyncSession):
    """Fixture providing organization, parent, linked children, unlinked student, and courses."""
    ts = datetime.now().timestamp()
    org = Organization(
        name="Springfield Elementary",
        slug=f"springfield-elem-{int(ts)}",
        status="active",
    )
    db_session.add(org)
    await db_session.flush()

    # Users: Parent (Marge), Child 1 (Bart), Child 2 (Lisa), Unlinked Student (Nelson)
    parent = UserAccount(
        email=f"marge.simpson.{ts}@springfield.edu",
        full_name="Marge Simpson",
        is_active=True,
    )
    child1 = UserAccount(
        email=f"bart.simpson.{ts}@springfield.edu",
        full_name="Bart Simpson",
        is_active=True,
    )
    child2 = UserAccount(
        email=f"lisa.simpson.{ts}@springfield.edu",
        full_name="Lisa Simpson",
        is_active=True,
    )
    unlinked_student = UserAccount(
        email=f"nelson.muntz.{ts}@springfield.edu",
        full_name="Nelson Muntz",
        is_active=True,
    )
    teacher = UserAccount(
        email=f"edna.krabappel.{ts}@springfield.edu",
        full_name="Edna Krabappel",
        is_active=True,
    )
    db_session.add_all([parent, child1, child2, unlinked_student, teacher])
    await db_session.flush()

    # Memberships & Role assignments
    m_parent = Membership(user_id=parent.id, organization_id=org.id, status="active")
    m_c1 = Membership(user_id=child1.id, organization_id=org.id, status="active")
    m_c2 = Membership(user_id=child2.id, organization_id=org.id, status="active")
    m_unlinked = Membership(user_id=unlinked_student.id, organization_id=org.id, status="active")
    m_teacher = Membership(user_id=teacher.id, organization_id=org.id, status="active")
    db_session.add_all([m_parent, m_c1, m_c2, m_unlinked, m_teacher])
    await db_session.flush()

    db_session.add_all(
        [
            RoleAssignment(membership_id=m_parent.id, role=RoleEnum.PARENT.value),
            RoleAssignment(membership_id=m_c1.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_c2.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_unlinked.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_teacher.id, role=RoleEnum.TEACHER.value),
        ]
    )
    await db_session.flush()

    # Course & Offering
    course = Course(
        code=f"SCI-101-{int(ts)}",
        title="Introductory Science",
        organization_id=org.id,
    )
    db_session.add(course)
    await db_session.flush()

    version = CourseVersion(
        course_id=course.id,
        version_tag="v1.0.0",
        status="published",
    )
    db_session.add(version)
    await db_session.flush()

    offering = CourseOffering(
        course_version_id=version.id,
        organization_id=org.id,
        term="Fall 2026",
        status="active",
    )
    db_session.add(offering)
    await db_session.flush()

    # Enroll child1 and child2
    e1 = CourseEnrollment(student_id=child1.id, offering_id=offering.id, status="enrolled")
    e2 = CourseEnrollment(student_id=child2.id, offering_id=offering.id, status="enrolled")
    db_session.add_all([e1, e2])

    # Verified relationship for child1; child2 initially unverified
    rel1 = GuardianRelationship(
        guardian_id=parent.id,
        student_id=child1.id,
        verification_status="verified",
        is_active=True,
    )
    db_session.add(rel1)
    await db_session.commit()

    parent_context = TenantContext(
        user=parent,
        organization_id=org.id,
        roles=[RoleEnum.PARENT.value],
    )

    return {
        "org": org,
        "parent": parent,
        "child1": child1,
        "child2": child2,
        "unlinked_student": unlinked_student,
        "teacher": teacher,
        "course": course,
        "offering": offering,
        "rel1": rel1,
        "context": parent_context,
    }


@pytest.mark.asyncio
async def test_guardian_link_request_and_verification(db_session: AsyncSession, parent_fixture):
    """Test parent requesting a link to child2, listing children, and verification approval."""
    context = parent_fixture["context"]
    child2 = parent_fixture["child2"]

    service = ParentService(db_session)

    # 1. Request link to child2
    req = await service.request_link(context, child2.email)
    assert req.verification_status == "pending"
    assert req.is_active is True

    # 2. List linked children shows child1 (verified) and child2 (pending)
    children = await service.list_linked_children(context)
    assert len(children) == 2
    c_names = [c["student_name"] for c in children]
    assert "Bart Simpson" in c_names
    assert "Lisa Simpson" in c_names

    # 3. Verify link
    verified = await service.verify_link(context, req.id)
    assert verified.verification_status == "verified"


@pytest.mark.asyncio
async def test_unlinked_student_access_rejected(db_session: AsyncSession, parent_fixture):
    """Parent cannot view learning records of student without verified link."""
    context = parent_fixture["context"]
    unlinked = parent_fixture["unlinked_student"]

    service = ParentService(db_session)

    with pytest.raises(HTTPException) as exc:
        await service.get_child_progress(context, unlinked.id)
    assert exc.value.status_code == 403
    assert "No verified guardian relationship" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        await service.get_child_assessments(context, unlinked.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_revocation_denies_access_immediately(db_session: AsyncSession, parent_fixture):
    """Revoking guardian relationship immediately denies all child record access."""
    context = parent_fixture["context"]
    child1 = parent_fixture["child1"]
    rel1 = parent_fixture["rel1"]

    service = ParentService(db_session)

    # Initially accessible
    progress = await service.get_child_progress(context, child1.id)
    assert progress["student_id"] == child1.id

    # Revoke relationship
    await service.revoke_link(context, rel1.id)

    # Subsequent access immediately denied with 403 Forbidden
    with pytest.raises(HTTPException) as exc:
        await service.get_child_progress(context, child1.id)
    assert exc.value.status_code == 403
    assert "No verified guardian relationship" in exc.value.detail


@pytest.mark.asyncio
async def test_privacy_filtered_learning_progress(db_session: AsyncSession, parent_fixture):
    """Verify that raw tutoring conversation turns are NEVER returned to parent views."""
    context = parent_fixture["context"]
    child1 = parent_fixture["child1"]
    offering = parent_fixture["offering"]

    service = ParentService(db_session)

    # Seed learning state
    db_session.add(
        CanonicalLearningState(
            student_id=child1.id,
            offering_id=offering.id,
            concept_id="photosynthesis",
            mastery_score=0.82,
            stability=10,
        )
    )

    # Seed a tutoring session with raw conversation turns
    session = TutorSession(
        student_id=child1.id,
        offering_id=offering.id,
        status="completed",
    )
    db_session.add(session)
    await db_session.flush()

    raw_turn = ConversationTurn(
        session_id=session.id,
        turn_number=1,
        role="user",
        message_text="I secretly hate doing biology homework because the teacher is annoying.",
    )
    db_session.add(raw_turn)
    await db_session.commit()

    # Query parent progress
    progress = await service.get_child_progress(context, child1.id)

    # Competency score is present
    assert progress["overall_mastery"] == 0.82
    assert progress["top_concepts"][0]["concept_id"] == "photosynthesis"
    assert progress["total_tutoring_sessions"] == 1

    # Raw dialogue is strictly absent from parent response payload
    progress_str = str(progress)
    assert "secretly hate" not in progress_str
    assert "annoying" not in progress_str
    assert "raw_turns" not in progress
    assert "conversation" not in progress
    assert "privacy_disclosure" in progress


@pytest.mark.asyncio
async def test_multi_child_switching(db_session: AsyncSession, parent_fixture):
    """Parent with multiple linked children can query each without data crossover."""
    context = parent_fixture["context"]
    child1 = parent_fixture["child1"]
    child2 = parent_fixture["child2"]
    offering = parent_fixture["offering"]

    service = ParentService(db_session)

    # Link & verify child2 as well
    rel2 = GuardianRelationship(
        guardian_id=context.user.id,
        student_id=child2.id,
        verification_status="verified",
        is_active=True,
    )
    db_session.add(rel2)

    # Bart: 0.50 on photosynthesis
    db_session.add(
        CanonicalLearningState(
            student_id=child1.id,
            offering_id=offering.id,
            concept_id="photosynthesis",
            mastery_score=0.50,
            stability=4,
        )
    )
    # Lisa: 0.98 on genetics
    db_session.add(
        CanonicalLearningState(
            student_id=child2.id,
            offering_id=offering.id,
            concept_id="genetics",
            mastery_score=0.98,
            stability=25,
        )
    )
    await db_session.commit()

    p_bart = await service.get_child_progress(context, child1.id)
    p_lisa = await service.get_child_progress(context, child2.id)

    assert p_bart["overall_mastery"] == 0.50
    assert p_bart["top_concepts"][0]["concept_id"] == "photosynthesis"

    assert p_lisa["overall_mastery"] == 0.98
    assert p_lisa["top_concepts"][0]["concept_id"] == "genetics"


@pytest.mark.asyncio
async def test_child_assessments_and_communications(db_session: AsyncSession, parent_fixture):
    """Test retrieving completed assessments and class announcements for linked child."""
    context = parent_fixture["context"]
    child1 = parent_fixture["child1"]
    offering = parent_fixture["offering"]
    teacher = parent_fixture["teacher"]
    org = parent_fixture["org"]

    service = ParentService(db_session)

    # Create assessment and attempt
    asm = Assessment(
        offering_id=offering.id,
        title="Cell Biology Quiz",
        assessment_type="MCQ",
        total_points=50,
    )
    db_session.add(asm)
    await db_session.flush()

    attempt = AssessmentAttempt(
        assessment_id=asm.id,
        student_id=child1.id,
        total_score=45.0,
        status="graded",
        submitted_at=datetime.now(),
    )
    db_session.add(attempt)

    # Create announcement
    ann = ClassAnnouncement(
        organization_id=org.id,
        offering_id=offering.id,
        teacher_id=teacher.id,
        title="Field Trip to Science Center",
        content="Permission slips due by Friday.",
    )
    db_session.add(ann)
    await db_session.commit()

    # 1. Assessments
    reports = await service.get_child_assessments(context, child1.id)
    assert len(reports) == 1
    assert reports[0]["title"] == "Cell Biology Quiz"
    assert reports[0]["score"] == 45.0
    assert reports[0]["percentage"] == 90.0

    # 2. Communications
    comms = await service.get_child_communications(context, child1.id)
    assert len(comms) == 1
    assert comms[0]["title"] == "Field Trip to Science Center"
    assert comms[0]["teacher_name"] == "Edna Krabappel"


@pytest.mark.asyncio
async def test_self_linking_prohibited(db_session: AsyncSession, parent_fixture):
    """Guardian cannot link to their own account as a student."""
    context = parent_fixture["context"]
    parent = parent_fixture["parent"]

    service = ParentService(db_session)

    with pytest.raises(HTTPException) as exc:
        await service.request_link(context, parent.id)
    assert exc.value.status_code == 400
    assert "cannot link to their own account" in exc.value.detail
