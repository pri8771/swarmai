"""Core provider adapter classes."""

from __future__ import annotations

from swarm.providers.core.base import BaseCoreAdapter


class OpenRouterAdapter(BaseCoreAdapter):
    provider_id = "openrouter"
    default_model = "openrouter/auto"


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
