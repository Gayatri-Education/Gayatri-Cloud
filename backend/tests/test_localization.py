"""Tests for Phase P17: Localization, Accessibility, and Offline Reading."""

from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rbac import RoleEnum, TenantContext
from app.db.base import Base
from app.db.models.course import ContentChunk, ContentSource, Course, CourseVersion
from app.db.models.identity import UserAccount
from app.db.models.organization import Membership, Organization, RoleAssignment
from app.domain.i18n.offline import OfflineService
from app.domain.i18n.registry import LanguageCode, TranslationRegistry


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
async def i18n_fixture(db_session: AsyncSession):
    """Fixture providing courses, versions, chunks, and tenants."""
    ts = datetime.now().timestamp()

    # 1. Organizations
    org_a = Organization(name="Stanford Online", slug=f"stanford-{int(ts)}", status="active")
    org_b = Organization(name="MIT Open", slug=f"mit-{int(ts)}", status="active")
    db_session.add_all([org_a, org_b])
    await db_session.flush()

    # 2. Users
    user_a = UserAccount(
        email=f"learner.{ts}@stanford.edu", full_name="Arjun Sharma", is_active=True
    )
    user_b = UserAccount(email=f"outsider.{ts}@mit.edu", full_name="Bob Smith", is_active=True)
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    # 3. Memberships
    m_a = Membership(user_id=user_a.id, organization_id=org_a.id, status="active")
    m_b = Membership(user_id=user_b.id, organization_id=org_b.id, status="active")
    db_session.add_all([m_a, m_b])
    await db_session.flush()

    db_session.add_all(
        [
            RoleAssignment(membership_id=m_a.id, role=RoleEnum.STUDENT.value),
            RoleAssignment(membership_id=m_b.id, role=RoleEnum.STUDENT.value),
        ]
    )

    # 4. Course with Published Version 1 & 2 Chunks
    course = Course(
        organization_id=org_a.id,
        code=f"QC-{int(ts)}",
        title="Introductory Quantum Mechanics",
        description="Fundamentals of wavefunctions and operators.",
    )
    db_session.add(course)
    await db_session.flush()

    v1 = CourseVersion(
        course_id=course.id,
        version_tag="v1.0.0",
        status="published",
        changelog="Initial release",
    )
    db_session.add(v1)
    await db_session.flush()

    source = ContentSource(
        course_version_id=v1.id,
        filename="intro_quantum.pdf",
        mime_type="application/pdf",
        file_size_bytes=1048576,
        s3_uri="s3://gayatri-courses/intro_quantum.pdf",
        checksum_sha256="abc123def4567890123456789012345678901234567890123456789012345678",
        ingestion_status="completed",
    )
    db_session.add(source)
    await db_session.flush()

    chunk1 = ContentChunk(
        source_id=source.id,
        text_content="The Schrödinger equation describes how the quantum state of a physical system changes over time.",
        token_count=18,
        chunk_index=0,
    )
    chunk2 = ContentChunk(
        source_id=source.id,
        text_content="Wave-particle duality states that every quantum entity exhibits both particle and wave properties.",
        token_count=16,
        chunk_index=1,
    )
    db_session.add_all([chunk1, chunk2])
    await db_session.commit()

    ctx_a = TenantContext(user=user_a, organization_id=org_a.id, roles=[RoleEnum.STUDENT.value])
    ctx_b = TenantContext(user=user_b, organization_id=org_b.id, roles=[RoleEnum.STUDENT.value])

    return {
        "org_a": org_a,
        "org_b": org_b,
        "user_a": user_a,
        "user_b": user_b,
        "course": course,
        "v1": v1,
        "ctx_a": ctx_a,
        "ctx_b": ctx_b,
    }


def test_supported_eight_languages():
    """Validates the 8 exact platform languages are registered with native labels and scripts."""
    langs = TranslationRegistry.get_supported_languages()
    assert len(langs) == 8

    codes = [item["code"] for item in langs]
    expected_codes = ["en", "hi", "sa", "ta", "te", "kn", "mr", "bn"]
    for ec in expected_codes:
        assert ec in codes

    # Native labels
    native_map = {item["code"]: item["native_label"] for item in langs}
    assert native_map["hi"] == "हिन्दी"
    assert native_map["sa"] == "संस्कृतम्"
    assert native_map["ta"] == "தமிழ்"
    assert native_map["te"] == "తెలుగు"
    assert native_map["kn"] == "ಕನ್ನಡ"
    assert native_map["mr"] == "मराठी"
    assert native_map["bn"] == "বাংলা"


def test_translation_lookup_and_english_fallback():
    """Tests key lookup, parameter interpolation, and robust fallback to English for missing keys."""
    # 1. Hindi lookup with interpolation
    hi_welcome = TranslationRegistry.get_text("welcome", lang="hi", name="रोहित")
    assert "पुनः स्वागत है, रोहित" in hi_welcome

    # 2. English lookup with interpolation
    en_welcome = TranslationRegistry.get_text("welcome", lang="en", name="Rohit")
    assert en_welcome == "Welcome back, Rohit"

    # 3. Sanskrit lookup
    sa_tutor = TranslationRegistry.get_text("tutor", lang="sa")
    assert sa_tutor == "एआई गुरुः"

    # 4. Tamil lookup
    ta_courses = TranslationRegistry.get_text("courses", lang="ta")
    assert ta_courses == "பாடநெறிகள்"

    # 5. Missing key in regional dictionary falls back to English
    fallback_text = TranslationRegistry.get_text("font_scale", lang="mr")
    assert fallback_text == "फॉन्ट आकार"

    # 6. Completely unknown key falls back to key itself
    unknown = TranslationRegistry.get_text("some_nonexistent_key_xyz", lang="ta")
    assert unknown == "some_nonexistent_key_xyz"


def test_decoupled_ai_prompt_language_directives():
    """Verifies that AI prompt language directives are strictly generated and decoupled from UI locale."""
    directive_hi = TranslationRegistry.get_ai_language_prompt_instruction(LanguageCode.HI.value)
    assert "SYSTEM LANGUAGE DIRECTIVE" in directive_hi
    assert "Devanagari script" in directive_hi

    directive_sa = TranslationRegistry.get_ai_language_prompt_instruction(LanguageCode.SA.value)
    assert "संस्कृतम्" in directive_sa

    directive_ta = TranslationRegistry.get_ai_language_prompt_instruction(LanguageCode.TA.value)
    assert "Tamil" in directive_ta

    directive_en = TranslationRegistry.get_ai_language_prompt_instruction(LanguageCode.EN.value)
    assert "respond in English" in directive_en


@pytest.mark.asyncio
async def test_offline_course_bundle_packaging(db_session: AsyncSession, i18n_fixture):
    """Test generating a portable offline course package with SHA-256 verification."""
    ctx_a = i18n_fixture["ctx_a"]
    course = i18n_fixture["course"]

    service = OfflineService(db_session)
    bundle = await service.package_course_bundle(ctx_a, course.id)

    assert bundle["course_id"] == course.id
    assert bundle["version_tag"] == "v1.0.0"
    assert bundle["lessons_count"] == 2
    assert len(bundle["sha256_checksum"]) == 64
    assert "Schrödinger equation" in bundle["lessons"][0]["content_text"]
    assert "Reading mode active" in bundle["offline_guidance"]


@pytest.mark.asyncio
async def test_offline_bundle_staleness_detection(db_session: AsyncSession, i18n_fixture):
    """Test detecting when a local cached bundle is outdated because a newer version was published."""
    course = i18n_fixture["course"]
    service = OfflineService(db_session)

    # 1. Local has version v1.0.0, latest published is v1.0.0 -> Not stale
    fresh = await service.check_bundle_staleness(course.id, local_version_tag="v1.0.0")
    assert fresh["is_stale"] is False
    assert fresh["status"] == "up_to_date"

    # 2. Publish Version v2.0.0 online
    v2 = CourseVersion(
        course_id=course.id,
        version_tag="v2.0.0",
        status="published",
        changelog="Added quantum entanglement module",
    )
    db_session.add(v2)
    await db_session.commit()

    # 3. Check staleness -> now local version v1.0.0 is stale!
    stale = await service.check_bundle_staleness(course.id, local_version_tag="v1.0.0")
    assert stale["is_stale"] is True
    assert stale["status"] == "stale"
    assert stale["latest_version_tag"] == "v2.0.0"


@pytest.mark.asyncio
async def test_offline_cross_tenant_denial(db_session: AsyncSession, i18n_fixture):
    """Cross-tenant isolation: caller from Org B cannot download offline bundle of Org A."""
    ctx_b = i18n_fixture["ctx_b"]
    course = i18n_fixture["course"]

    service = OfflineService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.package_course_bundle(ctx_b, course.id)
    assert exc.value.status_code == 403
    assert "Cross-tenant" in exc.value.detail


def test_user_language_preference_persistence():
    """Test getting and setting user language preference."""
    pref1 = TranslationRegistry.get_user_language("user-101")
    assert pref1 == "en"

    TranslationRegistry.set_user_language("user-101", "ta")
    pref2 = TranslationRegistry.get_user_language("user-101")
    assert pref2 == "ta"

    # Invalid code defaults to en
    TranslationRegistry.set_user_language("user-101", "invalid_xyz")
    pref3 = TranslationRegistry.get_user_language("user-101")
    assert pref3 == "en"
