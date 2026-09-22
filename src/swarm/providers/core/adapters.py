"""Core provider adapter classes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from swarm.contracts.enums import AvailabilityStatus
from swarm.contracts.provider import InferenceRequest, RouteSnapshot
from swarm.providers.core.base import BaseCoreAdapter


@dataclass(frozen=True)
class OpenRouterFreeRoute:
    """One exact free model and hosting backend, selected before admission."""

    model_id: str
    provider_slug: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*:free", self.model_id):
            raise ValueError("OpenRouter route requires an exact :free model slug")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", self.provider_slug):
            raise ValueError("OpenRouter route requires one exact backend slug")


class OpenRouterAdapter(BaseCoreAdapter):
    provider_id = "openrouter"
    default_model = "openrouter/auto"

    def __init__(self, *, free_route: OpenRouterFreeRoute | None = None, **kwargs: Any) -> None:
        self.free_route = free_route
        super().__init__(**kwargs)
        route = self._routes[f"rt_{self.provider_id}_default"]
        if free_route is None:
            route.availability_status = AvailabilityStatus.DISABLED
            route.status = "requires_explicit_free_route"
        else:
            route.model_id = free_route.model_id
            route.hosted_by = free_route.provider_slug
            route.billing_origin = "openrouter_free_unverified"

    async def discover(self) -> list[RouteSnapshot]:
        # No implicit authenticated /models request or unverified route creation.
        return list(self._routes.values())

    def _invoke(self, model_id: str, request: InferenceRequest) -> dict[str, Any]:
        free_route = self.free_route
        if free_route is None:
            if self.mode == "replay":
                return super()._invoke(model_id, request)
            raise ValueError("OpenRouter requires an explicit free route before network")
        if model_id != free_route.model_id:
            raise ValueError("OpenRouter route model differs from pinned free model")
        if request.max_output_tokens is None:
            raise ValueError("OpenRouter free route requires a finite output limit")
        response = self.transport.request_with_metadata(
            "POST",
            "/chat/completions",
            extra_headers={"X-OpenRouter-Metadata": "enabled"},
            json_body={
                "model": free_route.model_id,
                "messages": request.messages,
                "stream": False,
                "max_tokens": request.max_output_tokens,
                "provider": {
                    "only": [free_route.provider_slug],
                    "allow_fallbacks": False,
                    "max_price": {"prompt": 0, "completion": 0},
                    "require_parameters": True,
                },
            },
        )
        return {**response.body, "_swarm_rate_limit_headers": response.rate_limit_headers}


class GroqAdapter(BaseCoreAdapter):
    provider_id = "groq"
    default_model = "llama-3.1-8b-instant"


class GeminiAdapter(BaseCoreAdapter):
    provider_id = "gemini"
    default_model = "gemini-2.0-flash"
    api_style = "gemini"


class CloudflareWorkersAIAdapter(BaseCoreAdapter):
    provider_id = "cloudflare_workers_ai"
    default_model = "@cf/meta/llama-3.1-8b-instruct"
    api_style = "cloudflare"


class HuggingFaceInferenceAdapter(BaseCoreAdapter):
    provider_id = "huggingface_inference"
    default_model = "meta-llama/Meta-Llama-3-8B-Instruct"
    # Routed HF Inference Providers (OpenAI-compatible router) vs dedicated custom
    # endpoints are distinct billing origins; custom keys set billing_origin separately.


class NvidiaNimAdapter(BaseCoreAdapter):
    provider_id = "nvidia_nim"
    default_model = "meta/llama-3.1-8b-instruct"


class MistralAdapter(BaseCoreAdapter):
    provider_id = "mistral"
    default_model = "mistral-small-latest"


class CohereAdapter(BaseCoreAdapter):
    provider_id = "cohere"
    default_model = "command-r-plus"
    api_style = "cohere"


class CerebrasAdapter(BaseCoreAdapter):
    provider_id = "cerebras"
    default_model = "llama3.1-8b"


class OllamaAdapter(BaseCoreAdapter):
    provider_id = "ollama"
    default_model = "llama3.2"


CORE_ADAPTER_TYPES: dict[str, type[BaseCoreAdapter]] = {
    "openrouter": OpenRouterAdapter,
    "groq": GroqAdapter,
    "gemini": GeminiAdapter,
    "cloudflare_workers_ai": CloudflareWorkersAIAdapter,
    "huggingface_inference": HuggingFaceInferenceAdapter,
    "nvidia_nim": NvidiaNimAdapter,
    "mistral": MistralAdapter,
    "cohere": CohereAdapter,
    "cerebras": CerebrasAdapter,
    "ollama": OllamaAdapter,
}
