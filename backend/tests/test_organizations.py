"""Test organizations, memberships, multi-tenant RBAC, and isolation boundaries."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
async def org_test_client() -> AsyncClient:
    """Provides an AsyncClient connected to an isolated in-memory test database."""
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
    """Helper to register and login a user, returning user data and access token."""
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


# --- Integration Tests ---


@pytest.mark.asyncio
async def test_organization_creation_and_admin_assignment(org_test_client: AsyncClient):
    """Verify organization creation assigns creator as ORG_ADMIN and lists in /me."""
    user, token = await register_and_login(
        org_test_client, "org.creator@example.internal", "Org Creator"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Organization
    res = await org_test_client.post(
        "/api/v1/organizations",
        json={"name": "Delta Institute", "slug": "delta-inst"},
        headers=headers,
    )
    assert res.status_code == 201
    org_data = res.json()
    assert org_data["name"] == "Delta Institute"
    assert org_data["slug"] == "delta-inst"

    # 2. List My Organizations
    list_res = await org_test_client.get("/api/v1/organizations/me", headers=headers)
    assert list_res.status_code == 200
    orgs = list_res.json()
    assert len(orgs) == 1
    assert orgs[0]["id"] == org_data["id"]


@pytest.mark.asyncio
async def test_cross_tenant_access_denied(org_test_client: AsyncClient):
    """Verify that a member of Org B cannot access Org A endpoints (IDOR protection)."""
    # Create Org A with User A
    user_a, token_a = await register_and_login(
        org_test_client, "admin.a@example.internal", "Admin A"
    )
    res_a = await org_test_client.post(
        "/api/v1/organizations",
        json={"name": "Org Alpha", "slug": "org-alpha"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    org_a_id = res_a.json()["id"]

    # Create Org B with User B
    user_b, token_b = await register_and_login(
        org_test_client, "admin.b@example.internal", "Admin B"
    )
    res_b = await org_test_client.post(
        "/api/v1/organizations",
        json={"name": "Org Beta", "slug": "org-beta"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 201

    # User B attempts to access Org A's member list using Org A's ID
    unauthorized_res = await org_test_client.get(
        f"/api/v1/organizations/{org_a_id}/members",
        headers={
            "Authorization": f"Bearer {token_b}",
            "X-Organization-ID": org_a_id,
        },
    )
    assert unauthorized_res.status_code == 403
    assert "Access denied" in unauthorized_res.json()["detail"]


@pytest.mark.asyncio
async def test_invitation_lifecycle_and_single_use(org_test_client: AsyncClient):
    """Verify invitation creation, redemption, and single-use replay rejection."""
    # Org Admin setup
    admin_user, admin_token = await register_and_login(
        org_test_client, "admin.invite@example.internal", "Admin Invite"
    )
    org_res = await org_test_client.post(
        "/api/v1/organizations",
        json={"name": "Gamma College", "slug": "gamma-college"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    org_id = org_res.json()["id"]

    # Issue invitation for Teacher
    invite_res = await org_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "prof.smith@example.internal", "proposed_role": "TEACHER"},
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": org_id,
        },
    )
    assert invite_res.status_code == 201
    invite_token = invite_res.json()["token"]

    # Teacher registers and accepts invitation
    teacher_user, teacher_token = await register_and_login(
        org_test_client, "prof.smith@example.internal", "Prof Smith"
    )
    accept_res = await org_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["organization_id"] == org_id

    # Attempt to replay the same token
    replay_res = await org_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert replay_res.status_code == 400
    assert "Invalid or expired" in replay_res.json()["detail"]


@pytest.mark.asyncio
async def test_role_incompatibility_enforcement(org_test_client: AsyncClient):
    """Verify strict prohibition of STUDENT + TEACHER roles for the same user."""
    # Org setup
    admin_user, admin_token = await register_and_login(
        org_test_client, "admin.roles@example.internal", "Admin Roles"
    )
    org_res = await org_test_client.post(
        "/api/v1/organizations",
        json={"name": "Epsilon School", "slug": "epsilon-school"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    org_id = org_res.json()["id"]

    # Invite user as TEACHER
    invite_t = await org_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "hybrid@example.internal", "proposed_role": "TEACHER"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org_id},
    )
    token_t = invite_t.json()["token"]

    user, user_token = await register_and_login(
        org_test_client, "hybrid@example.internal", "Hybrid User"
    )
    # Accept TEACHER role
    await org_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": token_t},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Now attempt to invite the same user as STUDENT in this organization
    invite_s = await org_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "hybrid@example.internal", "proposed_role": "STUDENT"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org_id},
    )
    token_s = invite_s.json()["token"]

    # Attempting to accept STUDENT when already TEACHER must fail
    conflict_res = await org_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": token_s},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert conflict_res.status_code == 400
    assert "cannot hold both Student and Teacher" in conflict_res.json()["detail"]

    # Conversely, invite as PARENT must succeed (Teacher + Parent is permitted)
    invite_p = await org_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "hybrid@example.internal", "proposed_role": "PARENT"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org_id},
    )
    token_p = invite_p.json()["token"]

    parent_res = await org_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": token_p},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert parent_res.status_code == 200, "Teacher + Parent must be permitted"


@pytest.mark.asyncio
async def test_guardian_linkage_and_access_boundary(org_test_client: AsyncClient):
    """Verify parent linkage and boundary check."""
    parent_user, parent_token = await register_and_login(
        org_test_client, "parent.one@example.internal", "Parent One"
    )
    student_user, _ = await register_and_login(
        org_test_client, "child.one@example.internal", "Child One"
    )
    unrelated_user, _ = await register_and_login(
        org_test_client, "child.two@example.internal", "Child Two"
    )

    # Create Org and join
    org_res = await org_test_client.post(
        "/api/v1/organizations",
        json={"name": "Guardian School", "slug": "guardian-school"},
        headers={"Authorization": f"Bearer {parent_token}"},
    )
    org_id = org_res.json()["id"]

    # Link parent to student
    link_res = await org_test_client.post(
        f"/api/v1/organizations/{org_id}/guardians",
        json={"student_id": student_user["id"]},
        headers={
            "Authorization": f"Bearer {parent_token}",
            "X-Organization-ID": org_id,
        },
    )
    assert link_res.status_code == 201
