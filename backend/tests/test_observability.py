"""Tests for Phase P19: Observability, Reliability, Circuit Breaking, and Recovery."""

import time
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.identity import UserAccount
from app.db.models.organization import Organization
from app.db.session import get_db
from app.domain.observability.backup_recovery import BackupRecoverySimulator
from app.domain.observability.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
)
from app.domain.observability.health_service import DeepHealthService
from app.domain.observability.metrics import MetricsCollector
from app.main import app


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


def test_metrics_collector_and_prometheus_export():
    """Validates metrics accumulation, token accounting, and Prometheus exposition format."""
    collector = MetricsCollector()
    collector._init_metrics()  # Fresh state for test

    # 1. Record HTTP requests
    collector.record_http_request("GET", "/health", 200, 0.005)
    collector.record_http_request("GET", "/health", 200, 0.004)
    collector.record_http_request("POST", "/api/v1/auth/login", 200, 0.045)
    collector.record_http_request("POST", "/api/v1/tutoring/turn", 500, 0.500)

    # 2. Record AI Provider calls & token consumption
    collector.record_ai_call(
        "openai", "gpt-4o", "success", 0.450, prompt_tokens=120, completion_tokens=85
    )
    collector.record_ai_call(
        "anthropic", "claude-3-5-sonnet", "rate_limit", 0.200, prompt_tokens=50, completion_tokens=0
    )

    collector.set_outbox_lag(12)
    collector.set_circuit_trips(1)

    # Summary JSON verification
    summary = collector.get_summary()
    assert summary["total_http_requests"] == 4
    assert summary["total_ai_calls"] == 2
    assert summary["ai_token_consumption"]["prompt_tokens"] == 170
    assert summary["ai_token_consumption"]["completion_tokens"] == 85
    assert summary["ai_token_consumption"]["total_tokens"] == 255
    assert summary["outbox_lag_gauge"] == 12

    # Prometheus export verification
    prom = collector.generate_prometheus()
    assert "# HELP gayatri_http_requests_total" in prom
    assert 'gayatri_http_requests_total{method="GET",path="/health",status="200"} 2' in prom
    assert 'gayatri_ai_calls_total{provider="openai",model="gpt-4o",status="success"} 1' in prom
    assert 'gayatri_ai_tokens_total{provider="openai",type="prompt"} 120' in prom
    assert "gayatri_outbox_lag_gauge 12" in prom
    assert "gayatri_circuit_trips_gauge 1" in prom


def test_circuit_breaker_lifecycle_and_fast_fail():
    """Validates circuit breaker state machine: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    breaker = CircuitBreaker(
        name="test_ai_provider",
        failure_threshold=3,
        recovery_timeout_seconds=0.1,  # 100ms for test
        half_open_success_threshold=2,
    )

    # 1. Initially CLOSED
    assert breaker.state == CircuitState.CLOSED
    assert breaker.can_execute() is True
    breaker.require_execution_permission()  # Does not raise

    # 2. Record 2 failures (below threshold) -> Remains CLOSED
    breaker.record_failure("error 1")
    breaker.record_failure("error 2")
    assert breaker.state == CircuitState.CLOSED
    assert breaker.consecutive_failures == 2

    # 3. 3rd failure reaches threshold -> Trips to OPEN
    breaker.record_failure("error 3")
    assert breaker.state == CircuitState.OPEN
    assert breaker.can_execute() is False

    # Immediate execution raises 503 Service Unavailable fast-fail
    with pytest.raises(HTTPException) as exc:
        breaker.require_execution_permission()
    assert exc.value.status_code == 503
    assert "fast-failed" in exc.value.detail

    # 4. Wait for recovery cooldown (100ms)
    time.sleep(0.12)

    # Breaker enters HALF_OPEN probe state
    assert breaker.can_execute() is True
    assert breaker.state == CircuitState.HALF_OPEN

    # 5. First probe succeeds
    breaker.record_success()
    assert breaker.state == CircuitState.HALF_OPEN
    assert breaker.consecutive_successes == 1

    # 6. Second probe succeeds -> Fully recovered to CLOSED
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.consecutive_successes == 0
    assert breaker.consecutive_failures == 0


def test_circuit_breaker_emergency_kill_switch():
    """Validates administrative emergency kill-switch manual trip and reset."""
    breaker = CircuitBreaker(name="gemini_pro", failure_threshold=5)

    assert breaker.state == CircuitState.CLOSED

    # Admin emergency kill-switch trip
    breaker.manual_trip(reason="Security team detected anomalous token spike")
    assert breaker.state == CircuitState.OPEN
    assert breaker.is_manual_trip is True
    assert breaker.can_execute() is False

    with pytest.raises(HTTPException) as exc:
        breaker.require_execution_permission()
    assert exc.value.status_code == 503
    assert "anomalous token spike" in exc.value.detail

    # Admin manual reset
    breaker.manual_reset()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.is_manual_trip is False
    assert breaker.can_execute() is True


def test_circuit_breaker_registry_singleton():
    """Validates global registry lookup and retrieval."""
    b1 = CircuitBreakerRegistry.get("OpenAI")
    b2 = CircuitBreakerRegistry.get("openai")
    assert b1 is b2
    assert b1.name == "openai"


@pytest.mark.asyncio
async def test_deep_health_readiness_probe(db_session: AsyncSession):
    """Verifies that DeepHealthService checks DB, storage, outbox, and circuit breakers."""
    service = DeepHealthService(db_session)
    health = await service.check_readiness()

    assert health["status"] in ("healthy", "degraded")
    assert "database" in health["components"]
    assert health["components"]["database"]["status"] == "healthy"
    assert health["components"]["database"]["latency_ms"] >= 0.0

    assert "storage" in health["components"]
    assert health["components"]["storage"]["status"] == "healthy"

    assert "event_outbox" in health["components"]
    assert health["components"]["event_outbox"]["unprocessed_events_lag"] >= 0

    assert "circuit_breakers" in health["components"]
    assert health["components"]["circuit_breakers"]["total_monitored"] >= 5


@pytest.mark.asyncio
async def test_backup_snapshot_creation_and_restore_simulation(db_session: AsyncSession):
    """Verifies creation of deterministic backup snapshot manifest and simulated recovery."""
    # Seed some sample data
    ts = datetime.now(UTC).timestamp()
    org = Organization(name="Backup Test Org", slug=f"backup-org-{int(ts)}", status="active")
    user = UserAccount(email=f"backup.{ts}@test.org", full_name="Backup Tester", is_active=True)
    db_session.add_all([org, user])
    await db_session.commit()

    sim = BackupRecoverySimulator(db_session)

    # 1. Create Snapshot Manifest
    snapshot = await sim.create_snapshot(snapshot_label="nightly_backup_test")
    assert snapshot["status"] == "created_and_verified"
    assert snapshot["snapshot_id"].startswith("snap-")
    assert len(snapshot["checksum_sha256"]) == 64
    assert snapshot["inventory"]["user_accounts"] >= 1
    assert snapshot["inventory"]["organizations"] >= 1
    assert snapshot["encryption"] == "AES-256-GCM"

    # 2. Simulate Restore Verification -> SUCCESS
    restore_report = sim.verify_and_simulate_restore(snapshot)
    assert restore_report["status"] == "restored_successfully"
    assert restore_report["checksum_verified"] is True
    assert restore_report["data_divergence_detected"] is False
    assert restore_report["recovery_readiness_score"] == 100.0

    # 3. Corrupt Checksum Verification -> FAILS with 400
    corrupted_snapshot = dict(snapshot)
    corrupted_snapshot["checksum_sha256"] = "invalid_corrupted_tampered_hash_0123456789abcdef"
    with pytest.raises(HTTPException) as exc:
        sim.verify_and_simulate_restore(corrupted_snapshot)
    assert exc.value.status_code == 400
    assert "checksum mismatch" in exc.value.detail


@pytest.mark.asyncio
async def test_observability_api_endpoints(db_session: AsyncSession, async_client):
    """Verify Prometheus metrics and deep health probe over REST API."""

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    try:
        # 1. Prometheus scraping endpoint
        prom_res = await async_client.get("/api/v1/observability/metrics/prometheus")
        assert prom_res.status_code == 200
        assert "text/plain" in prom_res.headers.get("content-type", "")
        assert "gayatri_http_requests_total" in prom_res.text

        # 2. Deep health probe
        health_res = await async_client.get("/api/v1/observability/deep-health")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["status"] in ("healthy", "degraded")
        assert "database" in health_data["components"]
        assert health_data["components"]["database"]["status"] == "healthy"
        assert "storage" in health_data["components"]
    finally:
        app.dependency_overrides.pop(get_db, None)
