"""Extended provider adapters — configuration-driven compatible transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from swarm.providers.catalog import load_catalog
from swarm.providers.core.base import BaseCoreAdapter
from swarm.providers.transport.openai_compatible import TransportMode

# Protocol notes recorded from current public docs posture in the kit (offline).
EXTENDED_SPECS: dict[str, dict[str, Any]] = {
    "together": {
        "protocol": "openai_compatible",
        "base_url": "https://api.together.xyz/v1",
        "env_vars": ["TOGETHER_API_KEY"],
        "default_model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "general_model": True,
    },
    "fireworks": {
        "protocol": "openai_compatible",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "env_vars": ["FIREWORKS_API_KEY"],
        "default_model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "general_model": True,
    },
    "deepinfra": {
        "protocol": "openai_compatible",
        "base_url": "https://api.deepinfra.com/v1/openai",
        "env_vars": ["DEEPINFRA_API_KEY"],
        "default_model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "general_model": True,
    },
    "replicate": {
        "protocol": "openai_compatible",
        "base_url": "https://openai-proxy.replicate.com/v1",
        "env_vars": ["REPLICATE_API_TOKEN"],
        "default_model": "meta/meta-llama-3-8b-instruct",
        "general_model": True,
        "notes": "Also has model-specific HTTP API; chat proxy used when available",
    },
    "perplexity": {
        "protocol": "openai_compatible",
        "base_url": "https://api.perplexity.ai",
        "env_vars": ["PERPLEXITY_API_KEY"],
        "default_model": "sonar",
        "general_model": True,
        "specialized": ["web_grounded_search"],
    },
    "openai": {
        "protocol": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "env_vars": ["OPENAI_API_KEY"],
        "default_model": "gpt-4.1-mini",
        "general_model": True,
    },
    "anthropic": {
        "protocol": "anthropic_messages",
        "base_url": "https://api.anthropic.com",
        "env_vars": ["ANTHROPIC_API_KEY"],
        "default_model": "claude-sonnet-4-20250514",
        "general_model": True,
    },
    "aws_bedrock": {
        "protocol": "bedrock_runtime",
        "base_url": None,
        "env_vars": ["AWS_PROFILE", "AWS_REGION"],
        "default_model": "anthropic.claude-3-haiku-20240307-v1:0",
        "general_model": True,
        "notes": "Uses AWS credentials chain; not OpenAI-compatible",
    },
    "azure_ai_foundry": {
        "protocol": "azure_openai_compatible",
        "base_url": None,
        "env_vars": ["AZURE_AI_ENDPOINT", "AZURE_AI_API_KEY"],
        "default_model": "deployment-name",
        "general_model": True,
    },
    "hyperbolic": {
        "protocol": "openai_compatible",
        "base_url": "https://api.hyperbolic.xyz/v1",
        "env_vars": ["HYPERBOLIC_API_KEY"],
        "default_model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "general_model": True,
    },
    "sambanova": {
        "protocol": "openai_compatible",
        "base_url": "https://api.sambanova.ai/v1",
        "env_vars": ["SAMBANOVA_API_KEY"],
        "default_model": "Meta-Llama-3.1-8B-Instruct",
        "general_model": True,
    },
    "novita": {
        "protocol": "openai_compatible",
        "base_url": "https://api.novita.ai/v3/openai",
        "env_vars": ["NOVITA_API_KEY"],
        "default_model": "meta-llama/llama-3.1-8b-instruct",
        "general_model": True,
    },
    "requesty": {
        "protocol": "openai_compatible",
        "base_url": "https://router.requesty.ai/v1",
        "env_vars": ["REQUESTY_API_KEY"],
        "default_model": "openai/gpt-4.1-mini",
        "general_model": True,
        "notes": "Gateway; does not create free upstream quota",
    },
    "vercel_ai_gateway": {
        "protocol": "openai_compatible",
        "base_url": "https://ai-gateway.vercel.sh/v1",
        "env_vars": ["VERCEL_AI_GATEWAY_API_KEY"],
        "default_model": "openai/gpt-4.1-mini",
        "general_model": True,
        "notes": "Gateway; shared upstream quota with origin providers",
    },
    "portkey_cloud": {
        "protocol": "openai_compatible",
        "base_url": "https://api.portkey.ai/v1",
        "env_vars": ["PORTKEY_API_KEY"],
        "default_model": "gpt-4.1-mini",
        "general_model": True,
        "notes": "Gateway; not a free quota source",
    },
    "cloudflare_ai_gateway": {
        "protocol": "openai_compatible",
        "base_url": None,
        "env_vars": ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_GATEWAY_ID"],
        "default_model": "upstream-model",
        "general_model": True,
        "notes": "Gateway over upstream providers; neurons/credits follow upstream",
    },
    "huggingface_dedicated": {
        "protocol": "openai_compatible",
        "base_url": None,
        "env_vars": ["HF_TOKEN"],
        "default_model": "endpoint-model",
        "general_model": True,
        "notes": "Reference existing dedicated endpoint only; never provision here",
        "billing_origin": "hf_dedicated",
    },
    "vllm": {
        "protocol": "openai_compatible",
        "base_url": "http://127.0.0.1:8000/v1",
        "env_vars": ["VLLM_API_KEY", "VLLM_BASE_URL"],
        "default_model": "local-model",
        "general_model": True,
        "local": True,
    },
    "mlx_lm": {
        "protocol": "openai_compatible",
        "base_url": "http://127.0.0.1:8080/v1",
        "env_vars": ["MLX_LM_BASE_URL"],
        "default_model": "local-mlx-model",
        "general_model": True,
        "local": True,
    },
    "llama_cpp": {
        "protocol": "openai_compatible",
        "base_url": "http://127.0.0.1:8080/v1",
        "env_vars": ["LLAMA_CPP_BASE_URL", "LLAMA_CPP_API_KEY"],
        "default_model": "local-gguf",
        "general_model": True,
        "local": True,
    },
    "llamafile": {
        "protocol": "openai_compatible",
        "base_url": "http://127.0.0.1:8080/v1",
        "env_vars": ["LLAMAFILE_BASE_URL"],
        "default_model": "local-llamafile",
        "general_model": True,
        "local": True,
    },
}


@dataclass
class ExtendedAdapterInfo:
    provider_id: str
    protocol: str
    supported: bool
    reason: str | None = None
    adapter: BaseCoreAdapter | None = None


class ExtendedOpenAIAdapter(BaseCoreAdapter):
    def __init__(self, provider_id: str, *, default_model: str, **kwargs: Any) -> None:
        self.provider_id = provider_id
        self.default_model = default_model
        super().__init__(**kwargs)


class AnthropicAdapter(BaseCoreAdapter):
    """Anthropic Messages API thin adapter (fixture-replayable)."""

    provider_id = "anthropic"
    default_model = "claude-sonnet-4-20250514"
    api_style = "anthropic_messages"

    def _invoke(self, model_id: str, request: Any) -> dict[str, Any]:
        body = {
            "model": model_id,
            "max_tokens": request.max_output_tokens or 256,
            "messages": [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in request.messages
                if m.get("role") != "system"
            ],
        }
        raw = self.transport.request("POST", "/v1/messages", json_body=body)
        content = ""
        for block in raw.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
        usage = raw.get("usage") or {}
        return {
            "id": raw.get("id"),
            "model": raw.get("model", model_id),
            "choices": [{"message": {"role": "assistant", "content": content}}],
            "usage": {
                "prompt_tokens": usage.get("input_tokens"),
                "completion_tokens": usage.get("output_tokens"),
                "total_tokens": (
                    None
                    if usage.get("input_tokens") is None
                    else (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
                ),
            },
        }


def build_extended_adapters(
    *, mode: TransportMode = "replay", enabled: bool = False
) -> dict[str, ExtendedAdapterInfo]:
    catalog = {p["id"]: p for p in load_catalog().get("providers", [])}
    out: dict[str, ExtendedAdapterInfo] = {}
    for pid, spec in EXTENDED_SPECS.items():
        entry = catalog.get(pid, {})
        if entry.get("service_status") == "retired":
            out[pid] = ExtendedAdapterInfo(pid, spec["protocol"], False, "retired")
            continue
        protocol = spec["protocol"]
        env_vars = entry.get("env_vars") or spec["env_vars"]
        base_url = entry.get("base_url") or spec.get("base_url")
        if protocol in {"openai_compatible", "azure_openai_compatible"}:
            needs_url = {"azure_ai_foundry", "cloudflare_ai_gateway", "huggingface_dedicated"}
            if base_url is None and pid not in needs_url:
                out[pid] = ExtendedAdapterInfo(pid, protocol, False, "missing_base_url")
                continue
            # Placeholder local URL when endpoint is operator-configured.
            url = base_url or "http://127.0.0.1:9/v1"
            adapter: BaseCoreAdapter = ExtendedOpenAIAdapter(
                pid,
                default_model=spec["default_model"],
                secret_ref_names=env_vars,
                base_url=url,
                mode=mode,
                enabled=enabled,
            )
            if spec.get("billing_origin"):
                route = next(iter(adapter._routes.values()))
                route.billing_origin = spec["billing_origin"]
            out[pid] = ExtendedAdapterInfo(pid, protocol, True, None, adapter)
        elif protocol == "anthropic_messages":
            adapter = AnthropicAdapter(
                secret_ref_names=env_vars,
                base_url=base_url or "https://api.anthropic.com",
                mode=mode,
                enabled=enabled,
            )
            out[pid] = ExtendedAdapterInfo(pid, protocol, True, None, adapter)
        elif protocol == "bedrock_runtime":
            # Supported as a typed adapter shell that refuses unverified live calls.
            adapter = ExtendedOpenAIAdapter(
                pid,
                default_model=spec["default_model"],
                secret_ref_names=env_vars,
                base_url="https://bedrock.invalid/v1",
                mode=mode,
                enabled=False,
            )
            out[pid] = ExtendedAdapterInfo(
                pid,
                protocol,
                True,
                "offline_shell_only_requires_boto_live",
                adapter,
            )
        else:
            out[pid] = ExtendedAdapterInfo(pid, protocol, False, "unsupported_protocol")
    return out
