"""REST API endpoints for Billing, Subscriptions, Entitlements and Institution Fees."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import (
    RoleEnum,
    TenantContext,
    require_roles,
    resolve_optional_tenant_context,
)
from app.db.session import get_db
from app.domain.billing.service import BillingService

router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])


# =============================================================================
# Request Schemas
# =============================================================================


class SubscribeRequest(BaseModel):
    plan_code: str = Field(
        ..., description="free, pro_learner, institution_standard, institution_enterprise"
    )
    idempotency_key: str = Field(..., min_length=8, max_length=100)


class CreateInstitutionFeeRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field("", max_length=1000)
    amount_cents: int = Field(..., gt=0, description="Amount in currency smallest units (cents)")
    currency: str = Field("USD", min_length=3, max_length=3)
    due_date: datetime | None = None


class PayFeeRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=8, max_length=100)
    student_id: str | None = None


# =============================================================================
# 1. Plans & Subscriptions
# =============================================================================


@router.get("/plans", summary="List available subscription plans and entitlements")
async def list_plans(
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = BillingService(session)
    return await service.list_plans()


@router.get("/subscription", summary="Get active subscription and entitlements")
async def get_subscription(
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = BillingService(session)
    return await service.get_active_subscription(context)


@router.post("/subscribe", summary="Subscribe or change plan tier with idempotency guard")
async def subscribe(
    req: SubscribeRequest,
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = BillingService(session)
    return await service.subscribe(context, req.plan_code, req.idempotency_key)


@router.post("/cancel", summary="Cancel subscription at period end")
async def cancel_subscription(
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = BillingService(session)
    return await service.cancel_subscription(context)


# =============================================================================
# 2. Institutional Fees & Student Collections
# =============================================================================


@router.get("/institution/fees", summary="List institution fees (Admin/Teacher)")
async def list_institution_fees(
    organization_id: str = Query(...),
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = BillingService(session)
    return await service.list_institution_fees(context, organization_id)


@router.post(
    "/institution/fees",
    status_code=status.HTTP_201_CREATED,
    summary="Create institutional fee schedule (Org Admin only)",
)
async def create_institution_fee(
    req: CreateInstitutionFeeRequest,
    organization_id: str = Query(...),
    context: TenantContext = Depends(
        require_roles(RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value)
    ),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = BillingService(session)
    return await service.create_institution_fee(
        context=context,
        org_id=organization_id,
        title=req.title,
        description=req.description,
        amount_cents=req.amount_cents,
        currency=req.currency,
        due_date=req.due_date,
    )


@router.get("/student/fees", summary="List payable fees for current learner or linked child")
async def list_student_fees(
    student_id: str | None = Query(None),
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = BillingService(session)
    return await service.list_student_fees(context, student_id)


@router.post("/student/fees/{fee_id}/pay", summary="Pay student fee with idempotency guard")
async def pay_student_fee(
    fee_id: str,
    req: PayFeeRequest,
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = BillingService(session)
    return await service.pay_student_fee(
        context=context,
        fee_id=fee_id,
        idempotency_key=req.idempotency_key,
        student_id=req.student_id,
    )


# =============================================================================
# 3. Webhooks (Cryptographically Verified & Idempotent)
# =============================================================================


@router.post("/webhook", summary="Cryptographically verified payment gateway webhook")
async def payment_webhook(
    request: Request,
    x_signature: str | None = Header(None, alias="X-Signature"),
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    raw_body = await request.body()
    sig = x_signature or stripe_signature or ""
    if not sig:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing webhook signature header.",
        )

    service = BillingService(session)
    return await service.process_webhook(raw_body, sig)


# =============================================================================
# 4. Invoices & Receipts
# =============================================================================


@router.get("/invoices", summary="List past invoices and immutable receipts")
async def list_invoices(
    organization_id: str | None = Query(None),
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = BillingService(session)
    return await service.list_invoices(context, organization_id)
