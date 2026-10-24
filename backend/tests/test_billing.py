"""Tests for Phase P16: Billing, Subscriptions, Entitlements and Institution Fees."""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rbac import RoleEnum, TenantContext
from app.db.base import Base
from app.db.models.identity import UserAccount
from app.db.models.organization import (
    GuardianRelationship,
    Membership,
    Organization,
    RoleAssignment,
)
from app.domain.billing.gateway import MockPaymentGateway
from app.domain.billing.service import BillingService


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
async def billing_fixture(db_session: AsyncSession):
    """Fixture with organizations, users, roles, and guardian relationship."""
    ts = datetime.now().timestamp()

    # 1. Organizations
    org_alpha = Organization(name="Alpha University", slug=f"alpha-{int(ts)}", status="active")
    org_beta = Organization(name="Beta Institute", slug=f"beta-{int(ts)}", status="active")
    db_session.add_all([org_alpha, org_beta])
    await db_session.flush()

    # 2. Users
    admin_alpha = UserAccount(
        email=f"admin.{ts}@alpha.edu", full_name="Admin Alpha", is_active=True
    )
    student_alpha = UserAccount(
        email=f"student.{ts}@alpha.edu", full_name="Student Alpha", is_active=True
    )
    parent_alpha = UserAccount(
        email=f"parent.{ts}@gmail.com", full_name="Parent Alpha", is_active=True
    )
    super_admin = UserAccount(
        email=f"super.{ts}@gayatri.cloud", full_name="Super Admin", is_active=True
    )
    db_session.add_all([admin_alpha, student_alpha, parent_alpha, super_admin])
    await db_session.flush()

    # 3. Memberships
    m_admin = Membership(user_id=admin_alpha.id, organization_id=org_alpha.id, status="active")
    m_student = Membership(user_id=student_alpha.id, organization_id=org_alpha.id, status="active")
    m_parent = Membership(user_id=parent_alpha.id, organization_id=org_alpha.id, status="active")
    db_session.add_all([m_admin, m_student, m_parent])
    await db_session.flush()

    # 4. Roles
    db_session.add_all(
        [
            RoleAssignment(membership_id=m_admin.id, role=RoleEnum.ORG_ADMIN.value),
            RoleAssignment(membership_id=m_student.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_parent.id, role=RoleEnum.PARENT.value),
        ]
    )

    # 5. Guardian Relationship
    guardian_link = GuardianRelationship(
        guardian_id=parent_alpha.id,
        student_id=student_alpha.id,
        verification_status="verified",
        is_active=True,
    )
    db_session.add(guardian_link)
    await db_session.commit()

    # Contexts
    ctx_admin_a = TenantContext(
        user=admin_alpha, organization_id=org_alpha.id, roles=[RoleEnum.ORG_ADMIN.value]
    )
    ctx_student_a = TenantContext(
        user=student_alpha, organization_id=org_alpha.id, roles=[RoleEnum.STUDENT.value]
    )
    ctx_parent_a = TenantContext(
        user=parent_alpha, organization_id=org_alpha.id, roles=[RoleEnum.PARENT.value]
    )
    ctx_personal = TenantContext(
        user=student_alpha, organization_id=None, roles=[RoleEnum.STUDENT.value]
    )
    ctx_super = TenantContext(
        user=super_admin, organization_id=None, roles=[RoleEnum.SUPER_ADMIN.value]
    )

    return {
        "org_alpha": org_alpha,
        "org_beta": org_beta,
        "admin_alpha": admin_alpha,
        "student_alpha": student_alpha,
        "parent_alpha": parent_alpha,
        "ctx_admin_a": ctx_admin_a,
        "ctx_student_a": ctx_student_a,
        "ctx_parent_a": ctx_parent_a,
        "ctx_personal": ctx_personal,
        "ctx_super": ctx_super,
    }


@pytest.mark.asyncio
async def test_default_plans_and_entitlements(db_session: AsyncSession, billing_fixture):
    """Verifies baseline freemium plans are seeded and default free tier entitlements returned."""
    ctx_personal = billing_fixture["ctx_personal"]
    service = BillingService(db_session)

    # 1. List plans
    plans = await service.list_plans()
    assert len(plans) >= 4
    codes = [p["code"] for p in plans]
    assert "free" in codes
    assert "pro_learner" in codes
    assert "institution_standard" in codes
    assert "institution_enterprise" in codes

    # 2. Free tier entitlements by default
    sub = await service.get_active_subscription(ctx_personal)
    assert sub["status"] == "free_tier"
    assert sub["plan_code"] == "free"
    assert "tutoring:basic" in sub["entitlements"]
    assert "BYOK" in sub["byok_disclaimer"]


@pytest.mark.asyncio
async def test_subscription_checkout_and_idempotency(db_session: AsyncSession, billing_fixture):
    """Subscribing to a plan charges gateway, updates period, generates receipt, and protects against replay."""
    ctx_personal = billing_fixture["ctx_personal"]
    service = BillingService(db_session)

    idempotency_key = f"idem-key-{uuid.uuid4().hex[:12]}"

    # 1. Subscribe to Pro Learner tier
    sub_res = await service.subscribe(ctx_personal, "pro_learner", idempotency_key)
    assert sub_res["status"] == "succeeded"
    assert sub_res["plan_code"] == "pro_learner"
    assert sub_res["amount_paid_cents"] == 1200
    assert "INV-" in sub_res["invoice_number"]

    # 2. Check active subscription
    active = await service.get_active_subscription(ctx_personal)
    assert active["status"] == "active"
    assert active["plan_code"] == "pro_learner"
    assert "tutoring:advanced" in active["entitlements"]
    assert "rag:custom_uploads" in active["entitlements"]

    # 3. Duplicate checkout with SAME idempotency key (must NOT double-charge)
    replay_res = await service.subscribe(ctx_personal, "pro_learner", idempotency_key)
    assert replay_res.get("is_replay") is True
    assert replay_res["transaction_id"] == sub_res["transaction_id"]


@pytest.mark.asyncio
async def test_plan_upgrade_and_cancellation(db_session: AsyncSession, billing_fixture):
    """Test switching plans and canceling at end of billing cycle."""
    ctx_admin_a = billing_fixture["ctx_admin_a"]
    service = BillingService(db_session)

    # 1. Institutional subscription
    key1 = f"idem-{uuid.uuid4().hex[:12]}"
    await service.subscribe(ctx_admin_a, "institution_standard", key1)

    active = await service.get_active_subscription(ctx_admin_a)
    assert active["plan_code"] == "institution_standard"
    assert active["seat_limit"] == 250

    # 2. Upgrade to Enterprise
    key2 = f"idem-{uuid.uuid4().hex[:12]}"
    upgraded = await service.subscribe(ctx_admin_a, "institution_enterprise", key2)
    assert upgraded["plan_code"] == "institution_enterprise"

    active_up = await service.get_active_subscription(ctx_admin_a)
    assert active_up["plan_code"] == "institution_enterprise"
    assert active_up["seat_limit"] == 1000

    # 3. Cancel subscription
    canceled = await service.cancel_subscription(ctx_admin_a)
    assert canceled["cancel_at_period_end"] is True

    active_canceled = await service.get_active_subscription(ctx_admin_a)
    assert active_canceled["cancel_at_period_end"] is True


@pytest.mark.asyncio
async def test_institution_fee_lifecycle_and_student_payment(
    db_session: AsyncSession, billing_fixture
):
    """Org-admin creates fee; student or parent pays; receipt is generated."""
    ctx_admin_a = billing_fixture["ctx_admin_a"]
    ctx_student_a = billing_fixture["ctx_student_a"]
    ctx_parent_a = billing_fixture["ctx_parent_a"]
    org_a = billing_fixture["org_alpha"]
    student_a = billing_fixture["student_alpha"]

    service = BillingService(db_session)

    # 1. Org admin creates a lab materials fee
    fee = await service.create_institution_fee(
        context=ctx_admin_a,
        org_id=org_a.id,
        title="Physics Lab Equipment Fee",
        description="Covers optical sensors and lab manual.",
        amount_cents=3500,  # $35.00
        currency="USD",
        due_date=datetime.now(UTC) + timedelta(days=15),
    )
    assert fee["title"] == "Physics Lab Equipment Fee"
    assert fee["amount_cents"] == 3500

    # 2. Student views payable fees
    student_fees = await service.list_student_fees(ctx_student_a)
    assert len(student_fees) == 1
    assert student_fees[0]["fee_id"] == fee["id"]
    assert student_fees[0]["is_paid"] is False

    # 3. Parent views linked child's payable fees
    parent_view_fees = await service.list_student_fees(ctx_parent_a, target_student_id=student_a.id)
    assert len(parent_view_fees) == 1
    assert parent_view_fees[0]["is_paid"] is False

    # 4. Parent pays fee on behalf of student
    pay_key = f"pay-{uuid.uuid4().hex[:12]}"
    payment = await service.pay_student_fee(
        context=ctx_parent_a,
        fee_id=fee["id"],
        idempotency_key=pay_key,
        student_id=student_a.id,
    )
    assert payment["status"] == "completed"
    assert payment["amount_paid_cents"] == 3500
    assert "FEE-" in payment["invoice_number"]

    # 5. Check student fees again (now paid)
    updated_fees = await service.list_student_fees(ctx_student_a)
    assert updated_fees[0]["is_paid"] is True
    assert updated_fees[0]["paid_at"] is not None

    # 6. Replaying same idempotency key does NOT double charge
    replay_payment = await service.pay_student_fee(
        context=ctx_parent_a,
        fee_id=fee["id"],
        idempotency_key=pay_key,
        student_id=student_a.id,
    )
    assert replay_payment.get("is_replay") is True


@pytest.mark.asyncio
async def test_cross_tenant_fee_isolation(db_session: AsyncSession, billing_fixture):
    """Org-admin is strictly prevented from creating or listing fees in another organization."""
    ctx_admin_a = billing_fixture["ctx_admin_a"]
    org_b = billing_fixture["org_beta"]

    service = BillingService(db_session)

    # 1. Org admin of Alpha CANNOT create fee for Beta
    with pytest.raises(HTTPException) as exc:
        await service.create_institution_fee(
            context=ctx_admin_a,
            org_id=org_b.id,
            title="Sneaky Fee",
            description="Unauthorized cross-tenant fee",
            amount_cents=5000,
        )
    assert exc.value.status_code == 403

    # 2. Org admin of Alpha CANNOT list fees for Beta
    with pytest.raises(HTTPException) as exc:
        await service.list_institution_fees(ctx_admin_a, org_id=org_b.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_webhook_cryptographic_verification(db_session: AsyncSession):
    """Tests cryptographic signature validation and idempotent webhook event replay protection."""
    gateway = MockPaymentGateway(webhook_secret="test-super-secret-key-32chars")
    service = BillingService(db_session, gateway=gateway)

    payload = {
        "id": "evt_test_12345",
        "type": "payment_intent.succeeded",
        "data": {"amount": 2500},
    }
    raw_body = json.dumps(payload).encode("utf-8")

    # 1. Valid signature
    valid_sig = gateway.compute_signature(raw_body, secret="test-super-secret-key-32chars")
    res = await service.process_webhook(raw_body, valid_sig)
    assert res["status"] == "processed"
    assert res["signature_verified"] is True

    # 2. Invalid / forged signature
    with pytest.raises(HTTPException) as exc:
        await service.process_webhook(raw_body, "t=1700000000,v1=badbadbadbadbadbadbadbad")
    assert exc.value.status_code == 400
    assert "Invalid cryptographic webhook signature" in exc.value.detail
