"""Organization, Membership, and Multi-Tenant RBAC Endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, require_roles, resolve_tenant_context
from app.db.models.identity import UserAccount
from app.db.session import get_db
from app.domain.auth import get_current_user
from app.domain.organization import (
    AcceptInvitationRequest,
    CreateInvitationRequest,
    CreateOrganizationRequest,
    InvitationResponse,
    LinkGuardianRequest,
    MemberResponse,
    OrganizationResponse,
    OrganizationService,
)

router = APIRouter()


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization tenant",
)
async def create_organization(
    req: CreateOrganizationRequest,
    current_user: UserAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """Create a new tenant organization and automatically assign creator as ORG_ADMIN."""
    org = await OrganizationService.create_organization(session, current_user, req)
    return OrganizationResponse.model_validate(org)


@router.get(
    "/me",
    response_model=list[OrganizationResponse],
    status_code=status.HTTP_200_OK,
    summary="List active organizations for current user",
)
async def list_my_organizations(
    current_user: UserAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[OrganizationResponse]:
    """List all organizations where the authenticated user holds an active membership."""
    orgs = await OrganizationService.list_user_organizations(session, current_user.id)
    return [OrganizationResponse.model_validate(o) for o in orgs]


@router.post(
    "/{organization_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue an invitation to join the organization",
)
async def invite_member(
    organization_id: str,
    req: CreateInvitationRequest,
    context: TenantContext = Depends(require_roles(RoleEnum.ORG_ADMIN.value)),
    session: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    """Generate a single-use cryptographic invitation token (requires ORG_ADMIN)."""
    return await OrganizationService.create_invitation(session, organization_id, req)


@router.post(
    "/invitations/accept",
    status_code=status.HTTP_200_OK,
    summary="Accept an invitation token to join an organization",
)
async def accept_invitation(
    req: AcceptInvitationRequest,
    current_user: UserAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Redeem invitation token and join organization with the proposed role."""
    membership = await OrganizationService.accept_invitation(session, current_user, req.token)
    return {
        "status": "ok",
        "message": "Invitation accepted successfully.",
        "organization_id": membership.organization_id,
    }


@router.get(
    "/{organization_id}/members",
    response_model=list[MemberResponse],
    status_code=status.HTTP_200_OK,
    summary="List members in the organization",
)
async def list_members(
    organization_id: str,
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.ORG_ADMIN.value, RoleEnum.ACADEMIC_ADMIN.value, RoleEnum.TEACHER.value
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    """List all active members and their roles within the tenant (requires staff role)."""
    return await OrganizationService.list_members(session, organization_id)


@router.post(
    "/{organization_id}/guardians",
    status_code=status.HTTP_201_CREATED,
    summary="Establish guardian relationship to a student learner",
)
async def link_guardian(
    organization_id: str,
    req: LinkGuardianRequest,
    current_user: UserAccount = Depends(get_current_user),
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Link current user as guardian to the specified student."""
    await OrganizationService.link_guardian_to_student(session, current_user.id, req.student_id)
    return {"status": "ok", "message": "Guardian relationship established."}
