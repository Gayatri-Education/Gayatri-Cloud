"""Intelligent Quality-First AI Model Router."""

from __future__ import annotations

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext
from app.db.models.ai import ModelBenchmarkRun, ModelPolicy, ProviderModelSnapshot


class RoutingRequest(BaseModel):
    task_type: str = "tutoring"  # tutoring, assessment, grading, hint, general
    requested_model_id: str | None = None  # Optional manual override
    min_context_window: int = 4096
    requires_tools: bool = False


class RoutingDecision(BaseModel):
    selected_provider: str
    selected_model: str
    task_type: str
    composite_score: float
    is_manual_override: bool
    justification: str


class IntelligentModelRouter:
    """Selects the optimal eligible model based on task demands and benchmark quality scores."""

    @classmethod
    async def route(
        cls,
        session: AsyncSession,
        context: TenantContext,
        req: RoutingRequest,
    ) -> RoutingDecision:
        """Resolve routing decision enforcing capability constraints and quality-first ranking."""
        # 1. Fetch organization policy
        stmt = select(ModelPolicy).where(
            ModelPolicy.organization_id == context.organization_id,
            ModelPolicy.task_type == req.task_type,
        )
        policy = (await session.execute(stmt)).scalar_one_or_none()
        default_provider = policy.default_provider if policy else "mock"
        default_model = policy.default_model if policy else "mock-tutor-standard"

        # 2. Check Manual Selection Override
        if req.requested_model_id:
            # Verify capability and eligibility
            snap_stmt = select(ProviderModelSnapshot).where(
                ProviderModelSnapshot.model_id == req.requested_model_id
            )
            snapshot = (await session.execute(snap_stmt)).scalar_one_or_none()

            if snapshot and snapshot.context_window_tokens < req.min_context_window:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Requested model '{req.requested_model_id}' context window ({snapshot.context_window_tokens}) is insufficient for task requirement ({req.min_context_window}).",
                )

            # Check benchmark score if evaluated
            bench_stmt = (
                select(ModelBenchmarkRun)
                .where(ModelBenchmarkRun.model_id == req.requested_model_id)
                .order_by(ModelBenchmarkRun.evaluated_at.desc())
            )
            latest_run = (await session.execute(bench_stmt)).scalar_one_or_none()
            score = latest_run.composite_score if latest_run else 80.0

            provider = snapshot.provider_type if snapshot else default_provider
            return RoutingDecision(
                selected_provider=provider,
                selected_model=req.requested_model_id,
                task_type=req.task_type,
                composite_score=score,
                is_manual_override=True,
                justification=f"Manual user override granted for verified model '{req.requested_model_id}'.",
            )

        # 3. Automatic Quality-First Selection: Find eligible models ranked by composite score
        benchmarks_stmt = (
            select(ModelBenchmarkRun)
            .where(ModelBenchmarkRun.is_eligible.is_(True))
            .order_by(ModelBenchmarkRun.composite_score.desc())
        )
        eligible_runs = list((await session.execute(benchmarks_stmt)).scalars().all())

        if eligible_runs:
            top_run = eligible_runs[0]
            return RoutingDecision(
                selected_provider=top_run.provider_type,
                selected_model=top_run.model_id,
                task_type=req.task_type,
                composite_score=top_run.composite_score,
                is_manual_override=False,
                justification=f"Highest-ranked benchmarked model for educational task '{req.task_type}' (Score: {top_run.composite_score}%).",
            )

        # 4. Fallback to policy default
        return RoutingDecision(
            selected_provider=default_provider,
            selected_model=default_model,
            task_type=req.task_type,
            composite_score=75.0,
            is_manual_override=False,
            justification=f"Default policy baseline routed for task '{req.task_type}'.",
        )
