"""Observability, Telemetry, Circuit Breaking, and Disaster Recovery REST Endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, resolve_tenant_context
from app.db.session import get_db
from app.domain.observability.backup_recovery import BackupRecoverySimulator
from app.domain.observability.circuit_breaker import CircuitBreakerRegistry
from app.domain.observability.health_service import DeepHealthService
from app.domain.observability.metrics import metrics

router = APIRouter(prefix="/observability", tags=["Observability, Reliability & Recovery"])


def require_admin(context: TenantContext = Depends(resolve_tenant_context)) -> TenantContext:
    """Ensures caller has ORG_ADMIN or SUPER_ADMIN role."""
    allowed = {RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value}
    if not any(r in allowed for r in context.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for observability controls.",
        )
    return context


class TripCircuitRequest(BaseModel):
    reason: str = Field(default="Administrative manual kill-switch", max_length=255)


class SnapshotRequest(BaseModel):
    label: str = Field(default="manual_snapshot", max_length=100)


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics_json(
    _admin: TenantContext = Depends(require_admin),
) -> dict[str, Any]:
    """Retrieve structured real-time operational metrics in JSON format."""
    return metrics.get_summary()


@router.get("/metrics/prometheus", status_code=status.HTTP_200_OK)
async def get_prometheus_metrics() -> Response:
    """Prometheus metrics scraping endpoint (OpenMetrics / Prometheus text format)."""
    expo = metrics.generate_prometheus()
    return Response(content=expo, media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get("/deep-health", status_code=status.HTTP_200_OK)
async def get_deep_health(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Deep readiness probe checking database, storage, outbox lag, and circuit breaker states."""
    service = DeepHealthService(db)
    return await service.check_readiness()


@router.post("/circuit-breakers/{provider}/trip", status_code=status.HTTP_200_OK)
async def trip_circuit_breaker(
    provider: str,
    payload: TripCircuitRequest,
    _admin: TenantContext = Depends(require_admin),
) -> dict[str, Any]:
    """Emergency administrative kill-switch to immediately trip an AI provider breaker."""
    breaker = CircuitBreakerRegistry.get(provider)
    breaker.manual_trip(reason=payload.reason)
    return {
        "provider": provider,
        "action": "tripped",
        "status": breaker.get_status(),
        "message": f"Circuit breaker for '{provider}' has been manually tripped.",
    }


@router.post("/circuit-breakers/{provider}/reset", status_code=status.HTTP_200_OK)
async def reset_circuit_breaker(
    provider: str,
    _admin: TenantContext = Depends(require_admin),
) -> dict[str, Any]:
    """Manually reset an open or tripped circuit breaker back to CLOSED state."""
    breaker = CircuitBreakerRegistry.get(provider)
    breaker.manual_reset()
    return {
        "provider": provider,
        "action": "reset",
        "status": breaker.get_status(),
        "message": f"Circuit breaker for '{provider}' has been reset to CLOSED.",
    }


@router.post("/backup/snapshot", status_code=status.HTTP_201_CREATED)
async def create_backup_snapshot(
    payload: SnapshotRequest,
    _admin: TenantContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate point-in-time database backup snapshot metadata with SHA-256 manifest."""
    sim = BackupRecoverySimulator(db)
    return await sim.create_snapshot(snapshot_label=payload.label)


@router.post("/backup/verify", status_code=status.HTTP_200_OK)
async def verify_backup_restore(
    snapshot_metadata: dict[str, Any],
    _admin: TenantContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Verify SHA-256 checksum and simulate disaster recovery into an isolated environment."""
    sim = BackupRecoverySimulator(db)
    return sim.verify_and_simulate_restore(snapshot_metadata)
