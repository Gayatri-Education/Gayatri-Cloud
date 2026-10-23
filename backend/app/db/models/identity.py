"""Identity and authentication database models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, generate_uuid


class UserAccount(Base, TimestampMixin, SoftDeleteMixin):
    """Global user account representing an individual learner or educator."""

    __tablename__ = "user_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    identities: Mapped[list[AuthIdentity]] = relationship(
        "AuthIdentity", back_populates="user", cascade="all, delete-orphan"
    )
    memberships: Mapped[list[Membership]] = relationship(  # noqa: F821
        "Membership", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list[SessionDevice]] = relationship(
        "SessionDevice", back_populates="user", cascade="all, delete-orphan"
    )


class AuthIdentity(Base, TimestampMixin):
    """Credentials and authentication providers linked to a user."""

    __tablename__ = "auth_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), default="email", nullable=False)
    credential_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped[UserAccount] = relationship("UserAccount", back_populates="identities")


class SessionDevice(Base, TimestampMixin):
    """Active sessions and refresh token tracking for security controls."""

    __tablename__ = "session_devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[UserAccount] = relationship("UserAccount", back_populates="sessions")
