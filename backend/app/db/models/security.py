"""Security and Privacy Hardening Database Models."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, generate_uuid
from app.db.models.identity import UserAccount


class AccountDeletionRequest(Base, TimestampMixin):
    """Lifecycle tracking for GDPR/FERPA Right-to-be-Forgotten deletion requests."""

    __tablename__ = "account_deletion_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, completed, cancelled, rejected_legal_hold
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    grace_period_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    legal_hold_retained_records: Mapped[str | None] = mapped_column(Text, nullable=True)
    anonymized_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[UserAccount] = relationship("UserAccount")


class SecurityAuditLog(Base, TimestampMixin):
    """Immutable audit record of user-facing security and privacy events."""

    __tablename__ = "security_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # LOGIN, PASSWORD_CHANGE, EXPORT_DOWNLOAD, DELETION_REQUEST, DELETION_CANCEL, KEY_UPDATE
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
