"""End-to-End Integrated Lifecycle Journey Tests for Gayatri Cloud (P20).
Executes the full 12-milestone lifecycle across all platform subsystems.
"""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rbac import RoleEnum, TenantContext
from app.core.security import hash_password, verify_password
from app.db.base import Base
from app.db.models.course import (
    ContentChunk,
    ContentSource,
    Course,
    CourseEnrollment,
    CourseOffering,
    CourseVersion,
    TeacherInstruction,
)
from app.db.models.identity import AuthIdentity, UserAccount
from app.db.models.organization import (
    GuardianRelationship,
    Membership,
    Organization,
    RoleAssignment,
)
from app.db.models.teacher import TeacherIntervention
from app.domain.admin.service import AdminService
from app.domain.billing.service import BillingService
from app.domain.i18n.offline import OfflineService
from app.domain.i18n.registry import TranslationRegistry
from app.domain.parent.service import ParentService
from app.domain.security.deletion import DeletionService
from app.domain.teacher.service import TeacherService


@pytest.fixture
async def db_session():
    """Isolated in-memory test DB session."""
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
async def test_full_system_lifecycle_journey(db_session: AsyncSession):
    """Executes the complete 12-milestone journey from registration to deletion."""
    ts = int(datetime.now(UTC).timestamp())

    # =========================================================================
    # Milestone 1: User Registration & Identity Setup
    # =========================================================================
    learner_pwd = "SecureLearnerPass123!"
    learner = UserAccount(
        email=f"ananya.{ts}@iit.ac.in",
        full_name="Ananya Roy",
        is_active=True,
        is_verified=True,
    )
    teacher = UserAccount(
        email=f"prof.sharma.{ts}@iit.ac.in",
        full_name="Prof. Rajesh Sharma",
        is_active=True,
        is_verified=True,
    )
    parent = UserAccount(
        email=f"parent.{ts}@gmail.com",
        full_name="Sunita Roy",
        is_active=True,
        is_verified=True,
    )
    admin_user = UserAccount(
        email=f"admin.{ts}@iit.ac.in",
        full_name="Admin IIT",
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([learner, teacher, parent, admin_user])
    await db_session.flush()

    learner_auth = AuthIdentity(
        user_id=learner.id,
        provider="email",
        credential_hash=hash_password(learner_pwd),
    )
    db_session.add(learner_auth)
    await db_session.flush()

    assert verify_password(learner_pwd, learner_auth.credential_hash) is True

    # =========================================================================
    # Milestone 2: Organization & RBAC Lifecycle with RQ-003 Invariant
    # =========================================================================
    org = Organization(name="IIT Bombay Online", slug=f"iitb-{ts}", status="active")
    db_session.add(org)
    await db_session.flush()

    m_learner = Membership(user_id=learner.id, organization_id=org.id, status="active")
    m_teacher = Membership(user_id=teacher.id, organization_id=org.id, status="active")
    m_parent = Membership(user_id=parent.id, organization_id=org.id, status="active")
    m_admin = Membership(user_id=admin_user.id, organization_id=org.id, status="active")
    db_session.add_all([m_learner, m_teacher, m_parent, m_admin])
    await db_session.flush()

    db_session.add_all(
        [
            RoleAssignment(membership_id=m_learner.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_teacher.id, role=RoleEnum.TEACHER.value),
            RoleAssignment(membership_id=m_parent.id, role=RoleEnum.PARENT.value),
            RoleAssignment(membership_id=m_admin.id, role=RoleEnum.ORG_ADMIN.value),
        ]
    )
    await db_session.flush()

    admin_svc = AdminService(db_session)
    admin_ctx = TenantContext(
        user=admin_user, organization_id=org.id, roles=[RoleEnum.ORG_ADMIN.value]
    )

    # Invariant RQ-003 Check: Attempting to assign TEACHER role to Ananya (who is a STUDENT) fails
    with pytest.raises(HTTPException) as exc_info:
        await admin_svc.update_member_role(
            context=admin_ctx,
            org_id=org.id,
            membership_id=m_learner.id,
            new_role=RoleEnum.TEACHER.value,
        )
    assert exc_info.value.status_code == 400
    assert "RQ-003" in exc_info.value.detail

    # Negative Isolation Check: External organization admin cannot mutate IIT Bombay member
    rogue_org = Organization(name="Rogue University", slug=f"rogue-{ts}", status="active")
    db_session.add(rogue_org)
    await db_session.flush()
    rogue_admin_ctx = TenantContext(
        user=admin_user, organization_id=rogue_org.id, roles=[RoleEnum.ORG_ADMIN.value]
    )
    with pytest.raises(HTTPException) as exc_cross:
        await admin_svc.update_member_role(
            context=rogue_admin_ctx,
            org_id=org.id,
            membership_id=m_learner.id,
            new_role=RoleEnum.STUDENT.value,
        )
    assert exc_cross.value.status_code == 403

    # =========================================================================
    # Milestone 3: Course Creation, Content Ingestion & Immutable Publishing
    # =========================================================================
    course = Course(
        organization_id=org.id,
        code=f"CS-{ts}",
        title="Distributed Systems & Cloud Computing",
        description="Consensus algorithms, Raft, Paxos, and fault tolerance.",
    )
    db_session.add(course)
    await db_session.flush()

    v1 = CourseVersion(
        course_id=course.id,
        version_tag="v1.0.0",
        status="published",
        changelog="First official release",
    )
    db_session.add(v1)
    await db_session.flush()

    source = ContentSource(
        course_version_id=v1.id,
        filename="raft_paper.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048576,
        s3_uri="s3://gayatri-courses/raft_paper.pdf",
        checksum_sha256="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        ingestion_status="completed",
    )
    db_session.add(source)
    await db_session.flush()

    chunk1 = ContentChunk(
        source_id=source.id,
        chunk_index=0,
        text_content="Raft is a consensus algorithm designed to be easy to understand.",
        token_count=12,
        section_header="Introduction to Raft",
    )
    chunk2 = ContentChunk(
        source_id=source.id,
        chunk_index=1,
        text_content="Leader election occurs when a follower times out waiting for a heartbeat.",
        token_count=14,
        section_header="Leader Election",
    )
    db_session.add_all([chunk1, chunk2])
    await db_session.flush()

    # =========================================================================
    # Milestone 4: Cohort Offering Deployment & Student Enrollment
    # =========================================================================
    offering = CourseOffering(
        organization_id=org.id,
        course_version_id=v1.id,
        term="Autumn 2026",
        status="active",
    )
    db_session.add(offering)
    await db_session.flush()

    enrollment = CourseEnrollment(
        student_id=learner.id,
        offering_id=offering.id,
        status="enrolled",
    )
    db_session.add(enrollment)
    await db_session.flush()

    # =========================================================================
    # Milestone 5 & 6: 5-Tier Teacher Instructions & Tutor Turn
    # =========================================================================
    instruction = TeacherInstruction(
        organization_id=org.id,
        teacher_id=teacher.id,
        course_id=course.id,
        tier="COURSE",
        priority=3,
        directive_text="Guide students using Socratic hints before revealing Paxos vs Raft tradeoffs.",
        is_active=True,
    )
    db_session.add(instruction)
    await db_session.flush()

    teacher_svc = TeacherService(db_session)
    teacher_ctx = TenantContext(
        user=teacher, organization_id=org.id, roles=[RoleEnum.TEACHER.value]
    )
    active_instructions = await teacher_svc.list_instructions(teacher_ctx, course_id=course.id)
    assert len(active_instructions) == 1
    assert "Socratic" in active_instructions[0].directive_text

    # =========================================================================
    # Milestone 7 & 8: Teacher Interventions & Cohort Management
    # =========================================================================
    intervention = TeacherIntervention(
        organization_id=org.id,
        offering_id=offering.id,
        student_id=learner.id,
        concept_id="c_leader_election",
        status="PENDING",
        severity="HIGH",
        reason="Needs clarification on split vote resolution",
    )
    db_session.add(intervention)
    await db_session.flush()

    resolved_iv = await teacher_svc.acknowledge_intervention(
        teacher_ctx, intervention.id, resolution_notes="Completed review session", resolve=True
    )
    assert resolved_iv.status == "RESOLVED"
    assert resolved_iv.resolution_notes == "Completed review session"

    # =========================================================================
    # Milestone 9: Parent Guardian Link & Privacy-Filtered Progress
    # =========================================================================
    guardian_rel = GuardianRelationship(
        guardian_id=parent.id,
        student_id=learner.id,
        verification_status="verified",
        is_active=True,
    )
    db_session.add(guardian_rel)
    await db_session.flush()

    parent_svc = ParentService(db_session)
    parent_ctx = TenantContext(user=parent, organization_id=org.id, roles=[RoleEnum.PARENT.value])
    children = await parent_svc.list_linked_children(parent_ctx)
    assert len(children) == 1
    assert children[0]["student_name"] == "Ananya Roy"

    # =========================================================================
    # Milestone 10: Billing Freemium Subscriptions & Institutional Fees
    # =========================================================================
    billing_svc = BillingService(db_session)

    fee_schedule = await billing_svc.create_institution_fee(
        admin_ctx,
        org_id=org.id,
        title="Lab & Cloud Computing Fee",
        description="Server cluster compute allocation",
        amount_cents=15000,
        currency="USD",
    )
    assert fee_schedule["amount_cents"] == 15000

    # Student pays fee with idempotency
    learner_ctx = TenantContext(
        user=learner, organization_id=org.id, roles=[RoleEnum.STUDENT.value]
    )
    payment_res = await billing_svc.pay_student_fee(
        context=learner_ctx,
        fee_id=fee_schedule["id"],
        idempotency_key=f"pay-idem-{ts}",
    )
    assert payment_res["status"] == "completed"
    assert payment_res["amount_paid_cents"] == 15000

    # Idempotent replay check returns same status without duplicate payment
    replay_res = await billing_svc.pay_student_fee(
        context=learner_ctx,
        fee_id=fee_schedule["id"],
        idempotency_key=f"pay-idem-{ts}",
    )
    assert replay_res["is_replay"] is True
    assert replay_res["amount_paid_cents"] == 15000

    # =========================================================================
    # Milestone 11: Multilingual Registry & Offline Bundle Packaging
    # =========================================================================
    # Verify 8 languages supported
    langs = TranslationRegistry.get_supported_languages()
    assert len(langs) == 8
    assert TranslationRegistry.get_text("courses", lang="hi") == "पाठ्यक्रम"
    assert TranslationRegistry.get_text("tutor", lang="sa") == "एआई गुरुः"

    # Offline lesson bundle packaging with SHA-256
    offline_svc = OfflineService(db_session)
    bundle = await offline_svc.package_course_bundle(learner_ctx, course.id)
    assert bundle["course_id"] == course.id
    assert bundle["lessons_count"] == 2
    assert len(bundle["sha256_checksum"]) == 64
    assert "Reading mode active" in bundle["offline_guidance"]

    # =========================================================================
    # Milestone 12: GDPR Art. 20 Data Export & Account Deletion (Legal Hold)
    # =========================================================================
    sec_svc = DeletionService(db_session)

    # 1. Export data archive
    export_archive = await sec_svc.generate_user_data_export(learner_ctx, learner.id)
    assert export_archive["user_profile"]["id"] == learner.id
    assert len(export_archive["checksum_sha256"]) == 64

    # 2. Request account deletion (immediate=True)
    del_res = await sec_svc.request_account_deletion(
        learner_ctx, learner.id, reason="Graduation", immediate=True
    )
    assert del_res["status"] == "completed"

    # 3. Statutory legal hold verification (RQ-027, P16):
    # Because learner paid an institutional fee, accounting records are preserved, PII pseudonymized
    assert learner.is_deleted is True
    assert learner.full_name == "Anonymized Former Learner"
    assert learner.email.endswith("@anonymized.internal")
    assert "fee_payments" in del_res["legal_hold_retained_records"]
