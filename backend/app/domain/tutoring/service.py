"""Tutor Dialogue Orchestrator combining RAG, Pedagogical Hierarchy, and Mastery."""

from __future__ import annotations

import time
from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext
from app.db.base import generate_uuid
from app.db.models.course import (
    Course,
    CourseEnrollment,
    CourseOffering,
    CourseVersion,
    TeacherInstruction,
)
from app.db.models.tutoring import ConversationTurn, TutorSession
from app.domain.ai.adapters import AIGenerationRequest
from app.domain.ai.gateway import AIGateway
from app.domain.ai.router import IntelligentModelRouter, RoutingRequest
from app.domain.rag.retrieval import CourseRAGEngine
from app.domain.tutoring.mastery import CanonicalMasteryService
from app.domain.tutoring.pedagogy import PedagogicalPromptBuilder, TeacherInstructionCascade

# --- Schemas ---


class CreateTutorSessionRequest(BaseModel):
    offering_id: str
    tutoring_mode: str = "socratic"  # socratic, explain_first, practice_first, custom


class TutorSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    offering_id: str
    organization_id: str | None
    status: str
    tutoring_mode: str
    created_at: datetime


class ConversationTurnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    turn_number: int
    role: str
    message_text: str
    provider_model: str | None
    token_usage: int | None
    created_at: datetime


class PostTurnRequest(BaseModel):
    message_text: str = Field(min_length=1)
    concept_id: str | None = None
    is_validated_correct: bool | None = None
    diagnosed_misconception: str | None = None


class PostTurnResponse(BaseModel):
    user_turn: ConversationTurnResponse
    assistant_turn: ConversationTurnResponse
    citations: list[str]
    active_pedagogy: str
    mastery_state: dict | None = None


class CreateTeacherInstructionRequest(BaseModel):
    course_id: str
    tier: str = Field(description="ORG, COURSE, CLASS, STUDENT, SESSION")
    priority: int = Field(default=3, ge=1, le=5)
    directive_text: str = Field(min_length=3)
    class_group_id: str | None = None
    student_id: str | None = None
    expires_at: datetime | None = None


class TeacherInstructionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    teacher_id: str
    course_id: str
    tier: str
    priority: int
    directive_text: str
    is_active: bool
    expires_at: datetime | None
    created_at: datetime


# --- Domain Orchestrator ---


class TutorOrchestrator:
    """Coordinates dialogue turns, context assembly, RAG retrieval, and learning state."""

    @staticmethod
    async def create_session(
        session: AsyncSession,
        context: TenantContext,
        req: CreateTutorSessionRequest,
    ) -> TutorSession:
        """Initialize an active tutoring dialogue session, verifying enrollment."""
        # 1. Verify Offering
        o_stmt = select(CourseOffering).where(CourseOffering.id == req.offering_id)
        offering = (await session.execute(o_stmt)).scalar_one_or_none()
        if not offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course offering '{req.offering_id}' not found.",
            )

        # 2. Verify Student Enrollment (unless teacher or admin inspecting)
        is_student = context.has_role(RoleEnum.STUDENT.value)
        if is_student and not context.has_role(RoleEnum.TEACHER.value, RoleEnum.ORG_ADMIN.value):
            enr_stmt = select(CourseEnrollment).where(
                CourseEnrollment.student_id == context.user.id,
                CourseEnrollment.offering_id == offering.id,
                CourseEnrollment.status == "enrolled",
            )
            enrollment = (await session.execute(enr_stmt)).scalar_one_or_none()
            if not enrollment:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not enrolled in this course offering.",
                )

        tutor_session = TutorSession(
            id=generate_uuid(),
            student_id=context.user.id,
            offering_id=offering.id,
            organization_id=offering.organization_id or context.organization_id,
            status="active",
            tutoring_mode=req.tutoring_mode.lower(),
        )
        session.add(tutor_session)
        await session.commit()
        await session.refresh(tutor_session)
        return tutor_session

    @staticmethod
    async def get_session_or_404(
        session: AsyncSession,
        context: TenantContext,
        session_id: str,
    ) -> TutorSession:
        """Fetch session ensuring ownership and tenant boundary."""
        stmt = select(TutorSession).where(TutorSession.id == session_id)
        tutor_session = (await session.execute(stmt)).scalar_one_or_none()
        if not tutor_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutoring session '{session_id}' not found.",
            )

        is_owner = tutor_session.student_id == context.user.id
        is_teacher_or_admin = (
            tutor_session.organization_id == context.organization_id
            and context.has_role(
                RoleEnum.TEACHER.value, RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value
            )
        )
        if not (is_owner or is_teacher_or_admin or context.user.is_super_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access tutor session belonging to another learner or organization.",
            )
        return tutor_session

    @classmethod
    async def process_turn(
        cls,
        session: AsyncSession,
        context: TenantContext,
        session_id: str,
        req: PostTurnRequest,
    ) -> PostTurnResponse:
        """Execute complete multi-turn cycle: RAG search, teacher hierarchy, AI generation, turn audit, and mastery."""
        tutor_session = await cls.get_session_or_404(session, context, session_id)
        start_time = time.time()

        # 1. Fetch offering, course version, and course details
        offering_stmt = select(CourseOffering).where(CourseOffering.id == tutor_session.offering_id)
        offering = (await session.execute(offering_stmt)).scalar_one()

        v_stmt = select(CourseVersion).where(CourseVersion.id == offering.course_version_id)
        version = (await session.execute(v_stmt)).scalar_one()

        c_stmt = select(Course).where(Course.id == version.course_id)
        course = (await session.execute(c_stmt)).scalar_one()

        # 2. Determine Turn Sequence
        count_stmt = select(func.count(ConversationTurn.id)).where(
            ConversationTurn.session_id == tutor_session.id
        )
        existing_turn_count = (await session.execute(count_stmt)).scalar_one()
        user_turn_number = existing_turn_count + 1
        assistant_turn_number = existing_turn_count + 2

        # 3. Course-Scoped RAG Hybrid Retrieval
        rag_engine = CourseRAGEngine()
        org_scope = None if course.is_global else tutor_session.organization_id
        retrieved_chunks = await rag_engine.search(
            session=session,
            organization_id=org_scope,
            course_id=course.id,
            course_version_id=version.id,
            query=req.message_text,
            top_k=3,
        )

        # 4. Resolve Active Prioritized Teacher Directives
        teacher_instructions = await TeacherInstructionCascade.resolve_active_instructions(
            session=session,
            organization_id=tutor_session.organization_id,
            course_id=course.id,
            student_id=tutor_session.student_id,
        )

        # 5. Assemble Pedagogical System Prompt
        system_prompt = PedagogicalPromptBuilder.build_system_prompt(
            tutoring_mode=tutor_session.tutoring_mode,
            course_title=course.title,
            teacher_instructions=teacher_instructions,
            retrieved_chunks=retrieved_chunks,
        )

        # 6. Intelligent Model Routing
        route_decision = await IntelligentModelRouter.route(
            session=session,
            context=context,
            req=RoutingRequest(task_type="tutoring"),
        )

        # 7. Execute AI Generation via Gateway
        gen_req = AIGenerationRequest(
            prompt=req.message_text,
            system_prompt=system_prompt,
            model_id=route_decision.selected_model,
        )
        ai_res = await AIGateway.generate(session, context, gen_req)
        latency_ms = (time.time() - start_time) * 1000.0

        # 8. Persist User and Assistant Conversation Turns
        user_turn = ConversationTurn(
            id=generate_uuid(),
            session_id=tutor_session.id,
            turn_number=user_turn_number,
            role="user",
            message_text=req.message_text,
            token_usage=gen_req.prompt.count(" ") + 1,
        )
        assistant_turn = ConversationTurn(
            id=generate_uuid(),
            session_id=tutor_session.id,
            turn_number=assistant_turn_number,
            role="assistant",
            message_text=ai_res.content,
            provider_model=ai_res.model_id,
            latency_ms=round(latency_ms, 1),
            token_usage=ai_res.completion_tokens,
        )
        session.add(user_turn)
        session.add(assistant_turn)
        await session.commit()
        await session.refresh(user_turn)
        await session.refresh(assistant_turn)

        # 9. Deterministic Mastery Progression & Misconception Handling
        mastery_dict = None
        if req.concept_id:
            # Misconception logging
            if req.diagnosed_misconception:
                await CanonicalMasteryService.log_misconception(
                    session=session,
                    student_id=tutor_session.student_id,
                    offering_id=tutor_session.offering_id,
                    concept_id=req.concept_id,
                    description=req.diagnosed_misconception,
                )

            # Validated evidence check
            if req.is_validated_correct is not None:
                updated_state = await CanonicalMasteryService.record_evidence(
                    session=session,
                    student_id=tutor_session.student_id,
                    offering_id=tutor_session.offering_id,
                    concept_id=req.concept_id,
                    is_correct=req.is_validated_correct,
                    event_type="dialogue_turn_evidence",
                )
                mastery_dict = {
                    "concept_id": updated_state.concept_id,
                    "mastery_score": updated_state.mastery_score,
                    "review_count": updated_state.review_count,
                    "stability": updated_state.stability,
                }

        citations = [c.citation for c in retrieved_chunks]
        return PostTurnResponse(
            user_turn=ConversationTurnResponse.model_validate(user_turn),
            assistant_turn=ConversationTurnResponse.model_validate(assistant_turn),
            citations=citations,
            active_pedagogy=tutor_session.tutoring_mode,
            mastery_state=mastery_dict,
        )

    @staticmethod
    async def create_teacher_instruction(
        session: AsyncSession,
        context: TenantContext,
        req: CreateTeacherInstructionRequest,
    ) -> TeacherInstruction:
        """Create a new teacher directive within the authorized organization."""
        valid_tiers = {"ORG", "COURSE", "CLASS", "STUDENT", "SESSION"}
        tier_upper = req.tier.upper()
        if tier_upper not in valid_tiers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tier '{req.tier}'. Allowed: {list(valid_tiers)}",
            )

        inst = TeacherInstruction(
            id=generate_uuid(),
            organization_id=context.organization_id,
            teacher_id=context.user.id,
            course_id=req.course_id,
            tier=tier_upper,
            priority=req.priority,
            directive_text=req.directive_text.strip(),
            class_group_id=req.class_group_id,
            student_id=req.student_id,
            is_active=True,
            expires_at=req.expires_at,
        )
        session.add(inst)
        await session.commit()
        await session.refresh(inst)
        return inst
