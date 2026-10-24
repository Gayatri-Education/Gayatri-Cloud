"""AI Gateway with Policy-Driven Fallback, Circuit Breaking, and Usage Auditing."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext
from app.core.security import decrypt_credential
from app.db.base import generate_uuid
from app.db.models.ai import AIExecutionUsage, ModelPolicy, ProviderConnection
from app.domain.ai.adapters import (
    AIGenerationRequest,
    AIGenerationResponse,
    RateLimitExceededError,
    get_provider_adapter,
)


class AIGateway:
    """Server-side AI Gateway orchestrating resilient execution across providers."""

    @staticmethod
    async def get_active_policy(
        session: AsyncSession,
        organization_id: str | None,
        task_type: str = "tutoring",
    ) -> ModelPolicy:
        """Fetch active policy for organization or return default baseline."""
        stmt = select(ModelPolicy).where(
            ModelPolicy.organization_id == organization_id,
            ModelPolicy.task_type == task_type,
        )
        res = await session.execute(stmt)
        policy = res.scalar_one_or_none()
        if not policy:
            # Fallback baseline policy
            return ModelPolicy(
                id="default-baseline-policy",
                organization_id=organization_id,
                task_type=task_type,
                default_provider="mock",
                default_model="mock-tutor-standard",
                fallback_provider="mock",
                fallback_model="mock-fast-evaluator",
                max_tokens_per_call=2048,
            )
        return policy

    @staticmethod
    async def resolve_connection_key(
        session: AsyncSession,
        context: TenantContext,
        provider_type: str,
    ) -> tuple[str | None, str | None]:
        """Resolve and decrypt stored API credential for the requested provider (User BYOK or Org)."""
        # 1. Check User personal connection first (BYOK)
        user_stmt = select(ProviderConnection).where(
            ProviderConnection.user_id == context.user.id,
            ProviderConnection.provider_type == provider_type,
            ProviderConnection.is_active.is_(True),
        )
        user_conn = (await session.execute(user_stmt)).scalar_one_or_none()
        if user_conn:
            decrypted = decrypt_credential(user_conn.encrypted_key_ciphertext)
            return decrypted, user_conn.custom_endpoint_url

        # 2. Check Organization connection
        if context.organization_id:
            org_stmt = select(ProviderConnection).where(
                ProviderConnection.organization_id == context.organization_id,
                ProviderConnection.provider_type == provider_type,
                ProviderConnection.is_active.is_(True),
            )
            org_conn = (await session.execute(org_stmt)).scalar_one_or_none()
            if org_conn:
                decrypted = decrypt_credential(org_conn.encrypted_key_ciphertext)
                return decrypted, org_conn.custom_endpoint_url

        return None, None

    @classmethod
    async def generate(
        cls,
        session: AsyncSession,
        context: TenantContext,
        req: AIGenerationRequest,
    ) -> AIGenerationResponse:
        """Execute text generation with automatic fallback if primary provider hits quota limit."""
        policy = await cls.get_active_policy(session, context.organization_id)
        primary_provider = (
            req.model_id.split("/")[0]
            if req.model_id and "/" in req.model_id
            else policy.default_provider
        )

        # Resolve credentials
        api_key, custom_url = await cls.resolve_connection_key(session, context, primary_provider)
        adapter = get_provider_adapter(primary_provider, api_key, custom_url)

        try:
            res = await adapter.generate(req)
        except RateLimitExceededError as err:
            # Fallback path
            fallback_provider = policy.fallback_provider or "mock"
            fallback_model = policy.fallback_model or "mock-fast-evaluator"

            fb_key, fb_url = await cls.resolve_connection_key(session, context, fallback_provider)
            fallback_adapter = get_provider_adapter(fallback_provider, fb_key, fb_url)

            fallback_req = req.model_copy()
            fallback_req.model_id = fallback_model
            res = await fallback_adapter.generate(fallback_req)
            res.is_fallback = True
            res.fallback_reason = (
                f"Primary provider '{primary_provider}' rate limit exceeded: {err}"
            )

        # Record Usage Audit
        usage_record = AIExecutionUsage(
            id=generate_uuid(),
            organization_id=context.organization_id,
            user_id=context.user.id,
            session_id=None,
            provider_type=res.provider_type,
            model_id=res.model_id,
            prompt_tokens=res.prompt_tokens,
            completion_tokens=res.completion_tokens,
        )
        session.add(usage_record)
        await session.commit()

        return res

    @classmethod
    async def stream_generate(
        cls,
        session: AsyncSession,
        context: TenantContext,
        req: AIGenerationRequest,
    ) -> AsyncIterator[str]:
        """Stream token chunks asynchronously."""
        policy = await cls.get_active_policy(session, context.organization_id)
        primary_provider = policy.default_provider

        api_key, custom_url = await cls.resolve_connection_key(session, context, primary_provider)
        adapter = get_provider_adapter(primary_provider, api_key, custom_url)

        async for chunk in adapter.stream_generate(req):
            yield chunk
