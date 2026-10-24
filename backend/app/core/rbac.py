"""Role-Based Access Control (RBAC) and Tenant Scoping Dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.identity import UserAccount
from app.db.models.organization import Membership, RoleAssignment
from app.db.session import get_db
from app.domain.auth import get_current_user


class RoleEnum(StrEnum):
    """Supported roles within Gayatri Cloud."""

    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    ACADEMIC_ADMIN = "ACADEMIC_ADMIN"
    ORG_ADMIN = "ORG_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


@dataclass
class TenantContext:
    """Resolved tenant context for the active request."""

    user: UserAccount
    organization_id: str | None = None
    roles: list[str] = None  # type: ignore

    def has_role(self, *role_names: str) -> bool:
        """Check if active context holds at least one of the specified roles."""
        if self.user.is_super_admin:
            return True
        return any(role in (self.roles or []) for role in role_names)


async def resolve_optional_tenant_context(
    x_organization_id: Annotated[str | None, Header(alias="X-Organization-ID")] = None,
    current_user: UserAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TenantContext:
    """Resolve tenant context if X-Organization-ID header is present, else personal/all active roles."""
    if not x_organization_id:
        stmt = (
            select(RoleAssignment.role, Membership.organization_id)
            .join(Membership, Membership.id == RoleAssignment.membership_id)
            .where(Membership.user_id == current_user.id, Membership.status == "active")
        )
        res = await session.execute(stmt)
        rows = res.all()
        user_roles = [r[0] for r in rows]
        primary_org = rows[0][1] if rows else None

        if current_user.is_super_admin:
            user_roles.append(RoleEnum.SUPER_ADMIN.value)
        if not user_roles:
            user_roles = [RoleEnum.STUDENT.value]

        return TenantContext(
            user=current_user,
            organization_id=primary_org,
            roles=list(set(user_roles)),
        )
    return await resolve_tenant_context(x_organization_id, current_user, session)


async def resolve_tenant_context(
    x_organization_id: Annotated[str | None, Header(alias="X-Organization-ID")] = None,
    current_user: UserAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TenantContext:
    """Validate that the authenticated user holds an active membership in the requested organization."""
    if not x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Organization-ID' is required for organization-scoped operations.",
        )

    # Super Admin bypass
    if current_user.is_super_admin:
        return TenantContext(
            user=current_user,
            organization_id=x_organization_id,
            roles=[RoleEnum.SUPER_ADMIN.value],
        )

    # Query active membership
    stmt = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.organization_id == x_organization_id,
        Membership.status == "active",
    )
    res = await session.execute(stmt)
    membership = res.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have an active membership in this organization.",
        )

    # Query assigned roles
    roles_res = await session.execute(
        select(RoleAssignment.role).where(RoleAssignment.membership_id == membership.id)
    )
    roles = [row[0] for row in roles_res.fetchall()]

    return TenantContext(
        user=current_user,
        organization_id=x_organization_id,
        roles=roles,
    )


def require_roles(*allowed_roles: str):
    """Dependency factory restricting endpoint to users holding specified roles."""

    def role_checker(
        context: TenantContext = Depends(resolve_optional_tenant_context),
    ) -> TenantContext:
        if not context.has_role(*allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Required role in {list(allowed_roles)}.",
            )
        return context

    return role_checker
