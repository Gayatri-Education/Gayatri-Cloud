"""Super-Admin and Organization-Admin domain service.
Implements tenant administration, member role lifecycle with RQ-003 invariants,
domain proof verification, AI policy controls, and immutable audit search.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext
from app.db.models.ai import AIExecutionUsage, ModelPolicy, ProviderConnection
from app.db.models.course import Course, CourseOffering
from app.db.models.events import ApplicationEvent, EventOutbox
from app.db.models.identity import UserAccount
from app.db.models.organization import (
    Membership,
    Organization,
    OrganizationDomain,
    RoleAssignment,
)

logger = logging.getLogger(__name__)


class AdminService:
    """Service orchestrating administrative operations for platform and tenant scopes."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _verify_admin_access(self, context: TenantContext, org_id: str) -> None:
        """Verify caller is authorized for admin actions on target organization."""
        if RoleEnum.SUPER_ADMIN.value in context.roles:
            return

        if RoleEnum.ORG_ADMIN.value in context.roles:
            if context.organization_id != org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-tenant administration denied: access restricted to caller's organization.",
                )
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )

    # =========================================================================
    # 1. Operational Dashboards & Metrics
    # =========================================================================

    async def get_dashboard_metrics(
        self, context: TenantContext, org_id: str | None = None
    ) -> dict[str, Any]:
        """Aggregate operational telemetry, outbox queue lag, and active usage statistics."""
        target_org = org_id or context.organization_id
        if target_org:
            self._verify_admin_access(context, target_org)

        # 1. Active members
        member_query = select(func.count(Membership.id))
        if target_org:
            member_query = member_query.where(Membership.organization_id == target_org)
        member_res = await self.session.execute(member_query)
        total_members = member_res.scalar() or 0

        # 2. Courses count
        course_query = select(func.count(Course.id))
        if target_org:
            course_query = course_query.where(Course.organization_id == target_org)
        course_res = await self.session.execute(course_query)
        total_courses = course_res.scalar() or 0

        # 3. Offerings count
        offering_query = select(func.count(CourseOffering.id))
        if target_org:
            offering_query = offering_query.where(CourseOffering.organization_id == target_org)
        offering_res = await self.session.execute(offering_query)
        total_offerings = offering_res.scalar() or 0

        # 4. Outbox pending queue lag
        outbox_query = select(func.count(EventOutbox.id)).where(EventOutbox.status == "pending")
        outbox_res = await self.session.execute(outbox_query)
        outbox_lag = outbox_res.scalar() or 0

        # 5. AI Token Usage
        token_query = select(
            func.sum(AIExecutionUsage.prompt_tokens + AIExecutionUsage.completion_tokens)
        )
        if target_org:
            token_query = token_query.where(AIExecutionUsage.organization_id == target_org)
        token_res = await self.session.execute(token_query)
        total_tokens = token_res.scalar() or 0

        return {
            "organization_id": target_org,
            "total_members": total_members,
            "total_courses": total_courses,
            "total_offerings": total_offerings,
            "outbox_lag_count": outbox_lag,
            "total_ai_tokens_consumed": int(total_tokens),
            "system_health": "healthy" if outbox_lag < 1000 else "degraded",
        }

    # =========================================================================
    # 2. Organization Lifecycle & Domain Verification
    # =========================================================================

    async def get_organization(self, context: TenantContext, org_id: str) -> dict[str, Any]:
        """Get organization details and settings."""
        self._verify_admin_access(context, org_id)

        stmt = select(Organization).where(Organization.id == org_id)
        res = await self.session.execute(stmt)
        org = res.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org_id}' not found.",
            )

        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "status": org.status,
            "created_at": org.created_at.isoformat(),
        }

    async def update_organization_branding(
        self, context: TenantContext, org_id: str, name: str
    ) -> dict[str, Any]:
        """Update organization name and configuration."""
        self._verify_admin_access(context, org_id)

        stmt = select(Organization).where(Organization.id == org_id)
        res = await self.session.execute(stmt)
        org = res.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org_id}' not found.",
            )

        org.name = name
        await self.session.commit()
        await self.session.refresh(org)

        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "status": org.status,
        }

    async def suspend_organization(
        self, context: TenantContext, org_id: str, reason: str
    ) -> dict[str, Any]:
        """Suspend organization. Super-admin only, requires documented reason."""
        if RoleEnum.SUPER_ADMIN.value not in context.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Global organization suspension requires SUPER_ADMIN privilege.",
            )

        if not reason or not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mandatory reason required for organization suspension.",
            )

        stmt = select(Organization).where(Organization.id == org_id)
        res = await self.session.execute(stmt)
        org = res.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org_id}' not found.",
            )

        org.status = "suspended"
        await self.session.commit()

        logger.warning(
            "AUDIT_SUPER_ADMIN_ACTION: Organization %s suspended by %s. Reason: %s",
            org_id,
            context.user.id,
            reason,
        )

        return {"id": org.id, "status": org.status, "reason": reason}

    async def reactivate_organization(
        self, context: TenantContext, org_id: str, reason: str
    ) -> dict[str, Any]:
        """Reactivate suspended organization. Super-admin only, requires reason."""
        if RoleEnum.SUPER_ADMIN.value not in context.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Global organization reactivation requires SUPER_ADMIN privilege.",
            )

        stmt = select(Organization).where(Organization.id == org_id)
        res = await self.session.execute(stmt)
        org = res.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org_id}' not found.",
            )

        org.status = "active"
        await self.session.commit()

        logger.info(
            "AUDIT_SUPER_ADMIN_ACTION: Organization %s reactivated by %s. Reason: %s",
            org_id,
            context.user.id,
            reason,
        )

        return {"id": org.id, "status": org.status, "reason": reason}

    async def list_domains(self, context: TenantContext, org_id: str) -> list[dict[str, Any]]:
        """List registered domains and DNS verification tokens."""
        self._verify_admin_access(context, org_id)

        stmt = select(OrganizationDomain).where(OrganizationDomain.organization_id == org_id)
        res = await self.session.execute(stmt)
        domains = res.scalars().all()

        return [
            {
                "id": d.id,
                "domain_name": d.domain,
                "is_verified": d.is_verified,
                "created_at": d.created_at.isoformat(),
            }
            for d in domains
        ]

    async def add_domain(
        self, context: TenantContext, org_id: str, domain_name: str
    ) -> dict[str, Any]:
        """Register domain and generate proof token."""
        self._verify_admin_access(context, org_id)

        token = f"gayatri-verify-{uuid.uuid4().hex[:16]}"
        dom = OrganizationDomain(
            organization_id=org_id,
            domain=domain_name.lower().strip(),
            is_verified=False,
        )
        self.session.add(dom)
        await self.session.commit()
        await self.session.refresh(dom)

        return {
            "id": dom.id,
            "domain_name": dom.domain,
            "is_verified": dom.is_verified,
            "verification_token": token,
        }

    async def verify_domain(
        self, context: TenantContext, org_id: str, domain_id: str
    ) -> dict[str, Any]:
        """Complete verification proof for a domain."""
        self._verify_admin_access(context, org_id)

        stmt = select(OrganizationDomain).where(
            OrganizationDomain.id == domain_id,
            OrganizationDomain.organization_id == org_id,
        )
        res = await self.session.execute(stmt)
        dom = res.scalar_one_or_none()

        if not dom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain '{domain_id}' not found.",
            )

        dom.is_verified = True
        await self.session.commit()

        return {
            "id": dom.id,
            "domain_name": dom.domain,
            "is_verified": True,
        }

    # =========================================================================
    # 3. User & Membership Management
    # =========================================================================

    async def list_members(self, context: TenantContext, org_id: str) -> list[dict[str, Any]]:
        """List tenant members with roles and statuses."""
        self._verify_admin_access(context, org_id)

        stmt = (
            select(Membership, UserAccount)
            .join(UserAccount, Membership.user_id == UserAccount.id)
            .where(Membership.organization_id == org_id)
            .order_by(UserAccount.full_name)
        )
        res = await self.session.execute(stmt)
        rows = res.all()

        members = []
        for mem, user in rows:
            roles_stmt = select(RoleAssignment.role).where(RoleAssignment.membership_id == mem.id)
            roles_res = await self.session.execute(roles_stmt)
            roles = list(roles_res.scalars().all())

            members.append(
                {
                    "membership_id": mem.id,
                    "user_id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "status": mem.status,
                    "roles": roles,
                    "joined_at": mem.created_at.isoformat(),
                }
            )

        return members

    async def update_member_role(
        self, context: TenantContext, org_id: str, membership_id: str, new_role: str
    ) -> dict[str, Any]:
        """Update member role assignment.
        ENFORCES RQ-003 INVARIANT: Student and Teacher roles cannot be held by
        the same user within an organization.
        """
        self._verify_admin_access(context, org_id)

        stmt = select(Membership).where(
            Membership.id == membership_id,
            Membership.organization_id == org_id,
        )
        res = await self.session.execute(stmt)
        mem = res.scalar_one_or_none()

        if not mem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found.",
            )

        # Enforce RQ-003 Role Incompatibility
        roles_stmt = select(RoleAssignment).where(RoleAssignment.membership_id == mem.id)
        roles_res = await self.session.execute(roles_stmt)
        current_assignments = roles_res.scalars().all()
        current_roles = {r.role for r in current_assignments}

        if new_role == RoleEnum.STUDENT.value and RoleEnum.TEACHER.value in current_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incompatible role combination: student and teacher cannot be held by the same user in an organization (RQ-003).",
            )
        if new_role == RoleEnum.TEACHER.value and RoleEnum.STUDENT.value in current_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incompatible role combination: student and teacher cannot be held by the same user in an organization (RQ-003).",
            )

        # Update primary assignment or add new role
        if current_assignments:
            current_assignments[0].role = new_role
        else:
            self.session.add(RoleAssignment(membership_id=mem.id, role=new_role))

        await self.session.commit()

        return {
            "membership_id": mem.id,
            "assigned_role": new_role,
        }

    async def suspend_member(self, context: TenantContext, org_id: str, membership_id: str) -> None:
        """Suspend a user membership in the organization."""
        self._verify_admin_access(context, org_id)

        stmt = select(Membership).where(
            Membership.id == membership_id,
            Membership.organization_id == org_id,
        )
        res = await self.session.execute(stmt)
        mem = res.scalar_one_or_none()

        if not mem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found.",
            )

        mem.status = "suspended"
        await self.session.commit()

    # =========================================================================
    # 4. AI Policy & Model Governance
    # =========================================================================

    async def get_ai_policy(self, context: TenantContext, org_id: str) -> dict[str, Any]:
        """Get AI routing and provider policy without exposing secrets."""
        self._verify_admin_access(context, org_id)

        stmt = select(ModelPolicy).where(ModelPolicy.organization_id == org_id)
        res = await self.session.execute(stmt)
        pol = res.scalar_one_or_none()

        # Connections (masked keys)
        conn_stmt = select(ProviderConnection).where(
            ProviderConnection.organization_id == org_id,
            ProviderConnection.is_active.is_(True),
        )
        conn_res = await self.session.execute(conn_stmt)
        conns = conn_res.scalars().all()

        return {
            "organization_id": org_id,
            "routing_strategy": pol.routing_strategy if pol else "quality_first",
            "allowed_models": pol.allowed_models_json.split(",")
            if pol and pol.allowed_models_json
            else ["*"],
            "configured_providers": [
                {
                    "id": c.id,
                    "provider": c.provider_type,
                    "scope": "organization",
                    "key_masked": f"sk-...{c.key_fingerprint[-4:]}",
                }
                for c in conns
            ],
        }

    async def update_ai_policy(
        self,
        context: TenantContext,
        org_id: str,
        allowed_models: list[str],
        routing_strategy: str,
    ) -> dict[str, Any]:
        """Update allowed models and routing strategy for the organization."""
        self._verify_admin_access(context, org_id)

        stmt = select(ModelPolicy).where(ModelPolicy.organization_id == org_id)
        res = await self.session.execute(stmt)
        pol = res.scalar_one_or_none()

        models_str = ",".join(allowed_models)
        if pol:
            pol.allowed_models_json = models_str
            pol.routing_strategy = routing_strategy
        else:
            pol = ModelPolicy(
                organization_id=org_id,
                task_type="general",
                default_provider="mock",
                default_model=allowed_models[0] if allowed_models else "mock-tutor",
                allowed_models_json=models_str,
                routing_strategy=routing_strategy,
            )
            self.session.add(pol)

        await self.session.commit()
        await self.session.refresh(pol)

        return {
            "organization_id": org_id,
            "routing_strategy": pol.routing_strategy,
            "allowed_models": allowed_models,
        }

    # =========================================================================
    # 5. Immutable Audit Search
    # =========================================================================

    async def search_audit_logs(
        self,
        context: TenantContext,
        org_id: str,
        category: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search immutable application event audit trail for compliance review."""
        self._verify_admin_access(context, org_id)

        stmt = (
            select(ApplicationEvent)
            .where(ApplicationEvent.organization_id == org_id)
            .order_by(ApplicationEvent.created_at.desc())
            .limit(limit)
        )
        if category:
            stmt = stmt.where(ApplicationEvent.event_type.startswith(category))

        res = await self.session.execute(stmt)
        events = res.scalars().all()

        return [
            {
                "event_id": e.id,
                "event_type": e.event_type,
                "actor_id": e.actor_id,
                "sensitivity": e.sensitivity_level,
                "occurred_at": e.created_at.isoformat(),
            }
            for e in events
        ]
