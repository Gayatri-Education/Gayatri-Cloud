"""REST API endpoints for Super-Admin and Organization-Admin Portal."""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, require_roles
from app.db.session import get_db
from app.domain.admin.service import AdminService

router = APIRouter(prefix="/admin", tags=["Administration Portal"])

admin_auth = require_roles(
    RoleEnum.ORG_ADMIN.value,
    RoleEnum.SUPER_ADMIN.value,
)


class UpdateBrandingRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)


class ReasonRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Mandatory audit justification")


class AddDomainRequest(BaseModel):
    domain_name: str = Field(..., min_length=3, max_length=255)


class UpdateMemberRoleRequest(BaseModel):
    new_role: str = Field(..., description="STUDENT, TEACHER, ORG_ADMIN, etc.")


class UpdateAiPolicyRequest(BaseModel):
    allowed_models: list[str] = Field(default_factory=list)
    routing_strategy: str = Field("quality_first")


# =============================================================================
# 1. Dashboard
# =============================================================================


@router.get("/dashboard", summary="Operational telemetry and admin metrics")
async def get_admin_dashboard(
    organization_id: str | None = Query(None),
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.get_dashboard_metrics(context, organization_id)


# =============================================================================
# 2. Organization Lifecycle & Domain Verification
# =============================================================================


@router.get("/organizations/{org_id}", summary="Get organization details")
async def get_organization(
    org_id: str,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.get_organization(context, org_id)


@router.patch("/organizations/{org_id}", summary="Update organization branding")
async def update_organization_branding(
    org_id: str,
    req: UpdateBrandingRequest,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.update_organization_branding(context, org_id, req.name)


@router.post("/organizations/{org_id}/suspend", summary="Suspend organization (Super-admin only)")
async def suspend_organization(
    org_id: str,
    req: ReasonRequest,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.suspend_organization(context, org_id, req.reason)


@router.post(
    "/organizations/{org_id}/reactivate", summary="Reactivate organization (Super-admin only)"
)
async def reactivate_organization(
    org_id: str,
    req: ReasonRequest,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.reactivate_organization(context, org_id, req.reason)


@router.get("/organizations/{org_id}/domains", summary="List registered organization domains")
async def list_domains(
    org_id: str,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = AdminService(session)
    return await service.list_domains(context, org_id)


@router.post(
    "/organizations/{org_id}/domains",
    status_code=status.HTTP_201_CREATED,
    summary="Add organization domain",
)
async def add_domain(
    org_id: str,
    req: AddDomainRequest,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.add_domain(context, org_id, req.domain_name)


@router.post(
    "/organizations/{org_id}/domains/{domain_id}/verify", summary="Verify organization domain"
)
async def verify_domain(
    org_id: str,
    domain_id: str,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.verify_domain(context, org_id, domain_id)


# =============================================================================
# 3. User & Membership Management
# =============================================================================


@router.get("/organizations/{org_id}/members", summary="List organization members with roles")
async def list_members(
    org_id: str,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = AdminService(session)
    return await service.list_members(context, org_id)


@router.patch(
    "/organizations/{org_id}/members/{membership_id}/role", summary="Update member role assignment"
)
async def update_member_role(
    org_id: str,
    membership_id: str,
    req: UpdateMemberRoleRequest,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.update_member_role(context, org_id, membership_id, req.new_role)


@router.post(
    "/organizations/{org_id}/members/{membership_id}/suspend",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Suspend organization member",
)
async def suspend_member(
    org_id: str,
    membership_id: str,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = AdminService(session)
    await service.suspend_member(context, org_id, membership_id)


# =============================================================================
# 4. AI Policy Controls
# =============================================================================


@router.get("/organizations/{org_id}/ai-policy", summary="Get organization AI routing policy")
async def get_ai_policy(
    org_id: str,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.get_ai_policy(context, org_id)


@router.put("/organizations/{org_id}/ai-policy", summary="Update organization AI routing policy")
async def update_ai_policy(
    org_id: str,
    req: UpdateAiPolicyRequest,
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AdminService(session)
    return await service.update_ai_policy(context, org_id, req.allowed_models, req.routing_strategy)


# =============================================================================
# 5. Audit Search
# =============================================================================


@router.get("/organizations/{org_id}/audit", summary="Search immutable audit logs")
async def search_audit_logs(
    org_id: str,
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    context: TenantContext = Depends(admin_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = AdminService(session)
    return await service.search_audit_logs(context, org_id, category, limit)
