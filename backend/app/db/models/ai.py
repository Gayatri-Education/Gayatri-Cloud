"""AI Gateway, Provider Credentials, and Usage models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, generate_uuid


class ProviderConnection(Base, TimestampMixin):
    """Encrypted reference to an AI provider credential (BYOK or Org)."""

    __tablename__ = "provider_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # openai, gemini, anthropic, openrouter, custom
    encrypted_key_ciphertext: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # AES-256-GCM encrypted
    key_fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # SHA-256 for identification
    custom_endpoint_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProviderModelSnapshot(Base, TimestampMixin):
    """Discovered models and capability metadata."""

    __tablename__ = "provider_model_snapshots"
    __table_args__ = (UniqueConstraint("provider_type", "model_id", name="uq_provider_model"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    context_window_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_tools: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModelPolicy(Base, TimestampMixin):
    """Routing rules, default models, and cost ceilings."""

    __tablename__ = "model_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(
        String(100), default="general", nullable=False
    )  # tutoring, assessment, general, embedding
    default_provider: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)
    default_model: Mapped[str] = mapped_column(String(100), default="mock-tutor", nullable=False)
    fallback_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fallback_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    max_tokens_per_call: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    allowed_models_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="*")
    routing_strategy: Mapped[str] = mapped_column(
        String(50), default="quality_first", nullable=False
    )


class AIExecutionUsage(Base, TimestampMixin):
    """Audit log of tokens consumed and estimated costs for billing and quotas."""

    __tablename__ = "ai_execution_usages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tutor_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class ModelBenchmarkRun(Base, TimestampMixin):
    """Execution of a standardized educational benchmark evaluating model quality and eligibility."""

    __tablename__ = "model_benchmark_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    benchmark_suite_version: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 100.0
    pedagogical_score: Mapped[float] = mapped_column(Float, nullable=False)
    factual_accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    safety_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evaluation_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
