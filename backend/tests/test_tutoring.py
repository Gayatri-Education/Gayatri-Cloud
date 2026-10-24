"""Comprehensive test suite for Tutor Orchestration, Pedagogical Hierarchy, and Adaptive Mastery."""

import io

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.domain.tutoring.pedagogy import (
    PedagogicalPromptBuilder,
)
from app.main import app


@pytest.fixture
async def tutor_test_client() -> AsyncClient:
    """Provides AsyncClient with an isolated in-memory test database."""
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

    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()


async def register_and_login(client: AsyncClient, email: str, full_name: str) -> tuple[dict, str]:
    """Helper to register and login a user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": full_name},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = res.json()["access_token"]
    user_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return user_res.json(), token


# --- 1. Unit Tests: Pedagogy and Instruction Cascade ---


def test_pedagogical_prompt_builder():
    """Verify system prompt incorporates pedagogy mode, course title, and XML chunk wrappers."""
    prompt = PedagogicalPromptBuilder.build_system_prompt(
        tutoring_mode="socratic",
        course_title="Quantum Computing 101",
        teacher_instructions=[],
        retrieved_chunks=[],
    )
    assert "Socratic Method" in prompt
    assert "NEVER reveal the final answer directly" in prompt
    assert "Quantum Computing 101" in prompt


# --- 2. End-to-End Tutoring Session and Mastery Integration Tests ---


@pytest.mark.asyncio
async def test_tutor_orchestration_and_deterministic_mastery(tutor_test_client: AsyncClient):
    """Verify session creation, multi-turn dialogue, teacher instructions, and deterministic mastery."""
    # 1. Setup Admin, Teacher, Student & Organization
    admin_user, admin_token = await register_and_login(
        tutor_test_client, "admin.edu@example.internal", "Admin Edu"
    )
    org_res = await tutor_test_client.post(
        "/api/v1/organizations",
        json={"name": "Vedic Science Academy", "slug": "vedic-acad"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    org_id = org_res.json()["id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org_id}

    # Register and invite student
    student_user, student_token = await register_and_login(
        tutor_test_client, "student.one@example.internal", "Student One"
    )
    inv_res = await tutor_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "student.one@example.internal", "proposed_role": "STUDENT"},
        headers=admin_headers,
    )
    await tutor_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": inv_res.json()["token"]},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    student_headers = {"Authorization": f"Bearer {student_token}", "X-Organization-ID": org_id}

    # 2. Create Course, Publish v1.0.0, and Deploy Offering
    course_res = await tutor_test_client.post(
        "/api/v1/courses",
        json={"code": "MATH101", "title": "Discrete Mathematics"},
        headers=admin_headers,
    )
    course_id = course_res.json()["id"]

    v_res = await tutor_test_client.get(
        f"/api/v1/courses/{course_id}/versions", headers=admin_headers
    )
    version_id = v_res.json()[0]["id"]

    # Upload syllabus material
    doc_content = (
        b"# Propositional Logic\nTruth tables show truth values for compound propositions."
    )
    files = {"file": ("logic.md", io.BytesIO(doc_content), "text/markdown")}
    await tutor_test_client.post(
        f"/api/v1/courses/{course_id}/versions/{version_id}/sources",
        files=files,
        headers=admin_headers,
    )
    await tutor_test_client.post(
        f"/api/v1/rag/courses/{course_id}/versions/{version_id}/ingest",
        headers=admin_headers,
    )

    # Publish version
    await tutor_test_client.post(
        f"/api/v1/courses/{course_id}/versions/{version_id}/publish",
        headers=admin_headers,
    )

    # Create Offering
    offering_res = await tutor_test_client.post(
        "/api/v1/courses/offerings",
        json={"course_version_id": version_id, "term": "Fall 2026"},
        headers=admin_headers,
    )
    offering_id = offering_res.json()["id"]

    # Enroll Student
    await tutor_test_client.post(
        f"/api/v1/courses/offerings/{offering_id}/enroll",
        json={"student_id": student_user["id"]},
        headers=admin_headers,
    )

    # 3. Create Teacher Directive
    inst_res = await tutor_test_client.post(
        "/api/v1/tutoring/instructions",
        json={
            "course_id": course_id,
            "tier": "COURSE",
            "priority": 4,
            "directive_text": "Emphasize truth table construction before truth values.",
        },
        headers=admin_headers,
    )
    assert inst_res.status_code == 201

    # 4. Start Tutoring Session
    session_res = await tutor_test_client.post(
        "/api/v1/tutoring/sessions",
        json={"offering_id": offering_id, "tutoring_mode": "socratic"},
        headers=student_headers,
    )
    assert session_res.status_code == 201
    session_data = session_res.json()
    session_id = session_data["id"]
    assert session_data["tutoring_mode"] == "socratic"

    # 5. Process Dialogue Turn 1 (with validated evidence update)
    turn1_res = await tutor_test_client.post(
        f"/api/v1/tutoring/sessions/{session_id}/turns",
        json={
            "message_text": "What is a truth table in propositional logic?",
            "concept_id": "prop_logic",
            "is_validated_correct": True,
        },
        headers=student_headers,
    )
    assert turn1_res.status_code == 200
    turn1_data = turn1_res.json()
    assert turn1_data["user_turn"]["turn_number"] == 1
    assert turn1_data["assistant_turn"]["turn_number"] == 2
    assert turn1_data["mastery_state"] is not None
    assert turn1_data["mastery_state"]["mastery_score"] > 0.0

    # 6. Process Dialogue Turn 2 (with diagnosed misconception)
    turn2_res = await tutor_test_client.post(
        f"/api/v1/tutoring/sessions/{session_id}/turns",
        json={
            "message_text": "Does an implication become true only when both antecedent and consequent are true?",
            "concept_id": "prop_logic",
            "diagnosed_misconception": "Confusing logical conditional with logical biconditional equivalence.",
            "is_validated_correct": False,
        },
        headers=student_headers,
    )
    assert turn2_res.status_code == 200
    turn2_data = turn2_res.json()
    assert turn2_data["user_turn"]["turn_number"] == 3
    assert turn2_data["assistant_turn"]["turn_number"] == 4

    # 7. Check Student Mastery Vector
    mastery_res = await tutor_test_client.get(
        f"/api/v1/tutoring/sessions/{session_id}/mastery",
        headers=student_headers,
    )
    assert mastery_res.status_code == 200
    states = mastery_res.json()
    assert len(states) == 1
    assert states[0]["concept_id"] == "prop_logic"
    assert states[0]["review_count"] == 2


@pytest.mark.asyncio
async def test_cross_student_session_isolation(tutor_test_client: AsyncClient):
    """Verify Student B cannot access or send turns to Student A's tutoring session."""
    # Org
    admin_user, admin_token = await register_and_login(
        tutor_test_client, "admin.inst@example.internal", "Admin Inst"
    )
    org_res = await tutor_test_client.post(
        "/api/v1/organizations",
        json={"name": "Alpha Institute", "slug": "alpha-inst"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    org_id = org_res.json()["id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org_id}

    # Student A
    student_a, token_a = await register_and_login(
        tutor_test_client, "student.a@example.internal", "Student A"
    )
    inv_a = await tutor_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "student.a@example.internal", "proposed_role": "STUDENT"},
        headers=admin_headers,
    )
    await tutor_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": inv_a.json()["token"]},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_id}

    # Student B
    student_b, token_b = await register_and_login(
        tutor_test_client, "student.b@example.internal", "Student B"
    )
    inv_b = await tutor_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "student.b@example.internal", "proposed_role": "STUDENT"},
        headers=admin_headers,
    )
    await tutor_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": inv_b.json()["token"]},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_id}

    # Course & Offering
    course_res = await tutor_test_client.post(
        "/api/v1/courses",
        json={"code": "BIO101", "title": "Cell Biology"},
        headers=admin_headers,
    )
    c_id = course_res.json()["id"]
    v_id = (
        await tutor_test_client.get(f"/api/v1/courses/{c_id}/versions", headers=admin_headers)
    ).json()[0]["id"]
    await tutor_test_client.post(
        f"/api/v1/courses/{c_id}/versions/{v_id}/publish", headers=admin_headers
    )

    offering = await tutor_test_client.post(
        "/api/v1/courses/offerings",
        json={"course_version_id": v_id, "term": "Spring 2026"},
        headers=admin_headers,
    )
    offering_id = offering.json()["id"]

    # Enroll Student A
    await tutor_test_client.post(
        f"/api/v1/courses/offerings/{offering_id}/enroll",
        json={"student_id": student_a["id"]},
        headers=admin_headers,
    )

    # Student A starts session
    session_res = await tutor_test_client.post(
        "/api/v1/tutoring/sessions",
        json={"offering_id": offering_id, "tutoring_mode": "socratic"},
        headers=headers_a,
    )
    session_id = session_res.json()["id"]

    # Student B attempts to access Student A's session (MUST BE 403)
    attack_res = await tutor_test_client.get(
        f"/api/v1/tutoring/sessions/{session_id}",
        headers=headers_b,
    )
    assert attack_res.status_code == 403

    # Student B attempts to post turn into Student A's session (MUST BE 403)
    turn_attack = await tutor_test_client.post(
        f"/api/v1/tutoring/sessions/{session_id}/turns",
        json={"message_text": "Unauthorized intrusion."},
        headers=headers_b,
    )
    assert turn_attack.status_code == 403
