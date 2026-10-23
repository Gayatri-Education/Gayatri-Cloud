"""Ingestion orchestrator processing raw sources into indexed curriculum chunks."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext
from app.core.storage import get_storage_service
from app.db.base import generate_uuid
from app.db.models.course import ContentChunk, ContentSource, CourseVersion
from app.domain.course import CourseService
from app.domain.ingestion.chunker import ContentChunker
from app.domain.ingestion.extractors import get_extractor_for_mime


class IngestionService:
    """Processes ContentSource documents into indexed ContentChunks."""

    @staticmethod
    async def ingest_course_version(
        session: AsyncSession,
        context: TenantContext,
        course_id: str,
        version_id: str,
    ) -> dict[str, int]:
        """Process all pending sources for the specified course version."""
        await CourseService.get_course_or_404(session, course_id, context)

        v_stmt = select(CourseVersion).where(
            CourseVersion.id == version_id, CourseVersion.course_id == course_id
        )
        version = (await session.execute(v_stmt)).scalar_one_or_none()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course version not found.",
            )

        # Retrieve sources for this version
        s_stmt = select(ContentSource).where(ContentSource.course_version_id == version.id)
        sources = list((await session.execute(s_stmt)).scalars().all())

        if not sources:
            return {"processed_sources": 0, "total_chunks_indexed": 0}

        storage_service = get_storage_service()
        chunker = ContentChunker()
        total_chunks_created = 0
        processed_sources = 0

        for source in sources:
            # Mark status processing
            source.ingestion_status = "processing"
            await session.commit()

            try:
                # Read binary file from storage
                if source.s3_uri.startswith("local://"):
                    raw_path = source.s3_uri.replace("local://", "")
                elif source.s3_uri.startswith("s3://"):
                    parts = source.s3_uri.split("/", 3)
                    raw_path = parts[3] if len(parts) > 3 else ""
                else:
                    raw_path = source.s3_uri

                file_bytes = storage_service.download_file(raw_path)

                # Extract sections based on MIME type
                extractor = get_extractor_for_mime(source.mime_type)
                sections = extractor.extract(file_bytes)

                # Generate chunks
                chunk_payloads = chunker.chunk_sections(sections)

                # Delete existing chunks for this source if re-indexing
                await session.execute(
                    delete(ContentChunk).where(ContentChunk.source_id == source.id)
                )

                for cp in chunk_payloads:
                    db_chunk = ContentChunk(
                        id=generate_uuid(),
                        source_id=source.id,
                        chunk_index=cp.chunk_index,
                        text_content=cp.text_content,
                        page_number=cp.page_number,
                        section_header=cp.section_header,
                        token_count=cp.token_count,
                    )
                    session.add(db_chunk)
                    total_chunks_created += 1

                source.ingestion_status = "indexed"
                processed_sources += 1
                await session.commit()

            except Exception as err:
                source.ingestion_status = "failed"
                await session.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to ingest source '{source.filename}': {err}",
                ) from err

        return {
            "processed_sources": processed_sources,
            "total_chunks_indexed": total_chunks_created,
        }
