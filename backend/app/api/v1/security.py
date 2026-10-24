"""Security, Privacy, and Data Subject Rights REST Endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext, resolve_tenant_context
from app.db.session import get_db
from app.domain.security.deletion import DeletionService
from app.domain.security.ssrf_guard import validate_outbound_url

router = APIRouter(prefix="/security", tags=["Security, Privacy & Data Subject Rights"])


class DeletionRequestInput(BaseModel):
    reason: str | None = Field(default=None, max_length=500)
    immediate: bool = Field(
        default=False,
        description="Whether to purge immediately or allow 7-day grace period.",
    )


class UrlValidationInput(BaseModel):
    url: str = Field(..., max_length=1000)


@router.post("/validate-url", status_code=status.HTTP_200_OK)
async def validate_url(
    payload: UrlValidationInput,
    _context: TenantContext = Depends(resolve_tenant_context),
) -> dict[str, Any]:
    """Validate user-supplied URL against SSRF, metadata IPs, and private networks."""
    validated = validate_outbound_url(payload.url)
    return {
        "status": "valid",
        "url": validated,
        "message": "URL passed SSRF security checks.",
    }


@router.get("/export", status_code=status.HTTP_200_OK)
async def download_data_export(
    user_id: str | None = Query(
        default=None, description="Optional target user ID (super-admin only)"
    ),
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate and return machine-readable JSON data export archive (GDPR Art. 20)."""
    target = user_id or context.user.id
    service = DeletionService(db)
    return await service.generate_user_data_export(context, target)


@router.post("/deletion-request", status_code=status.HTTP_201_CREATED)
async def request_deletion(
    payload: DeletionRequestInput,
    user_id: str | None = Query(default=None),
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Initiate an account deletion request with 7-day grace period."""
    target = user_id or context.user.id
    service = DeletionService(db)
    return await service.request_account_deletion(
        context=context,
        target_user_id=target,
        reason=payload.reason,
        immediate=payload.immediate,
    )


@router.get("/deletion-request", status_code=status.HTTP_200_OK)
async def get_deletion_status(
    user_id: str | None = Query(default=None),
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check account deletion status and grace period expiration."""
    target = user_id or context.user.id
    service = DeletionService(db)
    return await service.get_deletion_status(context, target)


@router.post("/deletion-request/cancel", status_code=status.HTTP_200_OK)
async def cancel_deletion(
    user_id: str | None = Query(default=None),
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Cancel pending account deletion during grace period."""
    target = user_id or context.user.id
    service = DeletionService(db)
    return await service.cancel_deletion_request(context, target)


@router.get("/audit", status_code=status.HTTP_200_OK)
async def get_user_audit(
    user_id: str | None = Query(default=None),
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve personal security audit trail."""
    target = user_id or context.user.id
    service = DeletionService(db)
    return await service.get_user_security_audit(context, target)
