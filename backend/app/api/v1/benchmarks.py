"""Tutoring Benchmark and Model Routing Endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, require_roles, resolve_tenant_context
from app.db.models.ai import ModelBenchmarkRun
from app.db.session import get_db
from app.domain.ai.router import IntelligentModelRouter, RoutingDecision, RoutingRequest
from app.domain.benchmarks.evaluator import BenchmarkEvaluator

router = APIRouter()


class BenchmarkRunRequest(BaseModel):
    provider_type: str = "mock"
    model_id: str = "mock-tutor-standard"


class BenchmarkRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    benchmark_suite_version: str
    provider_type: str
    model_id: str
    composite_score: float
    pedagogical_score: float
    factual_accuracy_score: float
    safety_score: float
    is_eligible: bool
    evaluated_at: datetime


@router.post(
    "/run",
    response_model=BenchmarkRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute educational tutoring benchmark suite on a model",
)
async def run_benchmark(
    req: BenchmarkRunRequest,
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.ORG_ADMIN.value,
            RoleEnum.ACADEMIC_ADMIN.value,
            RoleEnum.SUPER_ADMIN.value,
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> BenchmarkRunResponse:
    """Run standardized pedagogical benchmark suite and record score and eligibility."""
    run = await BenchmarkEvaluator.evaluate_model(
        session=session,
        provider_type=req.provider_type,
        model_id=req.model_id,
    )
    return BenchmarkRunResponse.model_validate(run)


@router.get(
    "/runs",
    response_model=list[BenchmarkRunResponse],
    status_code=status.HTTP_200_OK,
    summary="List historical model benchmark evaluations",
)
async def list_benchmark_runs(
    provider_type: str | None = Query(None),
    is_eligible: bool | None = Query(None),
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[BenchmarkRunResponse]:
    """Retrieve benchmark scoreboards and eligibility records."""
    stmt = select(ModelBenchmarkRun).order_by(ModelBenchmarkRun.evaluated_at.desc())
    if provider_type:
        stmt = stmt.where(ModelBenchmarkRun.provider_type == provider_type.lower())
    if is_eligible is not None:
        stmt = stmt.where(ModelBenchmarkRun.is_eligible == is_eligible)

    res = await session.execute(stmt)
    runs = list(res.scalars().all())
    return [BenchmarkRunResponse.model_validate(r) for r in runs]


@router.post(
    "/route",
    response_model=RoutingDecision,
    status_code=status.HTTP_200_OK,
    summary="Resolve intelligent quality-first model route for task",
)
async def route_task(
    req: RoutingRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> RoutingDecision:
    """Select the highest-quality eligible model matching task requirements or process manual override."""
    return await IntelligentModelRouter.route(session, context, req)
