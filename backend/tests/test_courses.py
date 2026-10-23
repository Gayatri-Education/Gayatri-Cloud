"""Comprehensive test suite for file storage abstraction and course lifecycle."""

import io

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.storage import (
    LocalStorageAdapter,
    validate_file_content,
)
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
async def course_test_client(tmp_path) -> AsyncClient:
    """Provides AsyncClient with in-memory SQLite database and isolated storage directory."""
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


# --- 1. Storage Adapter Unit Tests ---


def test_local_storage_adapter(tmp_path):
    """Verify local storage adapter upload, download, exists, and deletion."""
    storage = LocalStorageAdapter(base_directory=str(tmp_path))
    test_data = b"Hello, Gayatri Cloud Storage!"
    path = "tenant1/courses/c1/v1/test.txt"

    uri = storage.upload_file(test_data, path, "text/plain")
    assert uri.startswith("local://")
    assert storage.file_exists(path) is True

    downloaded = storage.download_file(path)
    assert downloaded == test_data

    # Presigned URL check
    presigned = storage.generate_presigned_download_url(path)
    assert "/api/v1/courses/sources/files/" in presigned

    # Delete
    deleted = storage.delete_file(path)
    assert deleted is True
    assert storage.file_exists(path) is False


def test_local_storage_path_traversal_guard(tmp_path):
    """Verify that path traversal attempts are strictly caught and rejected."""
    storage = LocalStorageAdapter(base_directory=str(tmp_path))

    with pytest.raises(ValueError, match="Path traversal attempt detected"):
        storage.upload_file(b"malicious", "../../../etc/passwd", "text/plain")

    with pytest.raises(ValueError, match="Path traversal attempt detected"):
        storage.download_file("../../windows/system32/calc.exe")


# --- 2. Content Validation & Sniffing Tests ---


def test_validate_file_content_pdf():
    """Verify valid PDF magic bytes vs MIME spoofing."""
    valid_pdf = b"%PDF-1.4\n%Fake PDF binary content"
    validate_file_content(valid_pdf, "syllabus.pdf", "application/pdf")

    # Spoofed PDF (executable/text pretending to be PDF)
    fake_pdf = b"MZ\x90\x00Fake executable content"
    with pytest.raises(ValueError, match="Binary signature does not match"):
        validate_file_content(fake_pdf, "syllabus.pdf", "application/pdf")


def test_validate_file_content_text_and_null_bytes():
    """Verify UTF-8 text validation and null-byte rejection."""
    valid_text = b"Simple course text content"
    validate_file_content(valid_text, "notes.txt", "text/plain")

    # Text containing null bytes
    binary_text = b"Text with null byte \x00 invalid"
    with pytest.raises(ValueError, match="Binary executable/null characters detected"):
        validate_file_content(binary_text, "notes.txt", "text/plain")


def test_validate_file_content_oversized():
    """Verify rejection of files exceeding maximum limit."""
    with pytest.raises(ValueError, match="exceeds maximum limit"):
        validate_file_content(b"x" * (51 * 1024 * 1024), "huge.pdf", "application/pdf")


# --- 3. Course and Version Lifecycle Integration Tests ---


@pytest.mark.asyncio
async def test_course_creation_and_version_lifecycle(course_test_client: AsyncClient):
    """Verify course creation, initial draft version, adding sources, and immutability after publish."""
    # 1. Setup Admin & Organization
    admin_user, admin_token = await register_and_login(
        course_test_client, "prof.admin@example.internal", "Professor Admin"
    )
    auth_header = {"Authorization": f"Bearer {admin_token}"}

    org_res = await course_test_client.post(
        "/api/v1/organizations",
        json={"name": "Vedic Science Academy", "slug": "vedic-sci"},
        headers=auth_header,
    )
    org_id = org_res.json()["id"]
    headers = {"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org_id}

    # 2. Create Course
    course_res = await course_test_client.post(
        "/api/v1/courses",
        json={
            "code": "VED101",
            "title": "Introduction to Vedic Computation",
            "description": "Foundations of ancient algorithms",
        },
        headers=headers,
    )
    assert course_res.status_code == 201
    course_data = course_res.json()
    assert course_data["code"] == "VED101"
    course_id = course_data["id"]

    # 3. Verify initial version v1.0.0 exists in draft state
    v_res = await course_test_client.get(f"/api/v1/courses/{course_id}/versions", headers=headers)
    assert v_res.status_code == 200
    versions = v_res.json()
    assert len(versions) == 1
    assert versions[0]["version_tag"] == "v1.0.0"
    assert versions[0]["status"] == "draft"
    v1_id = versions[0]["id"]

    # 4. Upload curriculum PDF source to draft version
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Vedic Maths Chapter 1) >>\nendobj"
    files = {"file": ("chapter1.pdf", io.BytesIO(pdf_content), "application/pdf")}
    upload_res = await course_test_client.post(
        f"/api/v1/courses/{course_id}/versions/{v1_id}/sources",
        files=files,
        headers=headers,
    )
    assert upload_res.status_code == 201
    source_data = upload_res.json()
    assert source_data["filename"] == "chapter1.pdf"
    assert source_data["file_size_bytes"] == len(pdf_content)
    assert source_data["ingestion_status"] == "pending"
    source_id = source_data["id"]

    # 5. Download URL generation
    dl_res = await course_test_client.get(
        f"/api/v1/courses/{course_id}/versions/{v1_id}/sources/{source_id}/download",
        headers=headers,
    )
    assert dl_res.status_code == 200
    assert "download_url" in dl_res.json()

    # 6. Publish Version v1.0.0
    pub_res = await course_test_client.post(
        f"/api/v1/courses/{course_id}/versions/{v1_id}/publish",
        headers=headers,
    )
    assert pub_res.status_code == 200
    published_version = pub_res.json()
    assert published_version["status"] == "published"
    assert published_version["published_at"] is not None

    # 7. Invariant Verification: Adding source to published version MUST fail (400)
    files2 = {"file": ("chapter2.pdf", io.BytesIO(pdf_content), "application/pdf")}
    upload_fail_res = await course_test_client.post(
        f"/api/v1/courses/{course_id}/versions/{v1_id}/sources",
        files=files2,
        headers=headers,
    )
    assert upload_fail_res.status_code == 400
    assert "immutable" in upload_fail_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_offering_deployment_and_student_enrollment(course_test_client: AsyncClient):
    """Verify offering creation requires published version and verifies student enrollment."""
    # 1. Setup Admin & Organization
    admin_user, admin_token = await register_and_login(
        course_test_client, "admin.dept@example.internal", "Dept Admin"
    )
    org_res = await course_test_client.post(
        "/api/v1/organizations",
        json={"name": "Science Faculty", "slug": "sci-fac"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    org_id = org_res.json()["id"]
    headers = {"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org_id}

    # 2. Setup Student
    student_user, student_token = await register_and_login(
        course_test_client, "student.learner@example.internal", "Student Learner"
    )
    # Invite and accept student into organization
    inv_res = await course_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "student.learner@example.internal", "proposed_role": "STUDENT"},
        headers=headers,
    )
    inv_token = inv_res.json()["token"]
    await course_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": inv_token},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # 3. Create Course
    c_res = await course_test_client.post(
        "/api/v1/courses",
        json={"code": "MATH201", "title": "Calculus II"},
        headers=headers,
    )
    course_id = c_res.json()["id"]

    # 4. Get draft version
    v_res = await course_test_client.get(f"/api/v1/courses/{course_id}/versions", headers=headers)
    v1_id = v_res.json()[0]["id"]

    # 5. Attempt to deploy offering with DRAFT version (MUST FAIL with 400)
    fail_offering = await course_test_client.post(
        "/api/v1/courses/offerings",
        json={"course_version_id": v1_id, "term": "Spring 2026"},
        headers=headers,
    )
    assert fail_offering.status_code == 400
    assert "must be 'published'" in fail_offering.json()["detail"]

    # 6. Publish version
    await course_test_client.post(
        f"/api/v1/courses/{course_id}/versions/{v1_id}/publish",
        headers=headers,
    )

    # 7. Deploy offering now (MUST SUCCEED)
    offering_res = await course_test_client.post(
        "/api/v1/courses/offerings",
        json={"course_version_id": v1_id, "term": "Spring 2026"},
        headers=headers,
    )
    assert offering_res.status_code == 201
    offering_id = offering_res.json()["id"]

    # 8. Enroll student
    enroll_res = await course_test_client.post(
        f"/api/v1/courses/offerings/{offering_id}/enroll",
        json={"student_id": student_user["id"]},
        headers=headers,
    )
    assert enroll_res.status_code == 201
    enroll_data = enroll_res.json()
    assert enroll_data["status"] == "enrolled"

    # 9. Duplicate enrollment check (MUST FAIL with 409)
    dup_enroll = await course_test_client.post(
        f"/api/v1/courses/offerings/{offering_id}/enroll",
        json={"student_id": student_user["id"]},
        headers=headers,
    )
    assert dup_enroll.status_code == 409


@pytest.mark.asyncio
async def test_cross_tenant_course_and_source_isolation(course_test_client: AsyncClient):
    """Verify tenant isolation: Org B cannot access Org A's course or download Org A's sources."""
    # Org A
    user_a, token_a = await register_and_login(
        course_test_client, "teacher.a@example.internal", "Teacher A"
    )
    org_a_res = await course_test_client.post(
        "/api/v1/organizations",
        json={"name": "Org Alpha", "slug": "org-alpha"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    org_a_id = org_a_res.json()["id"]
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id}

    course_a = await course_test_client.post(
        "/api/v1/courses",
        json={"code": "PHY101", "title": "Physics I"},
        headers=headers_a,
    )
    course_a_id = course_a.json()["id"]

    v_a = await course_test_client.get(f"/api/v1/courses/{course_a_id}/versions", headers=headers_a)
    v_a_id = v_a.json()[0]["id"]

    pdf_content = b"%PDF-1.4\nAlpha Confidential Physics Material"
    files = {"file": ("alpha_physics.pdf", io.BytesIO(pdf_content), "application/pdf")}
    source_a = await course_test_client.post(
        f"/api/v1/courses/{course_a_id}/versions/{v_a_id}/sources",
        files=files,
        headers=headers_a,
    )
    source_a_id = source_a.json()["id"]

    # Org B
    user_b, token_b = await register_and_login(
        course_test_client, "teacher.b@example.internal", "Teacher B"
    )
    org_b_res = await course_test_client.post(
        "/api/v1/organizations",
        json={"name": "Org Beta", "slug": "org-beta"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    org_b_id = org_b_res.json()["id"]
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id}

    # Org B attempts to access Org A's course (MUST BE 403)
    leak_course = await course_test_client.get(
        f"/api/v1/courses/{course_a_id}",
        headers=headers_b,
    )
    assert leak_course.status_code == 403

    # Org B attempts to download Org A's source (MUST BE 403)
    leak_download = await course_test_client.get(
        f"/api/v1/courses/{course_a_id}/versions/{v_a_id}/sources/{source_a_id}/download",
        headers=headers_b,
    )
    assert leak_download.status_code == 403
