"""Organization, Membership, and Multi-Tenancy Domain Services."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum
from app.core.security import hash_token
from app.db.models.identity import UserAccount
from app.db.models.organization import (
    GuardianRelationship,
    Invitation,
    Membership,
    Organization,
    RoleAssignment,
)

# --- Schemas ---


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    status: str
    created_at: datetime


class CreateInvitationRequest(BaseModel):
    email: EmailStr
    proposed_role: str = Field(
        description="Role to grant: STUDENT, TEACHER, PARENT, ACADEMIC_ADMIN, ORG_ADMIN"
    )


class InvitationResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    proposed_role: str
    token: str
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    token: str


class MemberResponse(BaseModel):
    membership_id: str
    user_id: str
    email: str
    full_name: str
    status: str
    roles: list[str]
    created_at: datetime


class UserMembershipResponse(BaseModel):
    id: str
    organization_id: str
    organization_name: str
    organization_slug: str
    role: str
    is_active: bool


class LinkGuardianRequest(BaseModel):
    student_id: str


# --- Domain Logic ---


def validate_role_compatibility(existing_roles: list[str], new_role: str) -> None:
    """Enforce non-negotiable role compatibility rules.

    Rule: A person cannot be both Student and Teacher (DEC-C03).
    Rule: Teacher + Parent is allowed.
    """
    clean_new_role = new_role.upper().strip()
    upper_existing = [r.upper().strip() for r in existing_roles]

    if clean_new_role == RoleEnum.STUDENT.value and RoleEnum.TEACHER.value in upper_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role Incompatibility: A user cannot hold both Student and Teacher roles.",
        )
    if clean_new_role == RoleEnum.TEACHER.value and RoleEnum.STUDENT.value in upper_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role Incompatibility: A user cannot hold both Student and Teacher roles.",
        )


class OrganizationService:
    """Domain service for managing organizations, memberships, invitations, and guardian links."""

    @staticmethod
    async def create_organization(
        session: AsyncSession,
        creator_user: UserAccount,
        req: CreateOrganizationRequest,
    ) -> Organization:
        """Create a new tenant organization and assign creator as ORG_ADMIN."""
        clean_slug = req.slug.lower().strip()
        existing = await session.execute(
            select(Organization).where(Organization.slug == clean_slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An organization with this slug already exists.",
            )

        # 1. Create Organization
        org = Organization(
            name=req.name.strip(),
            slug=clean_slug,
            status="active",
        )
        session.add(org)
        await session.flush()

        # 2. Assign creator membership
        membership = Membership(
            user_id=creator_user.id,
            organization_id=org.id,
            status="active",
        )
        session.add(membership)
        await session.flush()

        # 3. Grant ORG_ADMIN role
        role = RoleAssignment(
            membership_id=membership.id,
            role=RoleEnum.ORG_ADMIN.value,
            scope="organization",
        )
        session.add(role)
        await session.commit()
        await session.refresh(org)
        return org

    @staticmethod
    async def list_user_organizations(
        session: AsyncSession,
        user_id: str,
    ) -> list[Organization]:
        """List all active organizations the user belongs to."""
        stmt = (
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(
                Membership.user_id == user_id,
                Membership.status == "active",
                Organization.is_deleted.is_(False),
            )
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def list_user_memberships(
        session: AsyncSession,
        user_id: str,
    ) -> list[UserMembershipResponse]:
        """List all active memberships and primary assigned roles for a user."""
        stmt = (
            select(Membership, Organization)
            .join(Organization, Organization.id == Membership.organization_id)
            .where(
                Membership.user_id == user_id,
                Membership.status == "active",
                Organization.is_deleted.is_(False),
            )
        )
        res = await session.execute(stmt)
        rows = res.all()

        memberships: list[UserMembershipResponse] = []
        for membership, org in rows:
            roles_res = await session.execute(
                select(RoleAssignment.role).where(RoleAssignment.membership_id == membership.id)
            )
            roles = [r[0] for r in roles_res.fetchall()]
            role = roles[0] if roles else RoleEnum.STUDENT.value
            memberships.append(
                UserMembershipResponse(
                    id=membership.id,
                    organization_id=org.id,
                    organization_name=org.name,
                    organization_slug=org.slug,
                    role=role,
                    is_active=membership.status == "active",
                )
            )
        return memberships

    @staticmethod
    async def create_invitation(
        session: AsyncSession,
        organization_id: str,
        req: CreateInvitationRequest,
    ) -> InvitationResponse:
        """Create a single-use invitation token for an organization."""
        clean_role = req.proposed_role.upper().strip()
        valid_roles = [r.value for r in RoleEnum if r != RoleEnum.SUPER_ADMIN]
        if clean_role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid proposed role. Must be one of: {valid_roles}",
            )

        raw_token = secrets.token_urlsafe(32)
        token_digest = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(days=7)

        invitation = Invitation(
            organization_id=organization_id,
            email=req.email.lower().strip(),
            token_hash=token_digest,
            proposed_role=clean_role,
            expires_at=expires_at,
            is_used=False,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)

        return InvitationResponse(
            id=invitation.id,
            organization_id=invitation.organization_id,
            email=invitation.email,
            proposed_role=invitation.proposed_role,
            token=raw_token,
            expires_at=invitation.expires_at,
        )

    @staticmethod
    async def accept_invitation(
        session: AsyncSession,
        user: UserAccount,
        raw_token: str,
    ) -> Membership:
        """Redeem a single-use invitation token and link user to organization."""
        token_digest = hash_token(raw_token)
        stmt = select(Invitation).where(
            Invitation.token_hash == token_digest,
            Invitation.is_used.is_(False),
        )
        res = await session.execute(stmt)
        invitation = res.scalar_one_or_none()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token.",
            )

        expires_at = (
            invitation.expires_at.replace(tzinfo=UTC)
            if invitation.expires_at.tzinfo is None
            else invitation.expires_at
        )
        if expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation token has expired.",
            )

        # Check existing membership
        mem_stmt = select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == invitation.organization_id,
        )
        mem_res = await session.execute(mem_stmt)
        membership = mem_res.scalar_one_or_none()

        existing_roles: list[str] = []
        if membership:
            roles_res = await session.execute(
                select(RoleAssignment.role).where(RoleAssignment.membership_id == membership.id)
            )
            existing_roles = [r[0] for r in roles_res.fetchall()]
        else:
            membership = Membership(
                user_id=user.id,
                organization_id=invitation.organization_id,
                status="active",
            )
            session.add(membership)
            await session.flush()

        # Enforce role compatibility
        validate_role_compatibility(existing_roles, invitation.proposed_role)

        # Assign role if not already present
        if invitation.proposed_role not in existing_roles:
            role_assignment = RoleAssignment(
                membership_id=membership.id,
                role=invitation.proposed_role,
            )
            session.add(role_assignment)

        # Invalidate invitation
        invitation.is_used = True
        await session.commit()
        await session.refresh(membership)
        return membership

    @staticmethod
    async def list_members(session: AsyncSession, organization_id: str) -> list[MemberResponse]:
        """List all members and their assigned roles in an organization."""
        stmt = (
            select(Membership, UserAccount)
            .join(UserAccount, UserAccount.id == Membership.user_id)
            .where(
                Membership.organization_id == organization_id,
                Membership.status == "active",
                UserAccount.is_deleted.is_(False),
            )
        )
        res = await session.execute(stmt)
        rows = res.all()

        results: list[MemberResponse] = []
        for membership, user in rows:
            roles_stmt = select(RoleAssignment.role).where(
                RoleAssignment.membership_id == membership.id
            )
            roles_res = await session.execute(roles_stmt)
            roles = [r[0] for r in roles_res.fetchall()]

            results.append(
                MemberResponse(
                    membership_id=membership.id,
                    user_id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    status=membership.status,
                    roles=roles,
                    created_at=membership.created_at,
                )
            )
        return results

    @staticmethod
    async def link_guardian_to_student(
        session: AsyncSession,
        guardian_user_id: str,
        student_user_id: str,
    ) -> GuardianRelationship:
        """Establish relationship between a parent/guardian and a student."""
        if guardian_user_id == student_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user cannot link themselves as their own guardian.",
            )

        # Verify both users exist
        res = await session.execute(
            select(UserAccount).where(UserAccount.id.in_([guardian_user_id, student_user_id]))
        )
        users = res.scalars().all()
        if len(users) < 2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both specified user accounts do not exist.",
            )

        # Check existing link
        stmt = select(GuardianRelationship).where(
            GuardianRelationship.guardian_id == guardian_user_id,
            GuardianRelationship.student_id == student_user_id,
        )
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Guardian relationship is already established.",
            )

        rel = GuardianRelationship(
            guardian_id=guardian_user_id,
            student_id=student_user_id,
            verification_status="verified",
            is_active=True,
        )
        session.add(rel)
        await session.commit()
        await session.refresh(rel)
        return rel

    @staticmethod
    async def verify_guardian_student_access(
        session: AsyncSession,
        guardian_user_id: str,
        student_user_id: str,
    ) -> bool:
        """Verify whether guardian has authorized active access to student."""
        stmt = select(GuardianRelationship).where(
            GuardianRelationship.guardian_id == guardian_user_id,
            GuardianRelationship.student_id == student_user_id,
            GuardianRelationship.verification_status == "verified",
            GuardianRelationship.is_active.is_(True),
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none() is not None
