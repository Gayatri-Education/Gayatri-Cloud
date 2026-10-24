"""Billing, Subscriptions, Entitlements and Institution Fees models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class SubscriptionPlan(Base, TimestampMixin):
    """Freemium subscription tier definitions with feature entitlements and limits."""

    __tablename__ = "subscription_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    billing_interval: Mapped[str] = mapped_column(
        String(20), default="monthly", nullable=False
    )  # monthly, yearly
    seat_limit: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    features_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Subscription(Base, TimestampMixin):
    """Active subscription status for a personal learner or institutional tenant."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False
    )  # active, past_due, canceled, trialing
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    plan: Mapped[SubscriptionPlan] = relationship("SubscriptionPlan")


class InstitutionFee(Base, TimestampMixin):
    """Institutional tuition, lab, or course fee schedules."""

    __tablename__ = "institution_fees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False
    )  # active, archived


class FeePayment(Base, TimestampMixin):
    """Payments made by students/guardians toward institution fees."""

    __tablename__ = "fee_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    fee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institution_fees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_paid_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, completed, refunded, failed
    payment_intent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    fee: Mapped[InstitutionFee] = relationship("InstitutionFee")


class PaymentTransaction(Base, TimestampMixin):
    """Immutable log of payment attempts, gateway references, and signature audits."""

    __tablename__ = "payment_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    gateway_provider: Mapped[str] = mapped_column(
        String(50), default="mock", nullable=False
    )  # mock, stripe_simulated
    gateway_transaction_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="succeeded", nullable=False
    )  # pending, succeeded, failed, refunded
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class InvoiceReceipt(Base, TimestampMixin):
    """Immutable accounting receipt generated upon successful transactions."""

    __tablename__ = "invoice_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("payment_transactions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    billing_details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    line_items_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    tax_amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    transaction: Mapped[PaymentTransaction] = relationship("PaymentTransaction")
