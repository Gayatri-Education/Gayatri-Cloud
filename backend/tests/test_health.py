"""Test health and readiness contracts."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200(async_client: AsyncClient):
    """Verify /health returns 200, valid payload, and no secret leakage."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data
    assert "timestamp" in data
    # Invariant: No database or secret tokens in public health response
    assert "password" not in response.text.lower()
    assert "secret" not in response.text.lower()


@pytest.mark.asyncio
async def test_readiness_check_returns_200(async_client: AsyncClient):
    """Verify /ready returns 200 and readiness status."""
    response = await async_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["api"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_request_id_and_security_headers_injected(async_client: AsyncClient):
    """Verify correlation ID and OWASP defensive security headers."""
    # When X-Request-ID is not provided, server generates one
    response = await async_client.get("/health")
    assert response.status_code == 200
    req_id = response.headers.get("X-Request-ID")
    assert req_id is not None
    assert len(req_id) > 10

    # OWASP Security Headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "X-Process-Time-Ms" in response.headers


@pytest.mark.asyncio
async def test_custom_request_id_preserved(async_client: AsyncClient):
    """Verify client-supplied correlation ID is preserved."""
    custom_id = "test-corr-id-12345"
    response = await async_client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


@pytest.mark.asyncio
async def test_not_found_endpoint_returns_json_and_headers(async_client: AsyncClient):
    """Verify 404 response includes correlation ID and security headers."""
    response = await async_client.get("/api/v1/nonexistent-resource")
    assert response.status_code == 404
    assert "X-Request-ID" in response.headers
    assert response.headers.get("X-Frame-Options") == "DENY"
