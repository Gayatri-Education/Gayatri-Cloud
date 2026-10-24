"""REST API endpoints for Parent and Guardian portal."""

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, require_roles
from app.db.session import get_db
from app.domain.parent.service import ParentService

router = APIRouter(prefix="/parent", tags=["Parent & Guardian Portal"])

# Dependency verifying parent or administrative roles
parent_auth = require_roles(
    RoleEnum.PARENT.value,
    RoleEnum.ORG_ADMIN.value,
    RoleEnum.SUPER_ADMIN.value,
)


class LinkStudentRequest(BaseModel):
    student_identifier: str = Field(..., description="Student account ID or email address")


@router.get(
    "/children",
    summary="List all linked children and their learning summaries",
)
async def list_linked_children(
    context: TenantContext = Depends(parent_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = ParentService(session)
    return await service.list_linked_children(context)


@router.post(
    "/link-request",
    status_code=status.HTTP_201_CREATED,
    summary="Request guardian link to a student learner",
)
async def request_student_link(
    req: LinkStudentRequest,
    context: TenantContext = Depends(parent_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = ParentService(session)
    rel = await service.request_link(context, req.student_identifier)
    return {
        "id": rel.id,
        "guardian_id": rel.guardian_id,
        "student_id": rel.student_id,
        "verification_status": rel.verification_status,
        "is_active": rel.is_active,
    }


@router.post(
    "/children/{relationship_id}/verify",
    summary="Verify and approve guardian relationship",
)
async def verify_guardian_link(
    relationship_id: str,
    context: TenantContext = Depends(parent_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = ParentService(session)
    rel = await service.verify_link(context, relationship_id)
    return {
        "id": rel.id,
        "verification_status": rel.verification_status,
        "is_active": rel.is_active,
    }


@router.delete(
    "/children/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Immediately revoke guardian relationship",
)
async def revoke_guardian_link(
    relationship_id: str,
    context: TenantContext = Depends(parent_auth),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = ParentService(session)
    await service.revoke_link(context, relationship_id)


@router.get(
    "/children/{student_id}/progress",
    summary="Get privacy-filtered learning progress for linked child",
)
async def get_child_learning_progress(
    student_id: str,
    context: TenantContext = Depends(parent_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = ParentService(session)
    return await service.get_child_progress(context, student_id)


@router.get(
    "/children/{student_id}/assessments",
    summary="Get assessment reports and feedback for linked child",
)
async def get_child_assessments(
    student_id: str,
    context: TenantContext = Depends(parent_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = ParentService(session)
    return await service.get_child_assessments(context, student_id)


@router.get(
    "/children/{student_id}/communications",
    summary="Get class announcements and school notices for linked child",
)
async def get_child_communications(
    student_id: str,
    context: TenantContext = Depends(parent_auth),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = ParentService(session)
    return await service.get_child_communications(context, student_id)
