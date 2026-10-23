"""Course and Version Lifecycle Domain Service."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext
from app.core.storage import get_storage_service, sanitize_filename, validate_file_content
from app.db.base import generate_uuid
from app.db.models.course import (
    ContentSource,
    Course,
    CourseEnrollment,
    CourseOffering,
    CourseVersion,
)
from app.db.models.identity import UserAccount
from app.db.models.organization import Membership, RoleAssignment

# --- Request & Response Schemas ---


class CreateCourseRequest(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    is_global: bool = False


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str | None
    code: str
    title: str
    description: str | None
    is_global: bool
    is_active: bool
    created_at: datetime


class CreateCourseVersionRequest(BaseModel):
    version_tag: str = Field(min_length=2, max_length=50)  # e.g., "v1.0.0"
    changelog: str | None = None


class CourseVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_id: str
    version_tag: str
    status: str
    changelog: str | None
    published_at: datetime | None
    created_at: datetime


class ContentSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_version_id: str
    filename: str
    mime_type: str
    file_size_bytes: int
    s3_uri: str
    checksum_sha256: str
    ingestion_status: str
    created_at: datetime


class CreateOfferingRequest(BaseModel):
    course_version_id: str
    term: str = Field(min_length=2, max_length=100)


class CourseOfferingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_version_id: str
    organization_id: str | None
    term: str
    status: str
    created_at: datetime


class EnrollStudentRequest(BaseModel):
    student_id: str


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    offering_id: str
    status: str
    created_at: datetime


# --- Domain Service ---


class CourseService:
    """Manages course catalogs, immutable versions, content sources, and offerings."""

    @staticmethod
    async def create_course(
        session: AsyncSession,
        context: TenantContext,
        req: CreateCourseRequest,
    ) -> Course:
        """Create a new course container, scoped to tenant or global for super admin."""
        if req.is_global:
            if not context.user.is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Platform Super Admins can create global courses.",
                )
            org_id = None
        else:
            org_id = context.organization_id

        course = Course(
            organization_id=org_id,
            code=req.code.strip(),
            title=req.title.strip(),
            description=req.description,
            is_global=req.is_global,
            is_active=True,
        )
        session.add(course)
        await session.flush()

        # Automatically create initial draft version "v1.0.0"
        initial_version = CourseVersion(
            course_id=course.id,
            version_tag="v1.0.0",
            status="draft",
            changelog="Initial course version",
        )
        session.add(initial_version)
        await session.commit()
        await session.refresh(course)
        return course

    @staticmethod
    async def list_courses(
        session: AsyncSession,
        context: TenantContext,
    ) -> list[Course]:
        """List courses visible to the user: organization-owned courses and global courses."""
        stmt = select(Course).where(
            (Course.organization_id == context.organization_id) | (Course.is_global.is_(True)),
            Course.is_active.is_(True),
            Course.deleted_at.is_(None),
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_course_or_404(
        session: AsyncSession,
        course_id: str,
        context: TenantContext,
    ) -> Course:
        """Fetch course ensuring organization boundary or global visibility."""
        stmt = select(Course).where(
            Course.id == course_id,
            Course.deleted_at.is_(None),
        )
        res = await session.execute(stmt)
        course = res.scalar_one_or_none()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course '{course_id}' not found.",
            )

        if not course.is_global and course.organization_id != context.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Course belongs to another organization.",
            )
        return course

    @staticmethod
    async def create_course_version(
        session: AsyncSession,
        context: TenantContext,
        course_id: str,
        req: CreateCourseVersionRequest,
    ) -> CourseVersion:
        """Create a new draft version for a course."""
        course = await CourseService.get_course_or_404(session, course_id, context)

        # Check for existing version tag
        v_stmt = select(CourseVersion).where(
            CourseVersion.course_id == course.id,
            CourseVersion.version_tag == req.version_tag.strip(),
        )
        existing = await session.execute(v_stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Version tag '{req.version_tag}' already exists for this course.",
            )

        version = CourseVersion(
            course_id=course.id,
            version_tag=req.version_tag.strip(),
            status="draft",
            changelog=req.changelog,
        )
        session.add(version)
        await session.commit()
        await session.refresh(version)
        return version

    @staticmethod
    async def list_course_versions(
        session: AsyncSession,
        course_id: str,
        context: TenantContext,
    ) -> list[CourseVersion]:
        """List all versions for a given course."""
        course = await CourseService.get_course_or_404(session, course_id, context)
        stmt = (
            select(CourseVersion)
            .where(CourseVersion.course_id == course.id)
            .order_by(CourseVersion.created_at.desc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def publish_course_version(
        session: AsyncSession,
        context: TenantContext,
        course_id: str,
        version_id: str,
    ) -> CourseVersion:
        """Transition course version from draft/in_review to published (locking immutability)."""
        await CourseService.get_course_or_404(session, course_id, context)

        stmt = select(CourseVersion).where(
            CourseVersion.id == version_id, CourseVersion.course_id == course_id
        )
        res = await session.execute(stmt)
        version = res.scalar_one_or_none()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course version not found.",
            )

        if version.status == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Version is already published.",
            )

        if version.status == "archived":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archived versions cannot be published.",
            )

        version.status = "published"
        version.published_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(version)
        return version

    @staticmethod
    async def upload_content_source(
        session: AsyncSession,
        context: TenantContext,
        course_id: str,
        version_id: str,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> ContentSource:
        """Upload curriculum content to private storage and associate with a draft version."""
        course = await CourseService.get_course_or_404(session, course_id, context)

        stmt = select(CourseVersion).where(
            CourseVersion.id == version_id, CourseVersion.course_id == course_id
        )
        res = await session.execute(stmt)
        version = res.scalar_one_or_none()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course version not found.",
            )

        # Invariant: Published versions are strictly immutable
        if version.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add sources to version with status '{version.status}'. Version is immutable; only 'draft' versions can be modified.",
            )

        # Content validation & sniff check
        try:
            validate_file_content(content, filename, mime_type)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err),
            ) from err

        # Calculate SHA-256 Checksum
        checksum = hashlib.sha256(content).hexdigest()
        source_id = generate_uuid()
        safe_name = sanitize_filename(filename)

        # Construct tenant-isolated storage path
        tenant_folder = course.organization_id or "global"
        storage_path = (
            f"{tenant_folder}/courses/{course.id}/{version.version_tag}/{source_id}/{safe_name}"
        )

        # Upload to Storage Service
        storage_service = get_storage_service()
        storage_uri = storage_service.upload_file(content, storage_path, mime_type)

        content_source = ContentSource(
            id=source_id,
            organization_id=course.organization_id,
            course_version_id=version.id,
            filename=safe_name,
            mime_type=mime_type,
            file_size_bytes=len(content),
            s3_uri=storage_uri,
            checksum_sha256=checksum,
            ingestion_status="pending",
        )
        session.add(content_source)
        await session.commit()
        await session.refresh(content_source)
        return content_source

    @staticmethod
    async def list_content_sources(
        session: AsyncSession,
        context: TenantContext,
        course_id: str,
        version_id: str,
    ) -> list[ContentSource]:
        """List content sources attached to a version."""
        await CourseService.get_course_or_404(session, course_id, context)
        stmt = (
            select(ContentSource)
            .where(ContentSource.course_version_id == version_id)
            .order_by(ContentSource.created_at.desc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_source_download_url(
        session: AsyncSession,
        context: TenantContext,
        course_id: str,
        version_id: str,
        source_id: str,
    ) -> str:
        """Generate authorized presigned download link for content source."""
        course = await CourseService.get_course_or_404(session, course_id, context)

        stmt = select(ContentSource).where(
            ContentSource.id == source_id, ContentSource.course_version_id == version_id
        )
        res = await session.execute(stmt)
        source = res.scalar_one_or_none()
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content source not found.",
            )

        if not course.is_global and source.organization_id != context.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Content source belongs to another organization.",
            )

        # Parse relative path from storage URI (e.g. "local://..." or "s3://...")
        storage_service = get_storage_service()
        if source.s3_uri.startswith("local://"):
            raw_path = source.s3_uri.replace("local://", "")
        elif source.s3_uri.startswith("s3://"):
            # strip s3://bucket/
            parts = source.s3_uri.split("/", 3)
            raw_path = parts[3] if len(parts) > 3 else ""
        else:
            raw_path = source.s3_uri

        return storage_service.generate_presigned_download_url(raw_path, expires_in_seconds=3600)

    @staticmethod
    async def create_course_offering(
        session: AsyncSession,
        context: TenantContext,
        req: CreateOfferingRequest,
    ) -> CourseOffering:
        """Create a course offering (term deployment) from an approved/published version."""
        v_stmt = select(CourseVersion).where(CourseVersion.id == req.course_version_id)
        v_res = await session.execute(v_stmt)
        version = v_res.scalar_one_or_none()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course version not found.",
            )

        # Invariant: Offerings can only be created from published course versions
        if version.status != "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deploy offering: Course version '{version.version_tag}' has status '{version.status}' (must be 'published').",
            )

        offering = CourseOffering(
            course_version_id=version.id,
            organization_id=context.organization_id,
            term=req.term.strip(),
            status="active",
        )
        session.add(offering)
        await session.commit()
        await session.refresh(offering)
        return offering

    @staticmethod
    async def enroll_student(
        session: AsyncSession,
        context: TenantContext,
        offering_id: str,
        student_id: str,
    ) -> CourseEnrollment:
        """Enroll a verified student of the organization into an active course offering."""
        o_stmt = select(CourseOffering).where(CourseOffering.id == offering_id)
        o_res = await session.execute(o_stmt)
        offering = o_res.scalar_one_or_none()
        if not offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course offering not found.",
            )

        if (
            offering.organization_id
            and offering.organization_id != context.organization_id
            and not context.user.is_super_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot enroll in an offering from another organization.",
            )

        # Verify student exists and is active member with STUDENT role
        user_stmt = select(UserAccount).where(UserAccount.id == student_id)
        user_res = await session.execute(user_stmt)
        student = user_res.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student user account not found.",
            )

        if offering.organization_id:
            mem_stmt = select(Membership).where(
                Membership.user_id == student_id,
                Membership.organization_id == offering.organization_id,
                Membership.status == "active",
            )
            mem = (await session.execute(mem_stmt)).scalar_one_or_none()
            if not mem:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student does not hold an active membership in this organization.",
                )

            role_stmt = select(RoleAssignment).where(
                RoleAssignment.membership_id == mem.id,
                RoleAssignment.role == "STUDENT",
            )
            role = (await session.execute(role_stmt)).scalar_one_or_none()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User does not have STUDENT role in this organization.",
                )

        # Check existing enrollment
        existing_stmt = select(CourseEnrollment).where(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.offering_id == offering_id,
        )
        existing = (await session.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student is already enrolled in this course offering.",
            )

        enrollment = CourseEnrollment(
            student_id=student_id,
            offering_id=offering_id,
            status="enrolled",
        )
        session.add(enrollment)
        await session.commit()
        await session.refresh(enrollment)
        return enrollment
