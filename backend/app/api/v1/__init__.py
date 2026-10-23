"""API Version 1 Router definitions."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.courses import router as course_router
from app.api.v1.organizations import router as org_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(org_router, prefix="/organizations", tags=["Organizations"])
api_v1_router.include_router(course_router, prefix="/courses", tags=["Courses"])

__all__ = ["api_v1_router"]
