"""Tests for Phase P13: Teacher and Academic Administration domain and APIs."""

from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rbac import RoleEnum, TenantContext
from app.db.base import Base
from app.db.models.course import Course, CourseOffering, CourseVersion
from app.db.models.identity import UserAccount
from app.db.models.organization import Membership, Organization, RoleAssignment
from app.db.models.teacher import TeacherIntervention
from app.db.models.tutoring import CanonicalLearningState, MisconceptionRecord
from app.domain.teacher.service import TeacherService


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
async def teacher_fixture(db_session: AsyncSession):
    """Fixture providing organizations, teacher, students, courses, and offerings."""
    # Org A
    org_a = Organization(
        name="Springfield Academy",
        slug=f"springfield-{datetime.now().timestamp()}",
        status="active",
    )
    # Org B (for cross-tenant tests)
    org_b = Organization(
        name="Shelbyville High",
        slug=f"shelbyville-{datetime.now().timestamp()}",
        status="active",
    )
    db_session.add_all([org_a, org_b])
    await db_session.flush()

    # Users: Teacher, Student 1, Student 2
    ts = datetime.now().timestamp()
    teacher = UserAccount(
        email=f"edna.krabappel.{ts}@springfield.edu",
        full_name="Edna Krabappel",
        is_active=True,
    )
    student1 = UserAccount(
        email=f"bart.simpson.{ts}@springfield.edu",
        full_name="Bart Simpson",
        is_active=True,
    )
    student2 = UserAccount(
        email=f"milhouse.vanhouten.{ts}@springfield.edu",
        full_name="Milhouse VanHouten",
        is_active=True,
    )
    db_session.add_all([teacher, student1, student2])
    await db_session.flush()

    # Memberships
    m_teacher = Membership(
        user_id=teacher.id,
        organization_id=org_a.id,
        status="active",
    )
    m_s1 = Membership(
        user_id=student1.id,
        organization_id=org_a.id,
        status="active",
    )
    m_s2 = Membership(
        user_id=student2.id,
        organization_id=org_a.id,
        status="active",
    )
    db_session.add_all([m_teacher, m_s1, m_s2])
    await db_session.flush()

    r_teacher = RoleAssignment(membership_id=m_teacher.id, role=RoleEnum.TEACHER.value)
    r_s1 = RoleAssignment(membership_id=m_s1.id, role=RoleEnum.STUDENT.value)
    r_s2 = RoleAssignment(membership_id=m_s2.id, role=RoleEnum.STUDENT.value)
    db_session.add_all([r_teacher, r_s1, r_s2])
    await db_session.flush()

    # Course in Org A
    course_a = Course(
        code=f"PHYS-401-{int(ts)}",
        title="Advanced Thermodynamics",
        organization_id=org_a.id,
    )
    db_session.add(course_a)
    await db_session.flush()

    version_a = CourseVersion(
        course_id=course_a.id,
        version_tag="v1.0.0",
        status="published",
    )
    db_session.add(version_a)
    await db_session.flush()

    offering_a = CourseOffering(
        course_version_id=version_a.id,
        organization_id=org_a.id,
        term="Fall 2026",
        status="active",
    )
    # Offering in Org B
    course_b = Course(
        code=f"CHEM-101-{int(ts)}",
        title="Organic Chemistry",
        organization_id=org_b.id,
    )
    db_session.add(course_b)
    await db_session.flush()

    version_b = CourseVersion(
        course_id=course_b.id,
        version_tag="v1.0.0",
        status="published",
    )
    db_session.add(version_b)
    await db_session.flush()

    offering_b = CourseOffering(
        course_version_id=version_b.id,
        organization_id=org_b.id,
        term="Fall 2026",
        status="active",
    )
    db_session.add_all([offering_a, offering_b])
    await db_session.commit()

    teacher_context = TenantContext(
        user=teacher,
        organization_id=org_a.id,
        roles=[RoleEnum.TEACHER.value],
    )

    return {
        "org_a": org_a,
        "org_b": org_b,
        "teacher": teacher,
        "student1": student1,
        "student2": student2,
        "course_a": course_a,
        "offering_a": offering_a,
        "offering_b": offering_b,
        "context": teacher_context,
    }


@pytest.mark.asyncio
async def test_class_roster_and_enrollment_lifecycle(db_session: AsyncSession, teacher_fixture):
    """Test enrolling students into class offering, retrieving roster, and unenrollment."""
    context = teacher_fixture["context"]
    offering = teacher_fixture["offering_a"]
    s1 = teacher_fixture["student1"]
    s2 = teacher_fixture["student2"]

    service = TeacherService(db_session)

    # 1. Enroll both students
    e1 = await service.enroll_student(context, offering.id, s1.id)
    e2 = await service.enroll_student(context, offering.id, s2.id)
    assert e1.status == "enrolled"
    assert e2.status == "enrolled"

    # Idempotent re-enrollment returns existing
    e1_again = await service.enroll_student(context, offering.id, s1.id)
    assert e1_again.id == e1.id

    # 2. Add some learning state for s1
    st = CanonicalLearningState(
        student_id=s1.id,
        offering_id=offering.id,
        concept_id="con_heat",
        mastery_score=0.85,
        stability=14,
    )
    db_session.add(st)
    await db_session.commit()

    # 3. Get roster
    roster = await service.get_roster(context, offering.id)
    assert len(roster) == 2
    student_names = [r["student_name"] for r in roster]
    assert "Bart Simpson" in student_names
    assert "Milhouse VanHouten" in student_names

    bart_entry = next(r for r in roster if r["student_name"] == "Bart Simpson")
    assert bart_entry["average_mastery"] == 0.85

    # 4. Unenroll Milhouse
    await service.unenroll_student(context, offering.id, s2.id)
    roster_after = await service.get_roster(context, offering.id)
    assert len(roster_after) == 1
    assert roster_after[0]["student_name"] == "Bart Simpson"


@pytest.mark.asyncio
async def test_cross_tenant_isolation_on_roster(db_session: AsyncSession, teacher_fixture):
    """Teacher from Org A cannot access offering from Org B."""
    context = teacher_fixture["context"]
    offering_b = teacher_fixture["offering_b"]

    service = TeacherService(db_session)

    with pytest.raises(HTTPException) as exc:
        await service.get_roster(context, offering_b.id)
    assert exc.value.status_code == 403
    assert "tenant boundaries" in exc.value.detail


@pytest.mark.asyncio
async def test_class_analytics_aggregation(db_session: AsyncSession, teacher_fixture):
    """Test mastery distribution calculation, hardest concepts, and misconception clusters."""
    context = teacher_fixture["context"]
    offering = teacher_fixture["offering_a"]
    s1 = teacher_fixture["student1"]
    s2 = teacher_fixture["student2"]

    service = TeacherService(db_session)
    await service.enroll_student(context, offering.id, s1.id)
    await service.enroll_student(context, offering.id, s2.id)

    # Seed learning states:
    # Bart: 0.90 on heat, 0.40 on entropy -> mean 0.65 (competent)
    # Milhouse: 0.30 on heat, 0.20 on entropy -> mean 0.25 (novice)
    db_session.add_all(
        [
            CanonicalLearningState(
                student_id=s1.id,
                offering_id=offering.id,
                concept_id="entropy",
                mastery_score=0.40,
                stability=5,
            ),
            CanonicalLearningState(
                student_id=s1.id,
                offering_id=offering.id,
                concept_id="heat",
                mastery_score=0.90,
                stability=20,
            ),
            CanonicalLearningState(
                student_id=s2.id,
                offering_id=offering.id,
                concept_id="entropy",
                mastery_score=0.20,
                stability=3,
            ),
            CanonicalLearningState(
                student_id=s2.id,
                offering_id=offering.id,
                concept_id="heat",
                mastery_score=0.30,
                stability=4,
            ),
            # Both have misconception on entropy
            MisconceptionRecord(
                student_id=s1.id,
                offering_id=offering.id,
                concept_id="entropy",
                description="Total entropy never changes",
                status="active",
                detected_at=datetime.now(),
            ),
            MisconceptionRecord(
                student_id=s2.id,
                offering_id=offering.id,
                concept_id="entropy",
                description="Total entropy never changes",
                status="active",
                detected_at=datetime.now(),
            ),
        ]
    )
    await db_session.commit()

    analytics = await service.get_class_analytics(context, offering.id)

    assert analytics["total_students"] == 2
    assert analytics["mastery_distribution"]["competent"] == 1
    assert analytics["mastery_distribution"]["novice"] == 1

    # Hardest concept should be 'entropy' (mean 0.30 vs heat 0.60)
    assert analytics["hardest_concepts"][0]["concept_id"] == "entropy"
    assert analytics["hardest_concepts"][0]["average_score"] == 0.30

    # Misconception cluster should show 2 students with 'Total entropy never changes'
    assert len(analytics["misconception_clusters"]) == 1
    assert analytics["misconception_clusters"][0]["description"] == "Total entropy never changes"
    assert analytics["misconception_clusters"][0]["student_count"] == 2


@pytest.mark.asyncio
async def test_intervention_queue_and_acknowledgement(db_session: AsyncSession, teacher_fixture):
    """Test flagging struggling student and teacher acknowledgement."""
    context = teacher_fixture["context"]
    offering = teacher_fixture["offering_a"]
    s2 = teacher_fixture["student2"]

    service = TeacherService(db_session)
    await service.enroll_student(context, offering.id, s2.id)

    # Create intervention
    interv = TeacherIntervention(
        organization_id=context.organization_id,
        offering_id=offering.id,
        student_id=s2.id,
        concept_id="entropy",
        severity="HIGH",
        reason="Persistent misconception MISCON_ENTROPY_CONSERVED after 3 attempts.",
        status="PENDING",
    )
    db_session.add(interv)
    await db_session.commit()

    queue = await service.get_intervention_queue(context, offering.id)
    assert len(queue) == 1
    assert queue[0]["student_name"] == "Milhouse VanHouten"
    assert queue[0]["severity"] == "HIGH"

    # Teacher acknowledges
    ack = await service.acknowledge_intervention(
        context,
        interv.id,
        resolution_notes="Scheduled 1-on-1 Socratic review session.",
        resolve=True,
    )
    assert ack.status == "RESOLVED"
    assert ack.acknowledged_by == context.user.id
    assert ack.resolution_notes == "Scheduled 1-on-1 Socratic review session."


@pytest.mark.asyncio
async def test_copilot_diagnostic_briefing(db_session: AsyncSession, teacher_fixture):
    """Test evidence-grounded copilot briefing with uncertainty and confirmation requirement."""
    context = teacher_fixture["context"]
    offering = teacher_fixture["offering_a"]
    s1 = teacher_fixture["student1"]

    service = TeacherService(db_session)
    await service.enroll_student(context, offering.id, s1.id)

    db_session.add(
        CanonicalLearningState(
            student_id=s1.id,
            offering_id=offering.id,
            concept_id="carnot_cycle",
            mastery_score=0.35,
            stability=3,
        )
    )
    await db_session.commit()

    briefing = await service.generate_copilot_briefing(context, offering.id)

    assert "carnot_cycle" in briefing["summary"]
    assert briefing["requires_teacher_confirmation"] is True
    assert len(briefing["evidence_sources"]) >= 2
    assert len(briefing["suggested_actions"]) >= 1
    assert "uncertainty_note" in briefing


@pytest.mark.asyncio
async def test_teacher_instruction_cascade_management(db_session: AsyncSession, teacher_fixture):
    """Test creating, listing, and deactivating directives in the 5-tier cascade."""
    context = teacher_fixture["context"]
    course = teacher_fixture["course_a"]

    service = TeacherService(db_session)

    # 1. Create two directives with priorities 2 and 5
    i1 = await service.create_instruction(
        context,
        course_id=course.id,
        tier="COURSE",
        directive_text="Default to explain-first before posing Socratic questions.",
        priority=2,
    )
    i2 = await service.create_instruction(
        context,
        course_id=course.id,
        tier="COURSE",
        directive_text="Urgent exam review: only practice problems.",
        priority=5,
    )

    # 2. List instructions — highest priority must be first
    instructions = await service.list_instructions(context, course.id)
    assert len(instructions) == 2
    assert instructions[0].priority == 5
    assert instructions[1].priority == 2

    # 3. Deactivate i2
    await service.deactivate_instruction(context, i2.id)
    active_after = await service.list_instructions(context, course.id)
    assert len(active_after) == 1
    assert active_after[0].id == i1.id


@pytest.mark.asyncio
async def test_class_announcements(db_session: AsyncSession, teacher_fixture):
    """Test publishing announcements to a class offering."""
    context = teacher_fixture["context"]
    offering = teacher_fixture["offering_a"]

    service = TeacherService(db_session)

    ann = await service.create_announcement(
        context,
        offering_id=offering.id,
        title="Midterm Exam Preparation",
        content="Please complete Thermodynamics Milestone 1 before Friday 5 PM.",
    )
    assert ann.title == "Midterm Exam Preparation"

    announcements = await service.get_announcements(context, offering.id)
    assert len(announcements) == 1
    assert announcements[0].title == "Midterm Exam Preparation"
