"""REST API endpoints for Localization, Language Preferences, and Offline Course Reading."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext, resolve_optional_tenant_context
from app.db.session import get_db
from app.domain.i18n.offline import OfflineService
from app.domain.i18n.registry import TranslationRegistry

router = APIRouter(prefix="/localization", tags=["Localization & Accessibility"])


class UpdateLanguagePreferenceRequest(BaseModel):
    language_code: str = Field(
        ..., min_length=2, max_length=5, description="en, hi, sa, ta, te, kn, mr, bn"
    )


class CheckStalenessRequest(BaseModel):
    course_id: str
    local_version_tag: str
    local_hash: str | None = None


# =============================================================================
# 1. Languages & Catalogs
# =============================================================================


@router.get("/languages", summary="List the 8 supported platform languages")
async def list_languages() -> list[dict[str, str]]:
    return TranslationRegistry.get_supported_languages()


@router.get("/translations/{lang_code}", summary="Get translation catalog for language code")
async def get_translations(lang_code: str) -> dict[str, str]:
    return TranslationRegistry.get_catalog(lang_code)


@router.get("/preference", summary="Get user language preference")
async def get_user_language_preference(
    context: TenantContext = Depends(resolve_optional_tenant_context),
) -> dict[str, str]:
    pref = TranslationRegistry.get_user_language(context.user.id)
    return {"language_code": pref}


@router.put("/preference", summary="Update user language preference")
async def update_user_language_preference(
    req: UpdateLanguagePreferenceRequest,
    context: TenantContext = Depends(resolve_optional_tenant_context),
) -> dict[str, str]:
    updated = TranslationRegistry.set_user_language(context.user.id, req.language_code)
    return {"language_code": updated}


# =============================================================================
# 2. Offline Reading Bundles & Staleness Detection
# =============================================================================


@router.get("/offline/bundle/{course_id}", summary="Download offline reading package for a course")
async def download_offline_bundle(
    course_id: str,
    context: TenantContext = Depends(resolve_optional_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = OfflineService(session)
    return await service.package_course_bundle(context, course_id)


@router.post("/offline/check-stale", summary="Check if locally cached course bundle is stale")
async def check_bundle_staleness(
    req: CheckStalenessRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = OfflineService(session)
    return await service.check_bundle_staleness(
        course_id=req.course_id,
        local_version_tag=req.local_version_tag,
        local_hash=req.local_hash,
    )
