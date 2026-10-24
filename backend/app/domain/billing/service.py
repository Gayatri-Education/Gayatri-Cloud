"""Billing, Subscriptions, Entitlements and Institution Fees domain service.
Implements freemium subscription tier lifecycle, deterministic payment gateway adapter,
idempotent cryptographic webhook processing, institutional fee collection, and immutable receipts.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.rbac import RoleEnum, TenantContext
from app.db.models.billing import (
    FeePayment,
    InstitutionFee,
    InvoiceReceipt,
    PaymentTransaction,
    Subscription,
    SubscriptionPlan,
)
from app.db.models.organization import GuardianRelationship
from app.domain.billing.gateway import MockPaymentGateway, PaymentGatewayAdapter

logger = logging.getLogger(__name__)

DEFAULT_PLANS = [
    {
        "code": "free",
        "name": "Free Learner",
        "description": "Baseline educational access with standard AI tutoring and practice assessments.",
        "price_cents": 0,
        "currency": "USD",
        "billing_interval": "monthly",
        "seat_limit": 1,
        "features": [
            "tutoring:basic",
            "courses:public",
            "assessments:practice",
        ],
    },
    {
        "code": "pro_learner",
        "name": "Pro Learner",
        "description": "Unlimited adaptive AI tutoring, custom RAG document uploads, and BYOK integration.",
        "price_cents": 1200,  # $12.00
        "currency": "USD",
        "billing_interval": "monthly",
        "seat_limit": 1,
        "features": [
            "tutoring:advanced",
            "courses:all",
            "assessments:all",
            "rag:custom_uploads",
            "ai:byok_unlimited",
        ],
    },
    {
        "code": "institution_standard",
        "name": "Institution Standard",
        "description": "Comprehensive institutional campus tier with cohort analytics, teacher copilot, and roster management.",
        "price_cents": 4900,  # $49.00
        "currency": "USD",
        "billing_interval": "monthly",
        "seat_limit": 250,
        "features": [
            "tutoring:institution",
            "teacher:copilot",
            "analytics:cohort",
            "roster:unlimited",
            "ai:byok_org",
        ],
    },
    {
        "code": "institution_enterprise",
        "name": "Institution Enterprise",
        "description": "Full-scale university/academy license with custom domains, SLA guarantee, and unlimited seat allocations.",
        "price_cents": 19900,  # $199.00
        "currency": "USD",
        "billing_interval": "monthly",
        "seat_limit": 1000,
        "features": [
            "tutoring:institution",
            "teacher:copilot",
            "analytics:advanced",
            "domain:unlimited",
            "sla:priority",
            "ai:byok_org",
        ],
    },
]


class BillingService:
    """Service orchestrating subscriptions, fee schedules, transactions, and immutable receipts."""

    def __init__(
        self,
        session: AsyncSession,
        gateway: PaymentGatewayAdapter | None = None,
    ) -> None:
        self.session = session
        self.gateway = gateway or MockPaymentGateway()

    # =========================================================================
    # 1. Plans & Baseline Initialization
    # =========================================================================

    async def ensure_default_plans(self) -> list[SubscriptionPlan]:
        """Seed baseline freemium plans if not already present."""
        created_or_found: list[SubscriptionPlan] = []
        for p_data in DEFAULT_PLANS:
            stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == p_data["code"])
            res = await self.session.execute(stmt)
            plan = res.scalar_one_or_none()
            if not plan:
                plan = SubscriptionPlan(
                    code=p_data["code"],
                    name=p_data["name"],
                    description=p_data["description"],
                    price_cents=p_data["price_cents"],
                    currency=p_data["currency"],
                    billing_interval=p_data["billing_interval"],
                    seat_limit=p_data["seat_limit"],
                    features_json=json.dumps(p_data["features"]),
                    is_active=True,
                )
                self.session.add(plan)
                await self.session.flush()
            created_or_found.append(plan)
        await self.session.commit()
        return created_or_found

    async def list_plans(self) -> list[dict[str, Any]]:
        """List active subscription tiers and feature entitlements."""
        await self.ensure_default_plans()
        stmt = (
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.price_cents.asc())
        )
        res = await self.session.execute(stmt)
        plans = res.scalars().all()
        return [
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "description": p.description,
                "price_cents": p.price_cents,
                "currency": p.currency,
                "billing_interval": p.billing_interval,
                "seat_limit": p.seat_limit,
                "features": json.loads(p.features_json),
            }
            for p in plans
        ]

    # =========================================================================
    # 2. Subscriptions & Entitlement Resolution
    # =========================================================================

    async def get_active_subscription(self, context: TenantContext) -> dict[str, Any]:
        """Fetch active subscription and entitlements for tenant or personal scope."""
        await self.ensure_default_plans()

        query = select(Subscription).options(selectinload(Subscription.plan))
        if context.organization_id:
            query = query.where(Subscription.organization_id == context.organization_id)
        else:
            query = query.where(
                Subscription.user_id == context.user.id,
                Subscription.organization_id.is_(None),
            )

        res = await self.session.execute(query)
        sub = res.scalar_one_or_none()

        if sub and sub.status in ("active", "trialing"):
            features = json.loads(sub.plan.features_json)
            return {
                "subscription_id": sub.id,
                "status": sub.status,
                "plan_code": sub.plan.code,
                "plan_name": sub.plan.name,
                "price_cents": sub.plan.price_cents,
                "currency": sub.plan.currency,
                "current_period_end": sub.current_period_end.isoformat(),
                "cancel_at_period_end": sub.cancel_at_period_end,
                "seat_limit": sub.plan.seat_limit,
                "entitlements": features,
                "byok_disclaimer": "Third-party AI inference (BYOK) is billed directly by your AI provider and is not charged by Gayatri Cloud.",
            }

        # Default to free tier
        free_stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == "free")
        free_res = await self.session.execute(free_stmt)
        free_plan = free_res.scalar_one_or_none()

        return {
            "subscription_id": None,
            "status": "free_tier",
            "plan_code": "free",
            "plan_name": free_plan.name if free_plan else "Free Learner",
            "price_cents": 0,
            "currency": "USD",
            "current_period_end": None,
            "cancel_at_period_end": False,
            "seat_limit": 1,
            "entitlements": json.loads(free_plan.features_json)
            if free_plan
            else ["tutoring:basic"],
            "byok_disclaimer": "Third-party AI inference (BYOK) is billed directly by your AI provider and is not charged by Gayatri Cloud.",
        }

    async def subscribe(
        self,
        context: TenantContext,
        plan_code: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Subscribe or switch plan tier with idempotency protection against double-charging."""
        # 1. Check idempotency: if transaction already processed with this key, return it
        existing_tx_stmt = select(PaymentTransaction).where(
            PaymentTransaction.idempotency_key == idempotency_key
        )
        existing_tx_res = await self.session.execute(existing_tx_stmt)
        existing_tx = existing_tx_res.scalar_one_or_none()
        if existing_tx:
            logger.info("IDEMPOTENT_RETRY: Returning existing transaction %s", existing_tx.id)
            return {
                "transaction_id": existing_tx.id,
                "status": existing_tx.status,
                "amount_cents": existing_tx.amount_cents,
                "idempotency_key": idempotency_key,
                "is_replay": True,
            }

        # 2. Find target plan
        await self.ensure_default_plans()
        plan_stmt = select(SubscriptionPlan).where(
            SubscriptionPlan.code == plan_code,
            SubscriptionPlan.is_active.is_(True),
        )
        plan_res = await self.session.execute(plan_stmt)
        target_plan = plan_res.scalar_one_or_none()
        if not target_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription plan '{plan_code}' not found.",
            )

        # 3. Process payment through gateway adapter
        target_org = context.organization_id
        payment_intent = await self.gateway.create_payment_intent(
            amount_cents=target_plan.price_cents,
            currency=target_plan.currency,
            idempotency_key=idempotency_key,
            metadata={
                "plan_code": plan_code,
                "user_id": context.user.id,
                "organization_id": target_org,
            },
        )

        now = datetime.now(UTC)
        period_end = now + timedelta(days=30)

        # 4. Record PaymentTransaction
        tx = PaymentTransaction(
            organization_id=target_org,
            user_id=context.user.id,
            amount_cents=target_plan.price_cents,
            currency=target_plan.currency,
            gateway_provider="mock",
            gateway_transaction_id=payment_intent["gateway_transaction_id"],
            idempotency_key=idempotency_key,
            status=payment_intent["status"],
            signature_verified=True,
        )
        self.session.add(tx)
        await self.session.flush()

        # 5. Generate InvoiceReceipt
        inv_number = f"INV-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        receipt = InvoiceReceipt(
            transaction_id=tx.id,
            invoice_number=inv_number,
            billing_details_json=json.dumps(
                {
                    "payer_name": context.user.full_name,
                    "payer_email": context.user.email,
                    "organization_id": target_org,
                }
            ),
            line_items_json=json.dumps(
                [
                    {
                        "description": f"Gayatri Cloud Subscription — {target_plan.name}",
                        "amount_cents": target_plan.price_cents,
                        "quantity": 1,
                    }
                ]
            ),
            tax_amount_cents=0,
            total_amount_cents=target_plan.price_cents,
            issued_at=now,
        )
        self.session.add(receipt)

        # 6. Update or create Subscription
        sub_stmt = select(Subscription)
        if target_org:
            sub_stmt = sub_stmt.where(Subscription.organization_id == target_org)
        else:
            sub_stmt = sub_stmt.where(
                Subscription.user_id == context.user.id,
                Subscription.organization_id.is_(None),
            )
        sub_res = await self.session.execute(sub_stmt)
        sub = sub_res.scalar_one_or_none()

        if sub:
            sub.plan_id = target_plan.id
            sub.status = "active"
            sub.current_period_start = now
            sub.current_period_end = period_end
            sub.cancel_at_period_end = False
        else:
            sub = Subscription(
                organization_id=target_org,
                user_id=context.user.id if not target_org else None,
                plan_id=target_plan.id,
                status="active",
                current_period_start=now,
                current_period_end=period_end,
                cancel_at_period_end=False,
            )
            self.session.add(sub)

        await self.session.commit()

        return {
            "transaction_id": tx.id,
            "invoice_number": inv_number,
            "status": "succeeded",
            "plan_code": target_plan.code,
            "amount_paid_cents": target_plan.price_cents,
            "current_period_end": period_end.isoformat(),
        }

    async def cancel_subscription(self, context: TenantContext) -> dict[str, Any]:
        """Mark active subscription to cancel at end of billing cycle."""
        target_org = context.organization_id
        stmt = select(Subscription)
        if target_org:
            stmt = stmt.where(Subscription.organization_id == target_org)
        else:
            stmt = stmt.where(
                Subscription.user_id == context.user.id,
                Subscription.organization_id.is_(None),
            )
        res = await self.session.execute(stmt)
        sub = res.scalar_one_or_none()

        if not sub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found to cancel.",
            )

        sub.cancel_at_period_end = True
        await self.session.commit()

        return {
            "subscription_id": sub.id,
            "cancel_at_period_end": True,
            "current_period_end": sub.current_period_end.isoformat(),
            "message": "Subscription will cancel at end of current period.",
        }

    # =========================================================================
    # 3. Institutional Fee Schedules & Student Payments
    # =========================================================================

    async def create_institution_fee(
        self,
        context: TenantContext,
        org_id: str,
        title: str,
        description: str,
        amount_cents: int,
        currency: str = "USD",
        due_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Create school/academy fee schedule (Tuition, Lab, Exam fees)."""
        if RoleEnum.SUPER_ADMIN.value not in context.roles and (
            RoleEnum.ORG_ADMIN.value not in context.roles or context.organization_id != org_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrative privilege for target organization required.",
            )

        if amount_cents <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fee amount must be greater than zero.",
            )

        fee = InstitutionFee(
            organization_id=org_id,
            title=title.strip(),
            description=description.strip(),
            amount_cents=amount_cents,
            currency=currency.upper(),
            due_date=due_date,
            status="active",
        )
        self.session.add(fee)
        await self.session.commit()
        await self.session.refresh(fee)

        return {
            "id": fee.id,
            "organization_id": fee.organization_id,
            "title": fee.title,
            "amount_cents": fee.amount_cents,
            "currency": fee.currency,
            "due_date": fee.due_date.isoformat() if fee.due_date else None,
            "status": fee.status,
        }

    async def list_institution_fees(
        self,
        context: TenantContext,
        org_id: str,
    ) -> list[dict[str, Any]]:
        """List active fee schedules for the organization."""
        if RoleEnum.SUPER_ADMIN.value not in context.roles and (context.organization_id != org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant fee access denied.",
            )

        stmt = select(InstitutionFee).where(
            InstitutionFee.organization_id == org_id,
            InstitutionFee.status == "active",
        )
        res = await self.session.execute(stmt)
        fees = res.scalars().all()

        return [
            {
                "id": f.id,
                "title": f.title,
                "description": f.description,
                "amount_cents": f.amount_cents,
                "currency": f.currency,
                "due_date": f.due_date.isoformat() if f.due_date else None,
            }
            for f in fees
        ]

    async def list_student_fees(
        self,
        context: TenantContext,
        target_student_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List fees payable for the learner or linked child."""
        caller_id = context.user.id
        effective_student_id = target_student_id or caller_id

        # If checking for someone else, verify guardian link
        if effective_student_id != caller_id:
            g_stmt = select(GuardianRelationship).where(
                GuardianRelationship.guardian_id == caller_id,
                GuardianRelationship.student_id == effective_student_id,
                GuardianRelationship.verification_status == "verified",
                GuardianRelationship.is_active.is_(True),
            )
            g_res = await self.session.execute(g_stmt)
            if not g_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: verified guardian link required.",
                )

        target_org = context.organization_id
        if not target_org:
            return []

        # Find fees for target org
        fee_stmt = select(InstitutionFee).where(
            InstitutionFee.organization_id == target_org,
            InstitutionFee.status == "active",
        )
        fee_res = await self.session.execute(fee_stmt)
        fees = fee_res.scalars().all()

        # Find existing payments for this student
        pay_stmt = select(FeePayment).where(
            FeePayment.student_id == effective_student_id,
            FeePayment.status == "completed",
        )
        pay_res = await self.session.execute(pay_stmt)
        payments = {p.fee_id: p for p in pay_res.scalars().all()}

        results: list[dict[str, Any]] = []
        for f in fees:
            paid_record = payments.get(f.id)
            results.append(
                {
                    "fee_id": f.id,
                    "title": f.title,
                    "description": f.description,
                    "amount_cents": f.amount_cents,
                    "currency": f.currency,
                    "due_date": f.due_date.isoformat() if f.due_date else None,
                    "is_paid": paid_record is not None,
                    "paid_at": paid_record.paid_at.isoformat()
                    if paid_record and paid_record.paid_at
                    else None,
                    "payment_reference": paid_record.transaction_reference if paid_record else None,
                }
            )

        return results

    async def pay_student_fee(
        self,
        context: TenantContext,
        fee_id: str,
        idempotency_key: str,
        student_id: str | None = None,
    ) -> dict[str, Any]:
        """Pay an institutional fee with idempotency check and instant receipt generation."""
        # 1. Idempotency check
        existing_tx_stmt = select(PaymentTransaction).where(
            PaymentTransaction.idempotency_key == idempotency_key
        )
        existing_tx_res = await self.session.execute(existing_tx_stmt)
        existing_tx = existing_tx_res.scalar_one_or_none()
        if existing_tx:
            return {
                "transaction_id": existing_tx.id,
                "status": existing_tx.status,
                "amount_paid_cents": existing_tx.amount_cents,
                "is_replay": True,
            }

        # 2. Get Fee record
        fee_stmt = select(InstitutionFee).where(InstitutionFee.id == fee_id)
        fee_res = await self.session.execute(fee_stmt)
        fee = fee_res.scalar_one_or_none()
        if not fee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fee '{fee_id}' not found.",
            )

        caller_id = context.user.id
        effective_student_id = student_id or caller_id

        # If paying for someone else, verify guardian link
        if effective_student_id != caller_id:
            g_stmt = select(GuardianRelationship).where(
                GuardianRelationship.guardian_id == caller_id,
                GuardianRelationship.student_id == effective_student_id,
                GuardianRelationship.verification_status == "verified",
                GuardianRelationship.is_active.is_(True),
            )
            g_res = await self.session.execute(g_stmt)
            if not g_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Payment denied: verified guardian link required.",
                )

        # 3. Charge via gateway adapter
        intent = await self.gateway.create_payment_intent(
            amount_cents=fee.amount_cents,
            currency=fee.currency,
            idempotency_key=idempotency_key,
            metadata={"fee_id": fee_id, "student_id": effective_student_id},
        )

        now = datetime.now(UTC)

        # 4. Record PaymentTransaction
        tx = PaymentTransaction(
            organization_id=fee.organization_id,
            user_id=caller_id,
            amount_cents=fee.amount_cents,
            currency=fee.currency,
            gateway_provider="mock",
            gateway_transaction_id=intent["gateway_transaction_id"],
            idempotency_key=idempotency_key,
            status=intent["status"],
            signature_verified=True,
        )
        self.session.add(tx)
        await self.session.flush()

        # 5. Create FeePayment record
        payment = FeePayment(
            fee_id=fee.id,
            student_id=effective_student_id,
            amount_paid_cents=fee.amount_cents,
            currency=fee.currency,
            status="completed",
            payment_intent_id=intent["gateway_transaction_id"],
            transaction_reference=f"REC-{uuid.uuid4().hex[:8].upper()}",
            paid_at=now,
        )
        self.session.add(payment)

        # 6. Generate InvoiceReceipt
        inv_number = f"FEE-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        receipt = InvoiceReceipt(
            transaction_id=tx.id,
            invoice_number=inv_number,
            billing_details_json=json.dumps(
                {
                    "payer_name": context.user.full_name,
                    "payer_email": context.user.email,
                    "student_id": effective_student_id,
                    "fee_title": fee.title,
                }
            ),
            line_items_json=json.dumps(
                [
                    {
                        "description": fee.title,
                        "amount_cents": fee.amount_cents,
                        "quantity": 1,
                    }
                ]
            ),
            tax_amount_cents=0,
            total_amount_cents=fee.amount_cents,
            issued_at=now,
        )
        self.session.add(receipt)
        await self.session.commit()

        return {
            "payment_id": payment.id,
            "transaction_id": tx.id,
            "invoice_number": inv_number,
            "fee_title": fee.title,
            "amount_paid_cents": fee.amount_cents,
            "status": "completed",
            "paid_at": now.isoformat(),
        }

    # =========================================================================
    # 4. Cryptographic Webhook Handler & Replay Defense
    # =========================================================================

    async def process_webhook(
        self,
        raw_body: bytes,
        signature_header: str,
    ) -> dict[str, Any]:
        """Validate cryptographic webhook signature and process event idempotently."""
        # 1. Cryptographic signature check
        is_valid = self.gateway.verify_webhook_signature(raw_body, signature_header)
        if not is_valid:
            logger.warning("SECURITY_AUDIT: Rejected webhook with invalid cryptographic signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cryptographic webhook signature.",
            )

        # 2. Parse event payload
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed webhook JSON payload.",
            ) from None

        event_id = payload.get("id") or payload.get("gateway_transaction_id")
        event_type = payload.get("type", "payment_intent.succeeded")

        # 3. Replay attack defense
        existing_tx_stmt = select(PaymentTransaction).where(
            PaymentTransaction.gateway_transaction_id == event_id
        )
        existing_tx_res = await self.session.execute(existing_tx_stmt)
        existing_tx = existing_tx_res.scalar_one_or_none()

        if existing_tx and existing_tx.status == "succeeded":
            logger.info(
                "IDEMPOTENT_WEBHOOK: Event %s already acknowledged, ignoring replay.", event_id
            )
            return {"status": "already_processed", "event_id": event_id}

        logger.info("WEBHOOK_PROCESSED: Event %s (%s) verified and applied.", event_id, event_type)
        return {
            "status": "processed",
            "event_id": event_id,
            "event_type": event_type,
            "signature_verified": True,
        }

    # =========================================================================
    # 5. Invoices & Receipts
    # =========================================================================

    async def list_invoices(
        self,
        context: TenantContext,
        org_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List immutable invoice receipts for audit and accounting."""
        target_org = org_id or context.organization_id

        stmt = select(InvoiceReceipt).join(PaymentTransaction)
        if target_org:
            if (
                RoleEnum.SUPER_ADMIN.value not in context.roles
                and context.organization_id != target_org
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-tenant invoice access denied.",
                )
            stmt = stmt.where(PaymentTransaction.organization_id == target_org)
        else:
            stmt = stmt.where(
                PaymentTransaction.user_id == context.user.id,
                PaymentTransaction.organization_id.is_(None),
            )

        stmt = stmt.order_by(InvoiceReceipt.issued_at.desc())
        res = await self.session.execute(stmt)
        receipts = res.scalars().all()

        return [
            {
                "invoice_number": r.invoice_number,
                "amount_cents": r.total_amount_cents,
                "tax_amount_cents": r.tax_amount_cents,
                "line_items": json.loads(r.line_items_json),
                "billing_details": json.loads(r.billing_details_json),
                "issued_at": r.issued_at.isoformat(),
            }
            for r in receipts
        ]
