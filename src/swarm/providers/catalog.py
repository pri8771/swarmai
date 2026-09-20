"""Provider catalog loading and listing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swarm.contracts.enums import AccountStatus, AvailabilityStatus

CORE_PROVIDER_IDS = (
    "openrouter",
    "groq",
    "gemini",
    "cloudflare_workers_ai",
    "huggingface_inference",
    "nvidia_nim",
    "mistral",
    "cohere",
    "cerebras",
    "ollama",
)

RETIRED_PROVIDER_IDS = ("github_models",)

DEFAULT_ENDPOINTS: dict[str, str] = {
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "cloudflare_workers_ai": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
    "huggingface_inference": "https://router.huggingface.co/v1",
    "nvidia_nim": "https://integrate.api.nvidia.com/v1",
    "mistral": "https://api.mistral.ai/v1",
    "cohere": "https://api.cohere.com/v2",
    "cerebras": "https://api.cerebras.ai/v1",
    "ollama": "http://127.0.0.1:11434/v1",
}


def catalog_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / "provider-catalog.json"


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    target = path or catalog_path()
    data = json.loads(target.read_text())
    assert isinstance(data, dict)
    return data


def list_providers(*, mode: str = "mock") -> list[dict[str, Any]]:
    catalog = load_catalog()
    rows: list[dict[str, Any]] = []
    for entry in catalog.get("providers", []):
        pid = entry["id"]
        retired = pid in RETIRED_PROVIDER_IDS or entry.get("service_status") == "retired"
        implemented = pid in CORE_PROVIDER_IDS
        rows.append(
            {
                "id": pid,
                "name": entry.get("name"),
                "wave": entry.get("implementation_wave"),
                "enabled": False if retired else bool(entry.get("enabled")),
                "retired": retired,
                "adapter_status": (
                    "retired"
                    if retired
                    else ("implemented_offline" if implemented else entry.get("adapter_status"))
                ),
                "account_status": entry.get("account_status", AccountStatus.UNKNOWN.value),
                "availability": (
                    AvailabilityStatus.RETIRED.value
                    if retired
                    else AvailabilityStatus.DISABLED.value
                ),
                "mode": mode,
                "env_vars": entry.get("env_vars", []),
                "base_url": entry.get("base_url") or DEFAULT_ENDPOINTS.get(pid),
            }
        )
    return rows
