"""REST API endpoints for Teacher and Academic Administration."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, require_roles
from app.db.session import get_db
from app.domain.teacher.service import TeacherService

router = APIRouter(prefix="/teacher", tags=["Teacher & Academic Administration"])

# Dependency verifying teacher or academic administrator roles
teacher_auth = require_roles(
    RoleEnum.TEACHER.value,
    RoleEnum.ACADEMIC_ADMIN.value,
    RoleEnum.ORG_ADMIN.value,
    RoleEnum.SUPER_ADMIN.value,
)


# Request & Response Schemas
class EnrollStudentRequest(BaseModel):
    student_id: str


class CreateInstructionRequest(BaseModel):
    course_id: str
    tier: str = Field(..., description="ORG, COURSE, CLASS, STUDENT, SESSION")
    directive_text: str
    student_id: str | None = None
    class_group_id: str | None = None
    priority: int = Field(1, ge=1, le=100)
    expires_at: datetime | None = None


class AcknowledgeInterventionRequest(BaseModel):
    resolution_notes: str | None = None
    resolve: bool = False


class CreateAnnouncementRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    content: str = Field(..., min_length=1)


# =============================================================================
# 1. Class Roster & Enrollment
# =============================================================================


@router.get(
    "/offerings/{offering_id}/roster",
    summary="Get class roster with student mastery summaries",
)
async def get_class_roster(
    offering_id: str,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = TeacherService(session)
    return await service.get_roster(context, offering_id)


@router.post(
    "/offerings/{offering_id}/enroll",
    status_code=status.HTTP_201_CREATED,
    summary="Enroll student into course offering",
)
async def enroll_student(
    offering_id: str,
    req: EnrollStudentRequest,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = TeacherService(session)
    enrollment = await service.enroll_student(context, offering_id, req.student_id)
    return {
        "id": enrollment.id,
        "offering_id": enrollment.offering_id,
        "student_id": enrollment.student_id,
        "status": enrollment.status,
        "enrolled_at": enrollment.created_at.isoformat(),
    }


@router.delete(
    "/offerings/{offering_id}/enroll/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unenroll student from course offering",
)
async def unenroll_student(
    offering_id: str,
    student_id: str,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = TeacherService(session)
    await service.unenroll_student(context, offering_id, student_id)


# =============================================================================
# 2. Class Analytics & Cohort Mastery
# =============================================================================


@router.get(
    "/offerings/{offering_id}/analytics",
    summary="Get cohort mastery distribution, hardest concepts, and misconception clusters",
)
async def get_class_analytics(
    offering_id: str,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = TeacherService(session)
    return await service.get_class_analytics(context, offering_id)


# =============================================================================
# 3. Intervention Queue
# =============================================================================


@router.get(
    "/offerings/{offering_id}/interventions",
    summary="Get active learner intervention queue for class",
)
async def get_intervention_queue(
    offering_id: str,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = TeacherService(session)
    return await service.get_intervention_queue(context, offering_id)


@router.post(
    "/interventions/{intervention_id}/acknowledge",
    summary="Acknowledge or resolve student intervention",
)
async def acknowledge_intervention(
    intervention_id: str,
    req: AcknowledgeInterventionRequest,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = TeacherService(session)
    interv = await service.acknowledge_intervention(
        context, intervention_id, req.resolution_notes, req.resolve
    )
    return {
        "id": interv.id,
        "status": interv.status,
        "acknowledged_by": interv.acknowledged_by,
        "acknowledged_at": interv.acknowledged_at.isoformat() if interv.acknowledged_at else None,
        "resolution_notes": interv.resolution_notes,
    }


# =============================================================================
# 4. Teacher Copilot Briefings
# =============================================================================


@router.get(
    "/offerings/{offering_id}/copilot-briefing",
    summary="Generate empirical, data-grounded instructional briefing",
)
async def get_copilot_briefing(
    offering_id: str,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = TeacherService(session)
    return await service.generate_copilot_briefing(context, offering_id)


# =============================================================================
# 5. Teacher Directive Cascade Management
# =============================================================================


@router.post(
    "/instructions",
    status_code=status.HTTP_201_CREATED,
    summary="Register teacher instruction into cascade",
)
async def create_instruction(
    req: CreateInstructionRequest,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = TeacherService(session)
    inst = await service.create_instruction(
        context,
        course_id=req.course_id,
        tier=req.tier,
        directive_text=req.directive_text,
        student_id=req.student_id,
        class_group_id=req.class_group_id,
        priority=req.priority,
        expires_at=req.expires_at,
    )
    return {
        "id": inst.id,
        "course_id": inst.course_id,
        "tier": inst.tier,
        "directive_text": inst.directive_text,
        "priority": inst.priority,
        "is_active": inst.is_active,
        "created_at": inst.created_at.isoformat(),
    }


@router.get(
    "/instructions",
    summary="List active teacher directives ordered by priority",
)
async def list_instructions(
    course_id: str = Query(...),
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = TeacherService(session)
    instructions = await service.list_instructions(context, course_id)
    return [
        {
            "id": i.id,
            "course_id": i.course_id,
            "tier": i.tier,
            "directive_text": i.directive_text,
            "priority": i.priority,
            "is_active": i.is_active,
            "created_at": i.created_at.isoformat(),
        }
        for i in instructions
    ]


@router.delete(
    "/instructions/{instruction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate teacher directive",
)
async def deactivate_instruction(
    instruction_id: str,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = TeacherService(session)
    await service.deactivate_instruction(context, instruction_id)


# =============================================================================
# 6. Announcements
# =============================================================================


@router.post(
    "/offerings/{offering_id}/announcements",
    status_code=status.HTTP_201_CREATED,
    summary="Post class announcement",
)
async def create_announcement(
    offering_id: str,
    req: CreateAnnouncementRequest,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = TeacherService(session)
    ann = await service.create_announcement(context, offering_id, req.title, req.content)
    return {
        "id": ann.id,
        "offering_id": ann.offering_id,
        "title": ann.title,
        "content": ann.content,
        "created_at": ann.created_at.isoformat(),
    }


@router.get(
    "/offerings/{offering_id}/announcements",
    summary="List announcements for offering",
)
async def get_announcements(
    offering_id: str,
    context: TenantContext = Depends(teacher_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = TeacherService(session)
    announcements = await service.get_announcements(context, offering_id)
    return [
        {
            "id": a.id,
            "offering_id": a.offering_id,
            "title": a.title,
            "content": a.content,
            "created_at": a.created_at.isoformat(),
        }
        for a in announcements
    ]
