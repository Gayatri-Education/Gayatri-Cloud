"""Test authentication, password security, JWT lifecycle, and auth endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import (
    create_access_token,
    decode_jwt_token,
    hash_password,
    verify_password,
)
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# --- Fixtures ---


@pytest.fixture
async def auth_test_client() -> AsyncClient:
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


# --- Unit Tests ---


def test_password_hashing_and_verification():
    """Verify password hashing generates unique salts and verifies correctly."""
    pw = "SuperSecurePassword123!"
    h1 = hash_password(pw)
    h2 = hash_password(pw)

    assert h1 != h2, "Salts must be random, producing different hashes for the same password"
    assert verify_password(pw, h1) is True
    assert verify_password(pw, h2) is True
    assert verify_password("WrongPassword!", h1) is False


def test_jwt_token_claims_and_decoding():
    """Verify JWT claims generation and decoding."""
    token = create_access_token("user-123", "alice@example.internal", is_super_admin=False)
    payload = decode_jwt_token(token)

    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["email"] == "alice@example.internal"
    assert payload["type"] == "access"
    assert "exp" in payload

    # Tampered token
    tampered = token[:-4] + "abcd"
    assert decode_jwt_token(tampered) is None


# --- Integration Tests ---


@pytest.mark.asyncio
async def test_user_registration_flow(auth_test_client: AsyncClient):
    """Verify registration creates user and rejects duplicate email."""
    payload = {
        "email": "learner.one@example.internal",
        "password": "Password1234!",
        "full_name": "Learner One",
    }
    res = await auth_test_client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "learner.one@example.internal"
    assert data["full_name"] == "Learner One"
    assert "id" in data
    assert "password" not in data

    # Attempt duplicate registration
    res_dup = await auth_test_client.post("/api/v1/auth/register", json=payload)
    assert res_dup.status_code == 409
    assert "already exists" in res_dup.json()["detail"]


@pytest.mark.asyncio
async def test_user_login_and_enumeration_resistance(auth_test_client: AsyncClient):
    """Verify login success and check that unknown email and bad password return identical 401."""
    # 1. Register user
    reg_payload = {
        "email": "learner.two@example.internal",
        "password": "CorrectPassword123!",
        "full_name": "Learner Two",
    }
    await auth_test_client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Login with correct password
    login_res = await auth_test_client.post(
        "/api/v1/auth/login",
        json={"email": "learner.two@example.internal", "password": "CorrectPassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Login with wrong password
    bad_pw_res = await auth_test_client.post(
        "/api/v1/auth/login",
        json={"email": "learner.two@example.internal", "password": "WrongPassword!"},
    )
    assert bad_pw_res.status_code == 401

    # 4. Login with unknown email
    unknown_email_res = await auth_test_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.internal", "password": "AnyPassword!"},
    )
    assert unknown_email_res.status_code == 401

    # User enumeration resistance check
    assert bad_pw_res.json()["detail"] == unknown_email_res.json()["detail"]


@pytest.mark.asyncio
async def test_protected_profile_endpoint(auth_test_client: AsyncClient):
    """Verify /api/v1/auth/me enforces authorization header."""
    # Register & Login
    await auth_test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile.user@example.internal",
            "password": "Password123!",
            "full_name": "Profile User",
        },
    )
    login_res = await auth_test_client.post(
        "/api/v1/auth/login",
        json={"email": "profile.user@example.internal", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]

    # Request without auth
    no_auth_res = await auth_test_client.get("/api/v1/auth/me")
    assert no_auth_res.status_code == 401

    # Request with valid bearer token
    auth_res = await auth_test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_res.status_code == 200
    user_info = auth_res.json()
    assert user_info["email"] == "profile.user@example.internal"
    assert user_info["full_name"] == "Profile User"


@pytest.mark.asyncio
async def test_session_refresh_and_token_rotation(auth_test_client: AsyncClient):
    """Verify refresh token rotation and replay prevention."""
    await auth_test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh.user@example.internal",
            "password": "Password123!",
            "full_name": "Refresh User",
        },
    )
    login_res = await auth_test_client.post(
        "/api/v1/auth/login",
        json={"email": "refresh.user@example.internal", "password": "Password123!"},
    )
    old_refresh_token = login_res.json()["refresh_token"]

    # 1. Rotate refresh token
    rotate_res = await auth_test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert rotate_res.status_code == 200
    new_tokens = rotate_res.json()
    new_refresh_token = new_tokens["refresh_token"]
    assert new_refresh_token != old_refresh_token

    # 2. Attempt to replay old refresh token (must be rejected)
    replay_res = await auth_test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert replay_res.status_code == 401
    assert "revoked" in replay_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout_revokes_session(auth_test_client: AsyncClient):
    """Verify logout invalidates refresh token."""
    await auth_test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout.user@example.internal",
            "password": "Password123!",
            "full_name": "Logout User",
        },
    )
    login_res = await auth_test_client.post(
        "/api/v1/auth/login",
        json={"email": "logout.user@example.internal", "password": "Password123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # Logout
    logout_res = await auth_test_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200

    # Attempting to refresh with revoked token fails
    refresh_attempt = await auth_test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_attempt.status_code == 401
