"""Offline Course Bundle Packager and Staleness Detector.
Provides portable, version-pinned lesson bundles for cached offline reading.
Computes SHA-256 checksums and strictly flags staleness when online updates occur (RQ-030, DEC-C20).
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext
from app.db.models.course import ContentChunk, ContentSource, Course, CourseVersion

logger = logging.getLogger(__name__)


class OfflineService:
    """Service generating portable offline reading bundles and detecting version staleness."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def package_course_bundle(
        self,
        context: TenantContext,
        course_id: str,
    ) -> dict[str, Any]:
        """Bundle published course version and content chunks into an offline reading package."""
        # 1. Fetch course with tenant boundary check
        stmt = select(Course).where(Course.id == course_id)
        res = await self.session.execute(stmt)
        course = res.scalar_one_or_none()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course '{course_id}' not found.",
            )

        # Cross-tenant check: if course has an org, caller must match or be super admin
        if course.organization_id and context.organization_id != course.organization_id:
            if "SUPER_ADMIN" not in context.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-tenant course access denied.",
                )

        # 2. Get active published version
        v_stmt = (
            select(CourseVersion)
            .where(
                CourseVersion.course_id == course_id,
                CourseVersion.status == "published",
            )
            .order_by(CourseVersion.created_at.desc(), CourseVersion.version_tag.desc())
            .limit(1)
        )
        v_res = await self.session.execute(v_stmt)
        version = v_res.scalars().first()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No published course version available for offline reading.",
            )

        # 3. Get content chunks for this version joined through ContentSource
        chunk_stmt = (
            select(ContentChunk)
            .join(ContentSource, ContentChunk.source_id == ContentSource.id)
            .where(ContentSource.course_version_id == version.id)
            .order_by(ContentChunk.chunk_index.asc())
        )
        chunk_res = await self.session.execute(chunk_stmt)
        chunks = chunk_res.scalars().all()

        lessons_data = [
            {
                "chunk_id": c.id,
                "title": c.section_header or f"Lesson Section {c.chunk_index + 1}",
                "content_text": c.text_content,
                "sequence_order": c.chunk_index,
                "token_count": c.token_count,
            }
            for c in chunks
        ]

        now = datetime.now(UTC)
        payload_for_hashing = json.dumps(
            {
                "course_id": course.id,
                "version_id": version.id,
                "version_tag": version.version_tag,
                "lessons": lessons_data,
            },
            sort_keys=True,
        )
        sha256_hash = hashlib.sha256(payload_for_hashing.encode("utf-8")).hexdigest()

        return {
            "course_id": course.id,
            "course_title": course.title,
            "description": course.description,
            "version_id": version.id,
            "version_tag": version.version_tag,
            "sha256_checksum": sha256_hash,
            "packaged_at": now.isoformat(),
            "lessons_count": len(lessons_data),
            "lessons": lessons_data,
            "offline_guidance": "Reading mode active. Live AI tutoring and graded exams require reconnection.",
        }

    async def check_bundle_staleness(
        self,
        course_id: str,
        local_version_tag: str,
        local_hash: str | None = None,
    ) -> dict[str, Any]:
        """Check if local cached bundle is outdated compared to active published version."""
        v_stmt = (
            select(CourseVersion)
            .where(
                CourseVersion.course_id == course_id,
                CourseVersion.status == "published",
            )
            .order_by(CourseVersion.created_at.desc(), CourseVersion.version_tag.desc())
            .limit(1)
        )
        v_res = await self.session.execute(v_stmt)
        latest_version = v_res.scalars().first()

        if not latest_version:
            return {
                "is_stale": False,
                "status": "up_to_date",
                "message": "No newer version published.",
            }

        is_stale = latest_version.version_tag != local_version_tag

        return {
            "course_id": course_id,
            "local_version_tag": local_version_tag,
            "latest_version_tag": latest_version.version_tag,
            "is_stale": is_stale,
            "status": "stale" if is_stale else "up_to_date",
            "message": (
                f"Course version {latest_version.version_tag} is available online."
                if is_stale
                else "Cached version is current."
            ),
        }
