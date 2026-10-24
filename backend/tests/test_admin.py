"""Tests for Phase P15: Super-Admin and Organization-Admin domain, security boundaries, and APIs."""

from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rbac import RoleEnum, TenantContext
from app.db.base import Base
from app.db.models.ai import ProviderConnection
from app.db.models.events import ApplicationEvent, EventOutbox
from app.db.models.identity import UserAccount
from app.db.models.organization import (
    Membership,
    Organization,
    RoleAssignment,
)
from app.domain.admin.service import AdminService


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
async def admin_fixture(db_session: AsyncSession):
    """Fixture providing organizations, super-admin, org-admins, and members."""
    ts = datetime.now().timestamp()

    # 1. Organizations: Org Alpha & Org Beta
    org_a = Organization(name="Alpha University", slug=f"alpha-{int(ts)}", status="active")
    org_b = Organization(name="Beta Institute", slug=f"beta-{int(ts)}", status="active")
    db_session.add_all([org_a, org_b])
    await db_session.flush()

    # 2. Users
    super_admin = UserAccount(
        email=f"super.admin.{ts}@gayatri.cloud", full_name="Super Administrator", is_active=True
    )
    org_admin_a = UserAccount(
        email=f"dean.alpha.{ts}@alpha.edu", full_name="Dean Alpha", is_active=True
    )
    student_a = UserAccount(
        email=f"student.alpha.{ts}@alpha.edu", full_name="Student Alpha", is_active=True
    )
    teacher_a = UserAccount(
        email=f"teacher.alpha.{ts}@alpha.edu", full_name="Teacher Alpha", is_active=True
    )
    db_session.add_all([super_admin, org_admin_a, student_a, teacher_a])
    await db_session.flush()

    # 3. Memberships
    m_admin_a = Membership(user_id=org_admin_a.id, organization_id=org_a.id, status="active")
    m_student_a = Membership(user_id=student_a.id, organization_id=org_a.id, status="active")
    m_teacher_a = Membership(user_id=teacher_a.id, organization_id=org_a.id, status="active")
    db_session.add_all([m_admin_a, m_student_a, m_teacher_a])
    await db_session.flush()

    # 4. Roles
    db_session.add_all(
        [
            RoleAssignment(membership_id=m_admin_a.id, role=RoleEnum.ORG_ADMIN.value),
            RoleAssignment(membership_id=m_student_a.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_teacher_a.id, role=RoleEnum.TEACHER.value),
        ]
    )
    await db_session.flush()

    # Contexts
    ctx_super = TenantContext(
        user=super_admin,
        organization_id=org_a.id,
        roles=[RoleEnum.SUPER_ADMIN.value],
    )
    ctx_org_a = TenantContext(
        user=org_admin_a,
        organization_id=org_a.id,
        roles=[RoleEnum.ORG_ADMIN.value],
    )

    await db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "super_admin": super_admin,
        "org_admin_a": org_admin_a,
        "student_a": student_a,
        "teacher_a": teacher_a,
        "m_admin_a": m_admin_a,
        "m_student_a": m_student_a,
        "m_teacher_a": m_teacher_a,
        "ctx_super": ctx_super,
        "ctx_org_a": ctx_org_a,
    }


@pytest.mark.asyncio
async def test_super_admin_vs_org_admin_scope(db_session: AsyncSession, admin_fixture):
    """Super-admin can manage any org; Org-admin is strictly confined to their tenant."""
    ctx_super = admin_fixture["ctx_super"]
    ctx_org_a = admin_fixture["ctx_org_a"]
    org_a = admin_fixture["org_a"]
    org_b = admin_fixture["org_b"]

    service = AdminService(db_session)

    # 1. Org-admin can access Org A
    details_a = await service.get_organization(ctx_org_a, org_a.id)
    assert details_a["id"] == org_a.id

    # 2. Org-admin CANNOT access Org B (cross-tenant negative test)
    with pytest.raises(HTTPException) as exc:
        await service.get_organization(ctx_org_a, org_b.id)
    assert exc.value.status_code == 403
    assert "Cross-tenant administration denied" in exc.value.detail

    # 3. Super-admin can access both Org A and Org B
    details_super_b = await service.get_organization(ctx_super, org_b.id)
    assert details_super_b["id"] == org_b.id


@pytest.mark.asyncio
async def test_organization_suspension_and_reactivation(db_session: AsyncSession, admin_fixture):
    """Global organization suspension/reactivation requires SUPER_ADMIN and mandatory reason."""
    ctx_super = admin_fixture["ctx_super"]
    ctx_org_a = admin_fixture["ctx_org_a"]
    org_b = admin_fixture["org_b"]

    service = AdminService(db_session)

    # 1. Org-admin cannot suspend an organization
    with pytest.raises(HTTPException) as exc:
        await service.suspend_organization(ctx_org_a, org_b.id, reason="Policy breach")
    assert exc.value.status_code == 403
    assert "SUPER_ADMIN" in exc.value.detail

    # 2. Super-admin must provide reason
    with pytest.raises(HTTPException) as exc:
        await service.suspend_organization(ctx_super, org_b.id, reason="   ")
    assert exc.value.status_code == 400

    # 3. Super-admin suspends with reason
    suspended = await service.suspend_organization(
        ctx_super, org_b.id, reason="Overdue account audit inspection."
    )
    assert suspended["status"] == "suspended"

    # 4. Super-admin reactivates with reason
    reactivated = await service.reactivate_organization(
        ctx_super, org_b.id, reason="Compliance audit successfully completed."
    )
    assert reactivated["status"] == "active"


@pytest.mark.asyncio
async def test_domain_proof_and_verification(db_session: AsyncSession, admin_fixture):
    """Test registering domain, generating DNS verification token, and completing proof."""
    ctx_org_a = admin_fixture["ctx_org_a"]
    org_a = admin_fixture["org_a"]

    service = AdminService(db_session)

    # 1. Register domain
    dom = await service.add_domain(ctx_org_a, org_a.id, "alpha.edu")
    assert dom["domain_name"] == "alpha.edu"
    assert dom["is_verified"] is False
    assert "gayatri-verify-" in dom["verification_token"]

    # 2. Verify domain
    verified = await service.verify_domain(ctx_org_a, org_a.id, dom["id"])
    assert verified["is_verified"] is True

    # 3. List domains
    domains = await service.list_domains(ctx_org_a, org_a.id)
    assert len(domains) == 1
    assert domains[0]["domain_name"] == "alpha.edu"
    assert domains[0]["is_verified"] is True


@pytest.mark.asyncio
async def test_member_role_update_enforces_rq003(db_session: AsyncSession, admin_fixture):
    """Updating member role enforces RQ-003: Student and Teacher roles cannot coexist in an organization."""
    ctx_org_a = admin_fixture["ctx_org_a"]
    org_a = admin_fixture["org_a"]
    m_student_a = admin_fixture["m_student_a"]
    m_teacher_a = admin_fixture["m_teacher_a"]

    service = AdminService(db_session)

    # 1. Attempting to add TEACHER role to a member with STUDENT role is rejected
    with pytest.raises(HTTPException) as exc:
        await service.update_member_role(
            ctx_org_a, org_a.id, m_student_a.id, RoleEnum.TEACHER.value
        )
    assert exc.value.status_code == 400
    assert "Incompatible role combination" in exc.value.detail
    assert "RQ-003" in exc.value.detail

    # 2. Attempting to add STUDENT role to a member with TEACHER role is rejected
    with pytest.raises(HTTPException) as exc:
        await service.update_member_role(
            ctx_org_a, org_a.id, m_teacher_a.id, RoleEnum.STUDENT.value
        )
    assert exc.value.status_code == 400
    assert "Incompatible role combination" in exc.value.detail

    # 3. Changing STUDENT to PARENT is permitted (Teacher + Parent / Parent allowed)
    upd = await service.update_member_role(
        ctx_org_a, org_a.id, m_student_a.id, RoleEnum.PARENT.value
    )
    assert upd["assigned_role"] == RoleEnum.PARENT.value


@pytest.mark.asyncio
async def test_member_suspension(db_session: AsyncSession, admin_fixture):
    """Test suspending a member in the tenant."""
    ctx_org_a = admin_fixture["ctx_org_a"]
    org_a = admin_fixture["org_a"]
    m_student_a = admin_fixture["m_student_a"]

    service = AdminService(db_session)
    await service.suspend_member(ctx_org_a, org_a.id, m_student_a.id)

    members = await service.list_members(ctx_org_a, org_a.id)
    student_entry = next(m for m in members if m["membership_id"] == m_student_a.id)
    assert student_entry["status"] == "suspended"


@pytest.mark.asyncio
async def test_ai_policy_configuration(db_session: AsyncSession, admin_fixture):
    """Test updating organization AI routing policy without exposing secret key values."""
    ctx_org_a = admin_fixture["ctx_org_a"]
    org_a = admin_fixture["org_a"]

    service = AdminService(db_session)

    # Add a provider connection
    conn = ProviderConnection(
        organization_id=org_a.id,
        provider_type="openai",
        encrypted_key_ciphertext="enc-secret-xyz-9876",
        key_fingerprint="fp-12345-9876",
        is_active=True,
    )
    db_session.add(conn)
    await db_session.commit()

    # Update AI policy
    upd = await service.update_ai_policy(
        ctx_org_a,
        org_a.id,
        allowed_models=["gpt-4o", "claude-3-5-sonnet"],
        routing_strategy="cost_efficient",
    )
    assert upd["routing_strategy"] == "cost_efficient"
    assert "gpt-4o" in upd["allowed_models"]

    # Retrieve policy
    policy = await service.get_ai_policy(ctx_org_a, org_a.id)
    assert policy["routing_strategy"] == "cost_efficient"
    assert len(policy["configured_providers"]) == 1
    # Key must be masked
    assert "enc-secret" not in policy["configured_providers"][0]["key_masked"]
    assert policy["configured_providers"][0]["key_masked"] == "sk-...9876"


@pytest.mark.asyncio
async def test_audit_search_and_operational_dashboard(db_session: AsyncSession, admin_fixture):
    """Test searching immutable audit logs and aggregating operational telemetry."""
    ctx_org_a = admin_fixture["ctx_org_a"]
    org_a = admin_fixture["org_a"]
    student_a = admin_fixture["student_a"]

    service = AdminService(db_session)

    # Seed an audit event
    event = ApplicationEvent(
        event_type="LEARNING_SESSION_STARTED",
        actor_id=student_a.id,
        organization_id=org_a.id,
        sensitivity_level="INTERNAL",
        payload_json='{"session_id": "ses-101"}',
    )
    db_session.add(event)
    await db_session.flush()

    # Seed an outbox item
    outbox = EventOutbox(
        event_id=event.id,
        status="pending",
        retry_count=0,
    )
    db_session.add(outbox)
    await db_session.commit()

    # 1. Search audit logs
    logs = await service.search_audit_logs(ctx_org_a, org_a.id, category="LEARNING")
    assert len(logs) == 1
    assert logs[0]["event_type"] == "LEARNING_SESSION_STARTED"
    assert logs[0]["actor_id"] == student_a.id

    # 2. Dashboard metrics
    metrics = await service.get_dashboard_metrics(ctx_org_a, org_a.id)
    assert metrics["total_members"] == 3
    assert metrics["outbox_lag_count"] >= 1
    assert metrics["system_health"] == "healthy"
