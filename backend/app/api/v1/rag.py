"""RAG Ingestion and Course-Scoped Retrieval Endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, require_roles, resolve_tenant_context
from app.db.session import get_db
from app.domain.course import CourseService
from app.domain.ingestion.service import IngestionService
from app.domain.rag.retrieval import CourseRAGEngine, RAGQueryRequest, RAGQueryResponse

router = APIRouter()


@router.post(
    "/courses/{course_id}/versions/{version_id}/ingest",
    status_code=status.HTTP_200_OK,
    summary="Trigger ingestion and indexing of course curriculum sources",
)
async def ingest_course_sources(
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
) -> dict[str, int | str]:
    """Extract, sanitize, chunk, and index all uploaded sources for the course version."""
    result = await IngestionService.ingest_course_version(session, context, course_id, version_id)
    return {
        "status": "ok",
        "course_version_id": version_id,
        **result,
    }


@router.post(
    "/courses/{course_id}/versions/{version_id}/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute course-scoped hybrid RAG search with citation traces",
)
async def query_course_rag(
    course_id: str,
    version_id: str,
    req: RAGQueryRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> RAGQueryResponse:
    """Retrieve relevant chunks and citations strictly scoped to course version and tenant boundary."""
    # Validate course ownership
    course = await CourseService.get_course_or_404(session, course_id, context)

    engine = CourseRAGEngine()
    org_scope = None if course.is_global else context.organization_id

    results = await engine.search(
        session=session,
        organization_id=org_scope,
        course_id=course.id,
        course_version_id=version_id,
        query=req.query,
        top_k=req.top_k,
        alpha=req.alpha,
    )

    formatted_results = [
        {
            "chunk_id": r.chunk_id,
            "source_id": r.source_id,
            "source_filename": r.source_filename,
            "text_content": r.text_content,
            "page_number": r.page_number,
            "section_header": r.section_header,
            "relevance_score": r.relevance_score,
            "citation": r.citation,
        }
        for r in results
    ]

    return RAGQueryResponse(
        query=req.query,
        course_version_id=version_id,
        retrieved_count=len(formatted_results),
        results=formatted_results,
    )
