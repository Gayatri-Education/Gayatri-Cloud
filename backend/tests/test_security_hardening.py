"""Tests for Phase P18: Security, Privacy, Retention, and Deletion Hardening."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rbac import RoleEnum, TenantContext
from app.db.base import Base
from app.db.models.billing import FeePayment, InstitutionFee
from app.db.models.course import Course, CourseEnrollment, CourseOffering, CourseVersion
from app.db.models.identity import SessionDevice, UserAccount
from app.db.models.organization import Membership, Organization, RoleAssignment
from app.domain.security.deletion import DeletionService
from app.domain.security.ssrf_guard import sanitize_storage_key, validate_outbound_url


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


@pytest.fixture
async def security_fixture(db_session: AsyncSession):
    """Fixture providing organizations, users with sessions, courses, enrollments, and fees."""
    ts = datetime.now(UTC).timestamp()

    # 1. Organizations
    org = Organization(name="Secure Academy", slug=f"sec-acad-{int(ts)}", status="active")
    db_session.add(org)
    await db_session.flush()

    # 2. Users
    user_a = UserAccount(email=f"alice.{ts}@example.com", full_name="Alice Student", is_active=True)
    user_b = UserAccount(email=f"bob.{ts}@example.com", full_name="Bob Malicious", is_active=True)
    super_admin = UserAccount(
        email=f"admin.{ts}@gayatri.edu",
        full_name="Platform Admin",
        is_active=True,
        is_super_admin=True,
    )
    db_session.add_all([user_a, user_b, super_admin])
    await db_session.flush()

    # 3. Memberships
    m_a = Membership(user_id=user_a.id, organization_id=org.id, status="active")
    m_b = Membership(user_id=user_b.id, organization_id=org.id, status="active")
    m_admin = Membership(user_id=super_admin.id, organization_id=org.id, status="active")
    db_session.add_all([m_a, m_b, m_admin])
    await db_session.flush()

    db_session.add_all(
        [
            RoleAssignment(membership_id=m_a.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_b.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_admin.id, role=RoleEnum.SUPER_ADMIN.value),
        ]
    )

    # 4. Active Device Sessions for Alice
    s1 = SessionDevice(
        user_id=user_a.id,
        refresh_token_hash=f"hash-chrome-{ts}",
        user_agent="macbook-chrome",
        ip_address="1.2.3.4",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    s2 = SessionDevice(
        user_id=user_a.id,
        refresh_token_hash=f"hash-safari-{ts}",
        user_agent="iphone-safari",
        ip_address="1.2.3.5",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add_all([s1, s2])

    # 5. Course & Enrollment
    course = Course(organization_id=org.id, code=f"SEC-{int(ts)}", title="Cybersecurity 101")
    db_session.add(course)
    await db_session.flush()

    v1 = CourseVersion(course_id=course.id, version_tag="v1.0.0", status="published")
    db_session.add(v1)
    await db_session.flush()

    offering = CourseOffering(
        organization_id=org.id,
        course_version_id=v1.id,
        term="Fall 2026",
    )
    db_session.add(offering)
    await db_session.flush()

    enrollment = CourseEnrollment(student_id=user_a.id, offering_id=offering.id, status="enrolled")
    db_session.add(enrollment)

    # 6. Statutory Financial Records for Alice (Fee Schedule + Fee Payment)
    fee = InstitutionFee(
        organization_id=org.id,
        title="Fall Tuition",
        description="Term tuition fee",
        amount_cents=50000,
        currency="USD",
        due_date=datetime.now(UTC),
    )
    db_session.add(fee)
    await db_session.flush()

    payment = FeePayment(
        fee_id=fee.id,
        student_id=user_a.id,
        amount_paid_cents=50000,
        currency="USD",
        status="completed",
        payment_intent_id=f"pi-{int(ts)}",
        transaction_reference=f"tx-{int(ts)}",
        paid_at=datetime.now(UTC),
    )
    db_session.add(payment)
    await db_session.commit()

    ctx_a = TenantContext(user=user_a, organization_id=org.id, roles=[RoleEnum.STUDENT.value])
    ctx_b = TenantContext(user=user_b, organization_id=org.id, roles=[RoleEnum.STUDENT.value])
    ctx_admin = TenantContext(
        user=super_admin, organization_id=org.id, roles=[RoleEnum.SUPER_ADMIN.value]
    )

    return {
        "org": org,
        "user_a": user_a,
        "user_b": user_b,
        "super_admin": super_admin,
        "ctx_a": ctx_a,
        "ctx_b": ctx_b,
        "ctx_admin": ctx_admin,
        "payment": payment,
    }


def test_ssrf_guard_blocks_cloud_metadata_and_private_ips():
    """Validates that SSRF guard strictly blocks AWS metadata (169.254.169.254), loopback, and private IPs."""
    # 1. AWS metadata IP literal
    with pytest.raises(HTTPException) as exc:
        validate_outbound_url("http://169.254.169.254/latest/meta-data/")
    assert exc.value.status_code == 400
    assert "restricted" in exc.value.detail or "prohibited" in exc.value.detail

    # 2. Localhost loopback
    with pytest.raises(HTTPException) as exc:
        validate_outbound_url("http://127.0.0.1:8000/internal-admin")
    assert exc.value.status_code == 400

    # 3. RFC-1918 Private networks
    for private_url in [
        "http://10.0.0.1/admin",
        "https://192.168.1.1/config",
        "http://172.16.0.10/database",
    ]:
        with pytest.raises(HTTPException) as exc:
            validate_outbound_url(private_url)
        assert exc.value.status_code == 400

    # 4. Unsupported protocol schemes
    with pytest.raises(HTTPException) as exc:
        validate_outbound_url("file:///etc/passwd")
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        validate_outbound_url("ftp://internal.backup/files")
    assert exc.value.status_code == 400

    # 5. Valid public HTTPS URL passes
    valid_url = "https://api.openai.com/v1/chat/completions"
    assert validate_outbound_url(valid_url) == valid_url


def test_path_traversal_sanitizer():
    """Validates that directory traversal attempts, null bytes, and root breakouts are rejected."""
    # 1. Path traversal with ..
    with pytest.raises(HTTPException) as exc:
        sanitize_storage_key("../../etc/passwd")
    assert exc.value.status_code == 400
    assert "Path traversal" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        sanitize_storage_key("uploads\\..\\..\\windows\\system32\\cmd.exe")
    assert exc.value.status_code == 400

    # 2. Null byte injection
    with pytest.raises(HTTPException) as exc:
        sanitize_storage_key("uploads/syllabus.pdf\x00.exe")
    assert exc.value.status_code == 400
    assert "Null byte" in exc.value.detail

    # 3. Clean path normalized
    assert (
        sanitize_storage_key("/courses/v1/quantum_lecture.pdf") == "courses/v1/quantum_lecture.pdf"
    )
    assert sanitize_storage_key("org-123/documents/notes.txt") == "org-123/documents/notes.txt"


@pytest.mark.asyncio
async def test_data_export_generation_and_cross_user_isolation(
    db_session: AsyncSession, security_fixture
):
    """Verifies GDPR Art. 20 data export generation, SHA-256 verification, and strict cross-user denial."""
    ctx_a = security_fixture["ctx_a"]
    ctx_b = security_fixture["ctx_b"]
    user_a = security_fixture["user_a"]

    service = DeletionService(db_session)

    # 1. Alice exports her own data -> SUCCESS
    export = await service.generate_user_data_export(ctx_a, user_a.id)
    assert export["user_profile"]["id"] == user_a.id
    assert export["user_profile"]["email"] == user_a.email
    assert len(export["memberships"]) == 1
    assert len(export["enrollments"]) == 1
    assert len(export["checksum_sha256"]) == 64

    # 2. Bob attempts to export Alice's data -> 403 FORBIDDEN
    with pytest.raises(HTTPException) as exc:
        await service.generate_user_data_export(ctx_b, user_a.id)
    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail


@pytest.mark.asyncio
async def test_account_deletion_grace_period_and_cancellation(
    db_session: AsyncSession, security_fixture
):
    """Verifies 7-day grace period, immediate session invalidation, and request cancellation."""
    ctx_a = security_fixture["ctx_a"]
    user_a = security_fixture["user_a"]
    service = DeletionService(db_session)

    # 1. Request deletion with 7-day grace period
    res = await service.request_account_deletion(
        ctx_a, user_a.id, reason="Graduated course", immediate=False
    )
    assert res["status"] == "pending"
    assert "7-day grace period" in res["message"]

    # Invariants: User account marked inactive immediately
    assert user_a.is_active is False

    # 2. Check deletion status
    status_info = await service.get_deletion_status(ctx_a, user_a.id)
    assert status_info["has_active_request"] is True
    assert status_info["status"] == "pending"

    # 3. User cancels deletion request -> restored
    cancel_res = await service.cancel_deletion_request(ctx_a, user_a.id)
    assert cancel_res["status"] == "cancelled"
    assert user_a.is_active is True

    # Check status again
    status_after = await service.get_deletion_status(ctx_a, user_a.id)
    assert status_after["has_active_request"] is False
    assert status_after["status"] == "cancelled"


@pytest.mark.asyncio
async def test_account_deletion_statutory_financial_hold_retention(
    db_session: AsyncSession, security_fixture
):
    """Verifies that user account deletion preserves tax/financial records under statutory legal hold (RQ-027, P16)."""
    ctx_a = security_fixture["ctx_a"]
    user_a = security_fixture["user_a"]
    service = DeletionService(db_session)

    # Execute immediate deletion
    res = await service.request_account_deletion(
        ctx_a, user_a.id, reason="Right to be forgotten", immediate=True
    )
    assert res["status"] == "completed"
    assert "statutory financial records preserved" in res["message"]

    # 1. User PII is pseudonymized
    assert user_a.is_deleted is True
    assert user_a.is_active is False
    assert user_a.full_name == "Anonymized Former Learner"
    assert user_a.email.endswith("@anonymized.internal")

    # 2. Statutory financial records are preserved
    assert res["legal_hold_retained_records"] is not None
    assert "fee_payments" in res["legal_hold_retained_records"]


@pytest.mark.asyncio
async def test_deletion_cross_user_denial(db_session: AsyncSession, security_fixture):
    """Bob cannot request deletion for Alice (403 Forbidden)."""
    ctx_b = security_fixture["ctx_b"]
    user_a = security_fixture["user_a"]
    service = DeletionService(db_session)

    with pytest.raises(HTTPException) as exc:
        await service.request_account_deletion(
            ctx_b, user_a.id, reason="Malicious deletion attempt"
        )
    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail


@pytest.mark.asyncio
async def test_comprehensive_security_headers(async_client):
    """Verify that all hardened OWASP security headers are present on API responses."""
    res = await async_client.get("/health")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert "camera=()" in headers.get("Permissions-Policy", "")
    assert "max-age=31536000" in headers.get("Strict-Transport-Security", "")
