"""Registry of core provider adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from swarm.providers.catalog import CORE_PROVIDER_IDS, RETIRED_PROVIDER_IDS, load_catalog
from swarm.providers.core.adapters import CORE_ADAPTER_TYPES
from swarm.providers.core.base import BaseCoreAdapter
from swarm.providers.transport.openai_compatible import TransportMode

ENV_DEFAULTS: dict[str, list[str]] = {
    "openrouter": ["OPENROUTER_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "gemini": ["GEMINI_API_KEY"],
    "cloudflare_workers_ai": ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"],
    "huggingface_inference": ["HF_TOKEN"],
    "nvidia_nim": ["NVIDIA_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "cohere": ["COHERE_API_KEY"],
    "cerebras": ["CEREBRAS_API_KEY"],
    "ollama": [],
}


def build_core_adapters(
    *,
    mode: TransportMode = "replay",
    fixtures_dir: Path | None = None,
    enabled: bool = False,
) -> dict[str, BaseCoreAdapter]:
    catalog = load_catalog()
    by_id = {p["id"]: p for p in catalog.get("providers", [])}
    adapters: dict[str, BaseCoreAdapter] = {}
    for pid in CORE_PROVIDER_IDS:
        if pid in RETIRED_PROVIDER_IDS:
            continue
        cls = CORE_ADAPTER_TYPES[pid]
        entry = by_id.get(pid, {})
        fixture = None
        if fixtures_dir is not None:
            fixture = fixtures_dir / f"{pid}.json"
        adapters[pid] = cls(
            secret_ref_names=entry.get("env_vars") or ENV_DEFAULTS.get(pid, []),
            base_url=entry.get("base_url"),
            mode=mode,
            fixture_path=fixture,
            enabled=enabled,
        )
    return adapters


def assert_github_models_inactive(adapters: dict[str, Any]) -> None:
    if "github_models" in adapters:
        raise RuntimeError("github_models must never be registered as an active adapter")
