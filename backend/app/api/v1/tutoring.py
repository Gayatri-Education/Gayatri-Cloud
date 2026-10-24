"""Tutor Session, Dialogue Turns, and Teacher Directives Endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, require_roles, resolve_tenant_context
from app.db.models.course import TeacherInstruction
from app.db.session import get_db
from app.domain.tutoring.mastery import CanonicalMasteryService
from app.domain.tutoring.service import (
    CreateTeacherInstructionRequest,
    CreateTutorSessionRequest,
    PostTurnRequest,
    PostTurnResponse,
    TeacherInstructionResponse,
    TutorOrchestrator,
    TutorSessionResponse,
)

router = APIRouter()


@router.post(
    "/sessions",
    response_model=TutorSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an interactive tutoring dialogue session",
)
async def create_tutor_session(
    req: CreateTutorSessionRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> TutorSessionResponse:
    """Create a new session, validating student enrollment in the course offering."""
    tutor_session = await TutorOrchestrator.create_session(session, context, req)
    return TutorSessionResponse.model_validate(tutor_session)


@router.get(
    "/sessions/{session_id}",
    response_model=TutorSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tutor session details",
)
async def get_tutor_session(
    session_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> TutorSessionResponse:
    """Fetch tutoring session with learner ownership verification."""
    tutor_session = await TutorOrchestrator.get_session_or_404(session, context, session_id)
    return TutorSessionResponse.model_validate(tutor_session)


@router.post(
    "/sessions/{session_id}/turns",
    response_model=PostTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Post learner message and receive tutor response with citations and mastery updates",
)
async def post_dialogue_turn(
    session_id: str,
    req: PostTurnRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> PostTurnResponse:
    """Execute dialogue turn: RAG search, teacher hierarchy, model routing, and deterministic mastery."""
    return await TutorOrchestrator.process_turn(session, context, session_id, req)


@router.get(
    "/sessions/{session_id}/mastery",
    status_code=status.HTTP_200_OK,
    summary="Get student's concept mastery vector for session offering",
)
async def get_session_mastery(
    session_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Retrieve canonical mastery state scores for all concepts in the offering."""
    tutor_session = await TutorOrchestrator.get_session_or_404(session, context, session_id)
    states = await CanonicalMasteryService.get_student_mastery_matrix(
        session, tutor_session.student_id, tutor_session.offering_id
    )
    return [
        {
            "concept_id": s.concept_id,
            "mastery_score": s.mastery_score,
            "review_count": s.review_count,
            "stability": s.stability,
            "last_tested_at": s.last_tested_at,
        }
        for s in states
    ]


@router.post(
    "/instructions",
    response_model=TeacherInstructionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a teacher directive into the 5-tier instruction cascade",
)
async def create_instruction(
    req: CreateTeacherInstructionRequest,
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.TEACHER.value,
            RoleEnum.ACADEMIC_ADMIN.value,
            RoleEnum.ORG_ADMIN.value,
            RoleEnum.SUPER_ADMIN.value,
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> TeacherInstructionResponse:
    """Create teacher instruction influencing tutoring behavior across tiers (ORG, COURSE, CLASS, STUDENT, SESSION)."""
    inst = await TutorOrchestrator.create_teacher_instruction(session, context, req)
    return TeacherInstructionResponse.model_validate(inst)


@router.get(
    "/instructions",
    response_model=list[TeacherInstructionResponse],
    status_code=status.HTTP_200_OK,
    summary="List teacher directives for course in organization",
)
async def list_instructions(
    course_id: str = Query(...),
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[TeacherInstructionResponse]:
    """Retrieve active teacher instructions in the organization scope."""
    stmt = (
        select(TeacherInstruction)
        .where(
            TeacherInstruction.organization_id == context.organization_id,
            TeacherInstruction.course_id == course_id,
            TeacherInstruction.is_active.is_(True),
        )
        .order_by(TeacherInstruction.priority.desc())
    )
    res = await session.execute(stmt)
    return [TeacherInstructionResponse.model_validate(i) for i in res.scalars().all()]
