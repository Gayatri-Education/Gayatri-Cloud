"""Assessment, Evaluation, and Grading API Endpoints."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, resolve_tenant_context
from app.db.models.course import CourseOffering
from app.db.models.tutoring import Assessment, AssessmentAttempt, AssessmentResponse
from app.db.session import get_db
from app.domain.assessment.service import (
    AssessmentService,
    AutosaveAttemptRequest,
    CreateAssessmentRequest,
    SubmitAttemptRequest,
    TeacherOverrideRequest,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_assessment(
    req: CreateAssessmentRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new course assessment (Teacher or Admin only)."""
    service = AssessmentService(db)
    assessment = await service.create_assessment(context, req)
    return {
        "id": assessment.id,
        "offering_id": assessment.offering_id,
        "title": assessment.title,
        "assessment_type": assessment.assessment_type,
        "total_points": assessment.total_points,
        "time_limit_minutes": assessment.time_limit_minutes,
        "passing_score": assessment.passing_score,
        "is_published": assessment.is_published,
    }


@router.post("/{assessment_id}/publish")
async def publish_assessment(
    assessment_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Publish an assessment to make it available to enrolled students."""
    service = AssessmentService(db)
    assessment = await service.publish_assessment(context, assessment_id)
    return {
        "id": assessment.id,
        "title": assessment.title,
        "is_published": assessment.is_published,
    }


@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get assessment definition. Automatically strips protected answers/rubrics for students."""
    service = AssessmentService(db)
    return await service.get_assessment(context, assessment_id)


@router.post("/{assessment_id}/attempts", status_code=status.HTTP_201_CREATED)
async def start_attempt(
    assessment_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Start an assessment attempt for the current student."""
    service = AssessmentService(db)
    attempt = await service.start_attempt(context, assessment_id)
    return {
        "id": attempt.id,
        "assessment_id": attempt.assessment_id,
        "student_id": attempt.student_id,
        "status": attempt.status,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "time_limit_minutes": attempt.time_limit_minutes,
    }


@router.get("/attempts/{attempt_id}")
async def get_attempt(
    attempt_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve attempt status, draft answers, or finalized grading summary."""
    attempt = await db.get(AssessmentAttempt, attempt_id)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found.",
        )

    assessment = await db.get(Assessment, attempt.assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    offering = await db.get(CourseOffering, assessment.offering_id)
    if not offering:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offering not found.",
        )

    # Cross-tenant negative isolation check
    if (
        offering.organization_id
        and offering.organization_id != context.organization_id
        and not context.user.is_super_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to attempts from another organization.",
        )

    is_teacher_or_admin = context.has_role(
        RoleEnum.TEACHER.value, RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value
    )
    if not is_teacher_or_admin and attempt.student_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this attempt.",
        )

    # Fetch individual responses if graded
    stmt = select(AssessmentResponse).where(AssessmentResponse.attempt_id == attempt.id)
    res = await db.execute(stmt)
    responses = [
        {
            "id": r.id,
            "question_id": r.question_id,
            "student_response": r.student_response,
            "score": r.score,
            "max_score": r.max_score,
            "is_correct": r.is_correct,
            "feedback_text": r.feedback_text,
            "evaluated_by": r.evaluated_by,
            "teacher_override_score": r.teacher_override_score,
            "teacher_override_comment": r.teacher_override_comment,
        }
        for r in res.scalars().all()
    ]

    return {
        "id": attempt.id,
        "assessment_id": attempt.assessment_id,
        "student_id": attempt.student_id,
        "status": attempt.status,
        "total_score": attempt.total_score,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "draft_answers": json.loads(attempt.draft_answers_json or "{}"),
        "grading_summary": json.loads(attempt.grading_summary_json or "{}"),
        "responses": responses,
    }


@router.put("/attempts/{attempt_id}/autosave")
async def autosave_attempt(
    attempt_id: str,
    req: AutosaveAttemptRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Autosave draft answers for an active attempt."""
    service = AssessmentService(db)
    return await service.autosave_attempt(context, attempt_id, req.draft_answers)


@router.post("/attempts/{attempt_id}/submit")
async def submit_attempt(
    attempt_id: str,
    req: SubmitAttemptRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Submit attempt for evaluation and update canonical mastery."""
    service = AssessmentService(db)
    summary = await service.submit_attempt(context, attempt_id, req.answers, req.idempotency_key)
    return summary.to_dict()


@router.post("/attempts/{attempt_id}/override")
async def teacher_override(
    attempt_id: str,
    req: TeacherOverrideRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Teacher or admin manual override of question scores."""
    service = AssessmentService(db)
    attempt = await service.teacher_override(context, attempt_id, req)
    return {
        "id": attempt.id,
        "status": attempt.status,
        "total_score": attempt.total_score,
    }
