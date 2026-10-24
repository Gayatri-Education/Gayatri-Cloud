"""API Version 1 Router definitions."""

from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.benchmarks import router as benchmarks_router
from app.api.v1.courses import router as course_router
from app.api.v1.organizations import router as org_router
from app.api.v1.rag import router as rag_router
from app.api.v1.tutoring import router as tutoring_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(org_router, prefix="/organizations", tags=["Organizations"])
api_v1_router.include_router(course_router, prefix="/courses", tags=["Courses"])
api_v1_router.include_router(rag_router, prefix="/rag", tags=["RAG"])
api_v1_router.include_router(ai_router, prefix="/ai", tags=["AI Gateway"])
api_v1_router.include_router(benchmarks_router, prefix="/benchmarks", tags=["Benchmarks & Routing"])
api_v1_router.include_router(tutoring_router, prefix="/tutoring", tags=["Tutoring & Mastery"])

__all__ = ["api_v1_router"]
