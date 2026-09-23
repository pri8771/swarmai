"""Core provider adapter classes."""

from __future__ import annotations

from typing import Any

from swarm.contracts.enums import AvailabilityStatus
from swarm.contracts.provider import InferenceRequest, RouteSnapshot
from swarm.providers.core.base import BaseCoreAdapter
from swarm.providers.openrouter_free import OpenRouterFreeRoute


class OpenRouterAdapter(BaseCoreAdapter):
    provider_id = "openrouter"
    default_model = "openrouter/auto"

    def __init__(self, *, free_route: OpenRouterFreeRoute | None = None, **kwargs: Any) -> None:
        self.free_route = free_route
        super().__init__(**kwargs)
        route = self._routes[f"rt_{self.provider_id}_default"]
        if free_route is None:
            # Live/network modes must pin an allowlisted free route; replay fixtures
            # retain the historical default for offline tests only.
            if self.mode != "replay":
                route.availability_status = AvailabilityStatus.DISABLED
                route.status = "requires_explicit_free_route"
        else:
            # Replace default seed with the exact allowlisted free route id.
            self._routes.pop(route.route_id, None)
            pinned = RouteSnapshot(
                route_id=free_route.route_id,
                provider=self.provider_id,
                account_id=self.account_id,
                model_id=free_route.model_id,
                endpoint=self.base_url,
                hosted_by=free_route.provider_slug,
                billing_origin="openrouter_free_allowlisted",
                capability_claims=["chat"],
                observed_capabilities=[],
                availability_status=(
                    AvailabilityStatus.DISABLED
                    if not self.enabled
                    else AvailabilityStatus.AVAILABLE
                ),
                status="implemented_offline" if not self.enabled else "enabled",
                observed_at=route.observed_at,
            )
            self._routes[pinned.route_id] = pinned

    async def discover(self) -> list[RouteSnapshot]:
        # No implicit authenticated /models discovery — avoid unverified routes.
        if self.free_route is not None or self.mode == "replay":
            return list(self._routes.values())
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
        return self.transport.request(
            "POST",
            "/chat/completions",
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
