"""Comprehensive test suite for AI Gateway, Credential Vault, and Model Discovery."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import (
    compute_key_fingerprint,
    decrypt_credential,
    encrypt_credential,
    mask_credential,
)
from app.db.base import Base
from app.db.session import get_db
from app.domain.ai.adapters import (
    AIGenerationRequest,
    AnthropicProviderAdapter,
    CustomEndpointAdapter,
    GeminiProviderAdapter,
    MockAIProviderAdapter,
    OpenAIProviderAdapter,
    OpenRouterAdapter,
)
from app.main import app


@pytest.fixture
async def ai_test_client() -> AsyncClient:
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


# --- 1. Unit Tests: AES-256-GCM Credential Vault ---


def test_credential_encryption_and_decryption():
    """Verify AES-256-GCM symmetric encryption roundtrip and non-deterministic nonces."""
    secret = "sk-live-1234567890abcdefghijklmnopqrstuvwxyz"
    ct1 = encrypt_credential(secret)
    ct2 = encrypt_credential(secret)

    # Different nonces produce different ciphertexts
    assert ct1 != ct2
    assert "$" in ct1

    # Accurate decryption
    decrypted = decrypt_credential(ct1)
    assert decrypted == secret


def test_credential_decryption_tamper_detection():
    """Verify corrupted ciphertext raises ValueError."""
    with pytest.raises(ValueError, match="Failed to decrypt credential"):
        decrypt_credential("badnonce$corruptedciphertext12345")


def test_mask_credential():
    """Verify secret masking exposes only prefix and suffix."""
    secret = "sk-proj-9876543210abcdefg"
    masked = mask_credential(secret)
    assert masked == "sk-...defg"
    assert "987654" not in masked


def test_key_fingerprint():
    """Verify SHA-256 key fingerprinting."""
    secret = "sk-secret-key-1"
    fp = compute_key_fingerprint(secret)
    assert len(fp) == 64
    assert fp == compute_key_fingerprint(secret)


# --- 2. Unit Tests: Provider Adapters ---


@pytest.mark.asyncio
async def test_provider_adapters_contract():
    """Verify all provider adapters adhere to standard catalog and generation interface."""
    adapters = [
        MockAIProviderAdapter(),
        OpenAIProviderAdapter(api_key="mock-key"),
        AnthropicProviderAdapter(api_key="mock-key"),
        GeminiProviderAdapter(api_key="mock-key"),
        OpenRouterAdapter(api_key="mock-key"),
        CustomEndpointAdapter(custom_url="http://localhost:8000/v1"),
    ]

    for adapter in adapters:
        models = await adapter.list_models()
        assert len(models) >= 1
        assert models[0].context_window_tokens > 0

        res = await adapter.generate(AIGenerationRequest(prompt="Explain Pythagorean Theorem."))
        assert res.content
        assert res.provider_type == adapter.provider_type
        assert res.prompt_tokens > 0


# --- 3. Integration Tests: AI Gateway and Credential Management ---


@pytest.mark.asyncio
async def test_create_and_list_provider_connections(ai_test_client: AsyncClient):
    """Verify encrypted credential registration, masked preview, and zero secret leakage."""
    user, token = await register_and_login(ai_test_client, "ai.admin@example.internal", "AI Admin")
    auth_header = {"Authorization": f"Bearer {token}"}

    org_res = await ai_test_client.post(
        "/api/v1/organizations",
        json={"name": "AI Institute", "slug": "ai-inst"},
        headers=auth_header,
    )
    org_id = org_res.json()["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    raw_key = "sk-live-super-secret-organization-api-key-99"

    # 1. Register Org-level Credential
    conn_res = await ai_test_client.post(
        "/api/v1/ai/connections",
        json={
            "provider_type": "openai",
            "api_key": raw_key,
            "is_organization_level": True,
        },
        headers=headers,
    )
    assert conn_res.status_code == 201
    conn_data = conn_res.json()
    assert conn_data["provider_type"] == "openai"
    assert conn_data["key_mask"] == "sk-...y-99"
    # CRITICAL: Raw key must never be returned
    assert raw_key not in str(conn_data)
    conn_id = conn_data["id"]

    # 2. List Connections
    list_res = await ai_test_client.get("/api/v1/ai/connections", headers=headers)
    assert list_res.status_code == 200
    connections = list_res.json()
    assert len(connections) == 1
    assert connections[0]["key_mask"] == "sk-...y-99"
    assert raw_key not in str(connections)

    # 3. Delete / Deactivate Connection
    del_res = await ai_test_client.delete(f"/api/v1/ai/connections/{conn_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify no active connections
    list_res2 = await ai_test_client.get("/api/v1/ai/connections", headers=headers)
    assert len(list_res2.json()) == 0


@pytest.mark.asyncio
async def test_ai_gateway_fallback_on_rate_limit(ai_test_client: AsyncClient):
    """Verify that provider rate limits automatically trigger fallback model and audit usage."""
    user, token = await register_and_login(
        ai_test_client, "learner.ai@example.internal", "Learner AI"
    )
    org_res = await ai_test_client.post(
        "/api/v1/organizations",
        json={"name": "Tech Academy", "slug": "tech-acad"},
        headers={"Authorization": f"Bearer {token}"},
    )
    org_id = org_res.json()["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # Normal prompt
    normal_res = await ai_test_client.post(
        "/api/v1/ai/generate",
        json={"prompt": "Explain quadratic equations."},
        headers=headers,
    )
    assert normal_res.status_code == 200
    res_data = normal_res.json()
    assert res_data["is_fallback"] is False
    assert res_data["model_id"] == "mock-tutor-standard"

    # Rate-limited prompt triggers simulated 429 and automatic fallback
    fallback_res = await ai_test_client.post(
        "/api/v1/ai/generate",
        json={"prompt": "SIMULATE_RATE_LIMIT please explain calculus."},
        headers=headers,
    )
    assert fallback_res.status_code == 200
    fb_data = fallback_res.json()
    assert fb_data["is_fallback"] is True
    assert "rate limit exceeded" in fb_data["fallback_reason"].lower()
    assert fb_data["model_id"] == "mock-fast-evaluator"


@pytest.mark.asyncio
async def test_ai_gateway_sse_streaming(ai_test_client: AsyncClient):
    """Verify Server-Sent Events (SSE) streaming token output."""
    user, token = await register_and_login(ai_test_client, "streamer@example.internal", "Streamer")
    org_res = await ai_test_client.post(
        "/api/v1/organizations",
        json={"name": "Stream Org", "slug": "stream-org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    org_id = org_res.json()["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    res = await ai_test_client.post(
        "/api/v1/ai/generate/stream",
        json={"prompt": "Stream tutorial."},
        headers=headers,
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    text_content = res.text
    assert "data: " in text_content
    assert "[DONE]" in text_content


@pytest.mark.asyncio
async def test_cross_tenant_credential_isolation(ai_test_client: AsyncClient):
    """Verify Org B cannot view or delete Org A's credentials."""
    # Org A
    user_a, token_a = await register_and_login(
        ai_test_client, "admin.a@example.internal", "Admin A"
    )
    org_a = await ai_test_client.post(
        "/api/v1/organizations",
        json={"name": "Org Alpha", "slug": "org-alpha"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    org_a_id = org_a.json()["id"]
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id}

    conn_a = await ai_test_client.post(
        "/api/v1/ai/connections",
        json={
            "provider_type": "anthropic",
            "api_key": "sk-ant-alpha-secret-key",
            "is_organization_level": True,
        },
        headers=headers_a,
    )
    conn_a_id = conn_a.json()["id"]

    # Org B
    user_b, token_b = await register_and_login(
        ai_test_client, "admin.b@example.internal", "Admin B"
    )
    org_b = await ai_test_client.post(
        "/api/v1/organizations",
        json={"name": "Org Beta", "slug": "org-beta"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    org_b_id = org_b.json()["id"]
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id}

    # Org B lists connections (should NOT contain Org A's credential)
    list_b = await ai_test_client.get("/api/v1/ai/connections", headers=headers_b)
    assert len(list_b.json()) == 0

    # Org B attempts to delete Org A's credential (MUST BE 403)
    del_attack = await ai_test_client.delete(
        f"/api/v1/ai/connections/{conn_a_id}", headers=headers_b
    )
    assert del_attack.status_code == 403
