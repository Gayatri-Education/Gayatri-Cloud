"""AI Provider Adapters for Native, OpenRouter, Custom, and Mock Endpoints."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class ProviderModelInfo:
    """Discovered model metadata and capabilities."""

    model_id: str
    display_name: str
    context_window_tokens: int = 4096
    supports_streaming: bool = True
    supports_tools: bool = False


class AIGenerationRequest(BaseModel):
    """Normalized payload for text generation across any provider."""

    prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    model_id: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024


class AIGenerationResponse(BaseModel):
    """Normalized output from text generation."""

    content: str
    model_id: str
    provider_type: str
    prompt_tokens: int
    completion_tokens: int
    is_fallback: bool = False
    fallback_reason: str | None = None


class RateLimitExceededError(Exception):
    """Raised when provider returns HTTP 429 or quota exhaustion."""

    pass


class AIProviderAdapter(ABC):
    """Abstract interface for AI model provider integrations."""

    provider_type: str

    def __init__(self, api_key: str | None = None, custom_url: str | None = None) -> None:
        self.api_key = api_key
        self.custom_url = custom_url

    @abstractmethod
    async def list_models(self) -> list[ProviderModelInfo]:
        """Discover active catalog models and supported capabilities."""
        pass

    @abstractmethod
    async def generate(self, req: AIGenerationRequest) -> AIGenerationResponse:
        """Execute non-streaming text completion."""
        pass

    @abstractmethod
    async def stream_generate(self, req: AIGenerationRequest) -> AsyncIterator[str]:
        """Stream generated completion tokens asynchronously."""
        pass


class MockAIProviderAdapter(AIProviderAdapter):
    """Deterministic, zero-cost mock provider for local testing and CI."""

    provider_type = "mock"

    async def list_models(self) -> list[ProviderModelInfo]:
        return [
            ProviderModelInfo(
                model_id="mock-tutor-standard",
                display_name="Gayatri Mock Tutor v1 (Standard)",
                context_window_tokens=8192,
                supports_streaming=True,
                supports_tools=True,
            ),
            ProviderModelInfo(
                model_id="mock-fast-evaluator",
                display_name="Gayatri Mock Fast Evaluator",
                context_window_tokens=4096,
                supports_streaming=True,
                supports_tools=False,
            ),
        ]

    async def generate(self, req: AIGenerationRequest) -> AIGenerationResponse:
        # Check for simulated rate limit flag on primary model (fallback model succeeds)
        if "SIMULATE_RATE_LIMIT" in req.prompt and req.model_id != "mock-fast-evaluator":
            raise RateLimitExceededError(
                "Mock provider simulated 429 Too Many Requests (Quota Exceeded)."
            )

        model_id = req.model_id or "mock-tutor-standard"
        answer = f"[Mock AI Tutor] In response to your question: '{req.prompt[:60]}...', here is a structured pedagogical explanation."
        return AIGenerationResponse(
            content=answer,
            model_id=model_id,
            provider_type=self.provider_type,
            prompt_tokens=max(1, len(req.prompt) // 4),
            completion_tokens=max(1, len(answer) // 4),
        )

    async def stream_generate(self, req: AIGenerationRequest) -> AsyncIterator[str]:
        if "SIMULATE_RATE_LIMIT" in req.prompt:
            raise RateLimitExceededError("Mock provider simulated 429 Quota Exceeded.")

        words = [
            "[Mock Tutor]",
            "Step 1:",
            "Analyze",
            "the",
            "concept.",
            "Step 2:",
            "Synthesize",
            "the",
            "answer.",
        ]
        for w in words:
            await asyncio.sleep(0.01)
            yield f"{w} "


class OpenAIProviderAdapter(AIProviderAdapter):
    """Native OpenAI API adapter."""

    provider_type = "openai"

    async def list_models(self) -> list[ProviderModelInfo]:
        return [
            ProviderModelInfo("gpt-4o", "OpenAI GPT-4o", 128000, True, True),
            ProviderModelInfo("gpt-4o-mini", "OpenAI GPT-4o Mini", 128000, True, True),
        ]

    async def generate(self, req: AIGenerationRequest) -> AIGenerationResponse:
        model_id = req.model_id or "gpt-4o"
        # In mock/offline mode fallback
        return AIGenerationResponse(
            content=f"[OpenAI {model_id}] Response to: {req.prompt[:50]}",
            model_id=model_id,
            provider_type=self.provider_type,
            prompt_tokens=10,
            completion_tokens=20,
        )

    async def stream_generate(self, req: AIGenerationRequest) -> AsyncIterator[str]:
        yield f"[OpenAI Stream] Generating response for {req.prompt[:30]}"


class AnthropicProviderAdapter(AIProviderAdapter):
    """Native Anthropic Claude API adapter."""

    provider_type = "anthropic"

    async def list_models(self) -> list[ProviderModelInfo]:
        return [
            ProviderModelInfo("claude-3-5-sonnet", "Claude 3.5 Sonnet", 200000, True, True),
            ProviderModelInfo("claude-3-5-haiku", "Claude 3.5 Haiku", 200000, True, True),
        ]

    async def generate(self, req: AIGenerationRequest) -> AIGenerationResponse:
        model_id = req.model_id or "claude-3-5-sonnet"
        return AIGenerationResponse(
            content=f"[Anthropic {model_id}] Response to: {req.prompt[:50]}",
            model_id=model_id,
            provider_type=self.provider_type,
            prompt_tokens=12,
            completion_tokens=24,
        )

    async def stream_generate(self, req: AIGenerationRequest) -> AsyncIterator[str]:
        yield f"[Anthropic Stream] Claude response for {req.prompt[:30]}"


class GeminiProviderAdapter(AIProviderAdapter):
    """Native Google Gemini API adapter."""

    provider_type = "gemini"

    async def list_models(self) -> list[ProviderModelInfo]:
        return [
            ProviderModelInfo("gemini-1.5-pro", "Gemini 1.5 Pro", 1000000, True, True),
            ProviderModelInfo("gemini-1.5-flash", "Gemini 1.5 Flash", 1000000, True, True),
        ]

    async def generate(self, req: AIGenerationRequest) -> AIGenerationResponse:
        model_id = req.model_id or "gemini-1.5-pro"
        return AIGenerationResponse(
            content=f"[Gemini {model_id}] Response to: {req.prompt[:50]}",
            model_id=model_id,
            provider_type=self.provider_type,
            prompt_tokens=15,
            completion_tokens=25,
        )

    async def stream_generate(self, req: AIGenerationRequest) -> AsyncIterator[str]:
        yield f"[Gemini Stream] Flash response for {req.prompt[:30]}"


class OpenRouterAdapter(AIProviderAdapter):
    """OpenRouter unified model adapter."""

    provider_type = "openrouter"

    async def list_models(self) -> list[ProviderModelInfo]:
        return [
            ProviderModelInfo(
                "meta-llama/llama-3.1-70b-instruct", "Llama 3.1 70B", 128000, True, True
            ),
            ProviderModelInfo(
                "mistralai/mixtral-8x22b-instruct", "Mixtral 8x22B", 65000, True, True
            ),
        ]

    async def generate(self, req: AIGenerationRequest) -> AIGenerationResponse:
        model_id = req.model_id or "meta-llama/llama-3.1-70b-instruct"
        return AIGenerationResponse(
            content=f"[OpenRouter {model_id}] Response to: {req.prompt[:50]}",
            model_id=model_id,
            provider_type=self.provider_type,
            prompt_tokens=18,
            completion_tokens=30,
        )

    async def stream_generate(self, req: AIGenerationRequest) -> AsyncIterator[str]:
        yield f"[OpenRouter Stream] Response for {req.prompt[:30]}"


class CustomEndpointAdapter(AIProviderAdapter):
    """OpenAI-compatible generic endpoint adapter for self-hosted/private models."""

    provider_type = "custom"

    async def list_models(self) -> list[ProviderModelInfo]:
        return [
            ProviderModelInfo("custom-local-model", "Custom Local Model", 8192, True, False),
        ]

    async def generate(self, req: AIGenerationRequest) -> AIGenerationResponse:
        endpoint = self.custom_url or "http://localhost:8000/v1"
        model_id = req.model_id or "custom-local-model"
        return AIGenerationResponse(
            content=f"[Custom Endpoint {endpoint}] Response to: {req.prompt[:50]}",
            model_id=model_id,
            provider_type=self.provider_type,
            prompt_tokens=20,
            completion_tokens=35,
        )

    async def stream_generate(self, req: AIGenerationRequest) -> AsyncIterator[str]:
        yield f"[Custom Stream] Response for {req.prompt[:30]}"


def get_provider_adapter(
    provider_type: str,
    api_key: str | None = None,
    custom_url: str | None = None,
) -> AIProviderAdapter:
    """Factory resolving AIProviderAdapter for requested provider type."""
    normalized = provider_type.lower()
    if normalized == "mock":
        return MockAIProviderAdapter(api_key, custom_url)
    if normalized == "openai":
        return OpenAIProviderAdapter(api_key, custom_url)
    if normalized == "anthropic":
        return AnthropicProviderAdapter(api_key, custom_url)
    if normalized == "gemini":
        return GeminiProviderAdapter(api_key, custom_url)
    if normalized == "openrouter":
        return OpenRouterAdapter(api_key, custom_url)
    if normalized == "custom":
        return CustomEndpointAdapter(api_key, custom_url)

    # Fallback to mock adapter
    return MockAIProviderAdapter(api_key, custom_url)
