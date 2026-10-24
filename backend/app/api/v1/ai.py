"""AI Provider Gateway, Credential Vault, and Model Catalog Endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext, resolve_tenant_context
from app.db.session import get_db
from app.domain.ai.adapters import AIGenerationRequest, AIGenerationResponse
from app.domain.ai.gateway import AIGateway
from app.domain.ai.service import (
    AIService,
    CreateProviderConnectionRequest,
    ProviderConnectionResponse,
    ProviderModelSnapshotResponse,
)

router = APIRouter()


@router.post(
    "/connections",
    response_model=ProviderConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an encrypted AI provider credential (BYOK or Org)",
)
async def create_provider_connection(
    req: CreateProviderConnectionRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> ProviderConnectionResponse:
    """Store encrypted API key using AES-256-GCM. Secret is never returned in plaintext."""
    return await AIService.create_connection(session, context, req)


@router.get(
    "/connections",
    response_model=list[ProviderConnectionResponse],
    status_code=status.HTTP_200_OK,
    summary="List active provider credentials with masked previews",
)
async def list_provider_connections(
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[ProviderConnectionResponse]:
    """List credentials belonging to the user or active organization. Keys are strictly masked."""
    return await AIService.list_connections(session, context)


@router.delete(
    "/connections/{connection_id}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate an AI provider credential",
)
async def delete_provider_connection(
    connection_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Deactivate stored credential with ownership authorization check."""
    await AIService.delete_connection(session, context, connection_id)
    return {"status": "ok", "message": "Provider credential deactivated successfully."}


@router.get(
    "/models",
    response_model=list[ProviderModelSnapshotResponse],
    status_code=status.HTTP_200_OK,
    summary="List discovered models and capabilities",
)
async def list_models(
    provider_type: str | None = Query(
        None, description="Filter by provider: openai, gemini, anthropic, mock"
    ),
    session: AsyncSession = Depends(get_db),
) -> list[ProviderModelSnapshotResponse]:
    """List available model catalog snapshots with context limits and tool capabilities."""
    models = await AIService.list_models(session, provider_type)
    return [ProviderModelSnapshotResponse.model_validate(m) for m in models]


@router.post(
    "/models/sync",
    response_model=list[ProviderModelSnapshotResponse],
    status_code=status.HTTP_200_OK,
    summary="Synchronize model catalog from provider",
)
async def sync_models(
    provider_type: str = Query(
        "mock", description="Provider to sync from: mock, openai, anthropic, gemini"
    ),
    session: AsyncSession = Depends(get_db),
) -> list[ProviderModelSnapshotResponse]:
    """Query provider and update local capability snapshot cache."""
    snapshots = await AIService.sync_models_from_provider(session, provider_type)
    return [ProviderModelSnapshotResponse.model_validate(s) for s in snapshots]


@router.post(
    "/generate",
    response_model=AIGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Server-side AI text generation with resilient fallback",
)
async def generate_completion(
    req: AIGenerationRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> AIGenerationResponse:
    """Execute text generation server-side. Triggers automated fallback if quota is exceeded."""
    return await AIGateway.generate(session, context, req)


@router.post(
    "/generate/stream",
    status_code=status.HTTP_200_OK,
    summary="Server-Sent Events (SSE) streaming text generation",
)
async def stream_completion(
    req: AIGenerationRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream generated tokens over Server-Sent Events (SSE)."""

    async def event_generator():
        async for chunk in AIGateway.stream_generate(session, context, req):
            payload = json.dumps({"chunk": chunk})
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
