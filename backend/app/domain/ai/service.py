"""AI Credentials and Model Catalog Management Domain Services."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext
from app.core.security import (
    compute_key_fingerprint,
    decrypt_credential,
    encrypt_credential,
    mask_credential,
)
from app.db.base import generate_uuid
from app.db.models.ai import ProviderConnection, ProviderModelSnapshot
from app.domain.ai.adapters import get_provider_adapter

# --- Schemas ---


class CreateProviderConnectionRequest(BaseModel):
    provider_type: str = Field(description="openai, anthropic, gemini, openrouter, custom, or mock")
    api_key: str = Field(min_length=4, description="Raw provider API key (encrypted immediately)")
    custom_endpoint_url: str | None = None
    is_organization_level: bool = False


class ProviderConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str | None
    user_id: str | None
    provider_type: str
    key_mask: str
    key_fingerprint: str
    custom_endpoint_url: str | None
    is_active: bool
    created_at: datetime


class ProviderModelSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_type: str
    model_id: str
    display_name: str
    context_window_tokens: int
    supports_streaming: bool
    supports_tools: bool
    last_discovered_at: datetime


class ModelPolicyRequest(BaseModel):
    default_provider: str = "mock"
    default_model: str = "mock-tutor-standard"
    fallback_provider: str | None = "mock"
    fallback_model: str | None = "mock-fast-evaluator"
    max_tokens_per_call: int = 2048


class ModelPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str | None
    task_type: str
    default_provider: str
    default_model: str
    fallback_provider: str | None
    fallback_model: str | None
    max_tokens_per_call: int


# --- Domain Service ---


class AIService:
    """Manages secure credential vault, model synchronization, and routing policies."""

    @staticmethod
    async def create_connection(
        session: AsyncSession,
        context: TenantContext,
        req: CreateProviderConnectionRequest,
    ) -> ProviderConnectionResponse:
        """Encrypt and persist provider credential. Raw secret is never returned in response."""
        # Check permissions for organization-level credentials
        if req.is_organization_level:
            if not context.has_role(RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Organization Admins can register organization-level provider credentials.",
                )
            org_id = context.organization_id
            user_id = None
        else:
            org_id = None
            user_id = context.user.id

        # Authenticated AES-256-GCM encryption
        ciphertext = encrypt_credential(req.api_key)
        fingerprint = compute_key_fingerprint(req.api_key)
        display_mask = mask_credential(req.api_key)

        conn = ProviderConnection(
            id=generate_uuid(),
            organization_id=org_id,
            user_id=user_id,
            provider_type=req.provider_type.lower(),
            encrypted_key_ciphertext=ciphertext,
            key_fingerprint=fingerprint,
            custom_endpoint_url=req.custom_endpoint_url,
            is_active=True,
        )
        session.add(conn)
        await session.commit()
        await session.refresh(conn)

        return ProviderConnectionResponse(
            id=conn.id,
            organization_id=conn.organization_id,
            user_id=conn.user_id,
            provider_type=conn.provider_type,
            key_mask=display_mask,
            key_fingerprint=conn.key_fingerprint,
            custom_endpoint_url=conn.custom_endpoint_url,
            is_active=conn.is_active,
            created_at=conn.created_at,
        )

    @staticmethod
    async def list_connections(
        session: AsyncSession,
        context: TenantContext,
    ) -> list[ProviderConnectionResponse]:
        """List active credentials visible to caller with masked secret previews."""
        stmt = select(ProviderConnection).where(
            (ProviderConnection.user_id == context.user.id)
            | (
                (ProviderConnection.organization_id == context.organization_id)
                & (ProviderConnection.organization_id.is_not(None))
            ),
            ProviderConnection.is_active.is_(True),
        )
        res = await session.execute(stmt)
        connections = list(res.scalars().all())

        responses: list[ProviderConnectionResponse] = []
        for c in connections:
            try:
                decrypted = decrypt_credential(c.encrypted_key_ciphertext)
                mask = mask_credential(decrypted)
            except Exception:
                mask = "sk-...[encrypted]"

            responses.append(
                ProviderConnectionResponse(
                    id=c.id,
                    organization_id=c.organization_id,
                    user_id=c.user_id,
                    provider_type=c.provider_type,
                    key_mask=mask,
                    key_fingerprint=c.key_fingerprint,
                    custom_endpoint_url=c.custom_endpoint_url,
                    is_active=c.is_active,
                    created_at=c.created_at,
                )
            )
        return responses

    @staticmethod
    async def delete_connection(
        session: AsyncSession,
        context: TenantContext,
        connection_id: str,
    ) -> None:
        """Deactivate provider credential with ownership verification."""
        stmt = select(ProviderConnection).where(ProviderConnection.id == connection_id)
        res = await session.execute(stmt)
        conn = res.scalar_one_or_none()
        if not conn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider connection not found.",
            )

        # Verification: User owns connection OR user is ORG_ADMIN of connection's organization
        is_owner = conn.user_id == context.user.id
        is_org_admin = conn.organization_id == context.organization_id and context.has_role(
            RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value
        )
        if not (is_owner or is_org_admin or context.user.is_super_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot delete credential belonging to another user or organization.",
            )

        conn.is_active = False
        await session.commit()

    @staticmethod
    async def sync_models_from_provider(
        session: AsyncSession,
        provider_type: str,
    ) -> list[ProviderModelSnapshot]:
        """Discover and synchronize available models into snapshot cache."""
        adapter = get_provider_adapter(provider_type)
        discovered = await adapter.list_models()

        snapshots: list[ProviderModelSnapshot] = []
        now = datetime.now(UTC)

        for m in discovered:
            stmt = select(ProviderModelSnapshot).where(
                ProviderModelSnapshot.provider_type == provider_type,
                ProviderModelSnapshot.model_id == m.model_id,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                existing.display_name = m.display_name
                existing.context_window_tokens = m.context_window_tokens
                existing.supports_streaming = m.supports_streaming
                existing.supports_tools = m.supports_tools
                existing.last_discovered_at = now
                snapshots.append(existing)
            else:
                new_snap = ProviderModelSnapshot(
                    id=generate_uuid(),
                    provider_type=provider_type,
                    model_id=m.model_id,
                    display_name=m.display_name,
                    context_window_tokens=m.context_window_tokens,
                    supports_streaming=m.supports_streaming,
                    supports_tools=m.supports_tools,
                    last_discovered_at=now,
                )
                session.add(new_snap)
                snapshots.append(new_snap)

        await session.commit()
        return snapshots

    @staticmethod
    async def list_models(
        session: AsyncSession,
        provider_type: str | None = None,
    ) -> list[ProviderModelSnapshot]:
        """List cached model snapshots, syncing defaults if empty."""
        stmt = select(ProviderModelSnapshot)
        if provider_type:
            stmt = stmt.where(ProviderModelSnapshot.provider_type == provider_type.lower())

        res = await session.execute(stmt)
        models = list(res.scalars().all())

        if not models:
            # Seed initial snapshots from mock adapter
            models = await AIService.sync_models_from_provider(session, provider_type or "mock")

        return models
