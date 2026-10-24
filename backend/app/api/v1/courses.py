"""Course, Version Lifecycle, and Content Source Management Endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import (
    RoleEnum,
    TenantContext,
    require_roles,
    resolve_optional_tenant_context,
    resolve_tenant_context,
)
from app.db.session import get_db
from app.domain.course import (
    ContentSourceResponse,
    CourseOfferingResponse,
    CourseResponse,
    CourseService,
    CourseVersionResponse,
    CreateCourseRequest,
    CreateCourseVersionRequest,
    CreateOfferingRequest,
    EnrollmentResponse,
    EnrollStudentRequest,
)

router = APIRouter()


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course container",
)
async def create_course(
    req: CreateCourseRequest,
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.ORG_ADMIN.value,
            RoleEnum.ACADEMIC_ADMIN.value,
            RoleEnum.TEACHER.value,
            RoleEnum.SUPER_ADMIN.value,
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> CourseResponse:
    """Create a course within the active tenant organization or global scope."""
    course = await CourseService.create_course(session, context, req)
    return CourseResponse.model_validate(course)


@router.get(
    "",
    response_model=list[CourseResponse],
    status_code=status.HTTP_200_OK,
    summary="List courses for active organization and global catalog",
)
async def list_courses(
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[CourseResponse]:
    """Retrieve all active courses for the tenant and platform global courses."""
    courses = await CourseService.list_courses(session, context)
    return [CourseResponse.model_validate(c) for c in courses]


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get course details",
)
async def get_course(
    course_id: str,
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> CourseResponse:
    """Retrieve course metadata ensuring tenant boundary."""
    course = await CourseService.get_course_or_404(session, course_id, context)
    return CourseResponse.model_validate(course)


@router.post(
    "/{course_id}/versions",
    response_model=CourseVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft version for a course",
)
async def create_course_version(
    course_id: str,
    req: CreateCourseVersionRequest,
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.ORG_ADMIN.value,
            RoleEnum.ACADEMIC_ADMIN.value,
            RoleEnum.TEACHER.value,
            RoleEnum.SUPER_ADMIN.value,
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> CourseVersionResponse:
    """Create a new version snapshot in draft state."""
    version = await CourseService.create_course_version(session, context, course_id, req)
    return CourseVersionResponse.model_validate(version)


@router.get(
    "/{course_id}/versions",
    response_model=list[CourseVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="List versions for a course",
)
async def list_course_versions(
    course_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[CourseVersionResponse]:
    """List all version snapshots for the course."""
    versions = await CourseService.list_course_versions(session, course_id, context)
    return [CourseVersionResponse.model_validate(v) for v in versions]


@router.post(
    "/{course_id}/versions/{version_id}/publish",
    response_model=CourseVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish a course version snapshot (locks immutability)",
)
async def publish_course_version(
    course_id: str,
    version_id: str,
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.ORG_ADMIN.value,
            RoleEnum.ACADEMIC_ADMIN.value,
            RoleEnum.TEACHER.value,
            RoleEnum.SUPER_ADMIN.value,
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> CourseVersionResponse:
    """Publish a draft course version. Once published, the curriculum and sources become immutable."""
    version = await CourseService.publish_course_version(session, context, course_id, version_id)
    return CourseVersionResponse.model_validate(version)


@router.post(
    "/{course_id}/versions/{version_id}/sources",
    response_model=ContentSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload curriculum content source into private storage",
)
async def upload_source(
    course_id: str,
    version_id: str,
    file: UploadFile = File(...),
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.ORG_ADMIN.value,
            RoleEnum.ACADEMIC_ADMIN.value,
            RoleEnum.TEACHER.value,
            RoleEnum.SUPER_ADMIN.value,
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> ContentSourceResponse:
    """Upload and validate document/media source for a draft course version."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename must be provided.")

    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    source = await CourseService.upload_content_source(
        session=session,
        context=context,
        course_id=course_id,
        version_id=version_id,
        filename=file.filename,
        content=content,
        mime_type=content_type,
    )
    return ContentSourceResponse.model_validate(source)


@router.get(
    "/{course_id}/versions/{version_id}/sources",
    response_model=list[ContentSourceResponse],
    status_code=status.HTTP_200_OK,
    summary="List curriculum sources for a version",
)
async def list_sources(
    course_id: str,
    version_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[ContentSourceResponse]:
    """Retrieve metadata of all content sources belonging to the course version."""
    sources = await CourseService.list_content_sources(session, context, course_id, version_id)
    return [ContentSourceResponse.model_validate(s) for s in sources]


@router.get(
    "/{course_id}/versions/{version_id}/sources/{source_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Generate authorized download URL for private content source",
)
async def get_source_download(
    course_id: str,
    version_id: str,
    source_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Return short-lived presigned download URL with tenant access verification."""
    url = await CourseService.get_source_download_url(
        session, context, course_id, version_id, source_id
    )
    return {"download_url": url}


@router.post(
    "/offerings",
    response_model=CourseOfferingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy offering from published course version",
)
async def create_offering(
    req: CreateOfferingRequest,
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.ORG_ADMIN.value,
            RoleEnum.ACADEMIC_ADMIN.value,
            RoleEnum.TEACHER.value,
            RoleEnum.SUPER_ADMIN.value,
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> CourseOfferingResponse:
    """Create a term/cohort offering from an approved and published course version."""
    offering = await CourseService.create_course_offering(session, context, req)
    return CourseOfferingResponse.model_validate(offering)


@router.post(
    "/offerings/{offering_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll student into course offering",
)
async def enroll_student(
    offering_id: str,
    req: EnrollStudentRequest,
    context: TenantContext = Depends(
        require_roles(
            RoleEnum.ORG_ADMIN.value,
            RoleEnum.ACADEMIC_ADMIN.value,
            RoleEnum.TEACHER.value,
            RoleEnum.SUPER_ADMIN.value,
        )
    ),
    session: AsyncSession = Depends(get_db),
) -> EnrollmentResponse:
    """Enroll an active organization student into an active course offering."""
    enrollment = await CourseService.enroll_student(session, context, offering_id, req.student_id)
    return EnrollmentResponse.model_validate(enrollment)
