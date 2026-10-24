"""Application Events, Outbox, Archival, and Training Dataset models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, generate_uuid


class ApplicationEvent(Base, TimestampMixin):
    """Immutable audit trail of domain and operational occurrences."""

    __tablename__ = "application_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensitivity_level: Mapped[str] = mapped_column(
        String(50), default="PROTECTED", nullable=False
    )  # PUBLIC, INTERNAL, PROTECTED, RESTRICTED
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class EventOutbox(Base, TimestampMixin):
    """Transactional outbox ensuring durable event dispatching to S3 and workers."""

    __tablename__ = "event_outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("application_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False, index=True
    )  # pending, archived, failed, quarantined
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EventArchiveBatch(Base, TimestampMixin):
    """Immutable archive batches persisted to private S3 prefixes."""

    __tablename__ = "event_archive_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    batch_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)


class TrainingEligibilityRecord(Base, TimestampMixin):
    """Independent governance record regulating model training eligibility (deny-by-default)."""

    __tablename__ = "training_eligibility_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("application_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), default="NOT_REVIEWED", nullable=False, index=True
    )  # NOT_REVIEWED, ELIGIBLE, EXCLUDED, REDACTION_REQUIRED
    authorization_basis: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # EXPLICIT_CONSENT, INSTITUTION_POLICY, OWNER_APPROVED
    purpose_scope: Mapped[str] = mapped_column(
        String(100), default="GENERAL_MODEL_TRAINING", nullable=False
    )
    exclusion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    pii_redacted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TrainingDatasetExport(Base, TimestampMixin):
    """Reproducible dataset export manifest with split counts and human sign-off gating."""

    __tablename__ = "training_dataset_exports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    version_tag: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    total_examples: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    train_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    val_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    test_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
