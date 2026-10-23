"""Organization and Multi-Tenancy database models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, generate_uuid


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    """Institutional tenant (school, university, coaching academy)."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    branding_config: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Relationships
    domains: Mapped[list[OrganizationDomain]] = relationship(
        "OrganizationDomain", back_populates="organization", cascade="all, delete-orphan"
    )
    memberships: Mapped[list[Membership]] = relationship(
        "Membership", back_populates="organization", cascade="all, delete-orphan"
    )


class OrganizationDomain(Base, TimestampMixin):
    """Verified domains associated with an organization."""

    __tablename__ = "organization_domains"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_join_policy: Mapped[str] = mapped_column(
        String(50), default="request_required", nullable=False
    )

    organization: Mapped[Organization] = relationship("Organization", back_populates="domains")


class Membership(Base, TimestampMixin):
    """Links a global UserAccount to an Organization with specific membership status."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization_membership"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    user: Mapped[UserAccount] = relationship("UserAccount", back_populates="memberships")  # noqa: F821
    organization: Mapped[Organization] = relationship("Organization", back_populates="memberships")
    roles: Mapped[list[RoleAssignment]] = relationship(
        "RoleAssignment", back_populates="membership", cascade="all, delete-orphan"
    )


class RoleAssignment(Base, TimestampMixin):
    """Roles granted to a user within an organization membership."""

    __tablename__ = "role_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    membership_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # STUDENT, TEACHER, PARENT, ORG_ADMIN, ACADEMIC_ADMIN
    scope: Mapped[str] = mapped_column(String(255), default="organization", nullable=False)

    membership: Mapped[Membership] = relationship("Membership", back_populates="roles")


class Invitation(Base, TimestampMixin):
    """Invitations sent to prospective members."""

    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    proposed_role: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class GuardianRelationship(Base, TimestampMixin):
    """Parent/Guardian link to a student learner."""

    __tablename__ = "guardian_relationships"
    __table_args__ = (UniqueConstraint("guardian_id", "student_id", name="uq_guardian_student"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    guardian_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
