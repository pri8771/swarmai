"""Live provider capability registry (V0.2 P27).

Joins static catalog + env key presence + optional auth health probes.
Never logs secret values. Honors SWARM_ALLOW_PAID=false.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.envfile import load_repo_dotenv
from swarm.providers.catalog import DEFAULT_ENDPOINTS, RETIRED_PROVIDER_IDS, load_catalog

# Providers deferred / inference-blocked under zero-spend policy this pass.
DEFERRED_PROVIDERS = frozenset({"openai"})
PAID_INFERENCE_BLOCKED = frozenset({"together", "fireworks"})

# Auth probe endpoints (models.list style) — metadata only, no generation.
PROBE_SPECS: dict[str, dict[str, Any]] = {
    "openrouter": {"url": "https://openrouter.ai/api/v1/models", "auth": "bearer", "env": "OPENROUTER_API_KEY"},
    "groq": {"url": "https://api.groq.com/openai/v1/models", "auth": "bearer", "env": "GROQ_API_KEY"},
    "gemini": {"url_env": "GEMINI_API_KEY", "url_fmt": "https://generativelanguage.googleapis.com/v1beta/models?key={key}&pageSize=1", "auth": "query", "env": "GEMINI_API_KEY"},
    "mistral": {"url": "https://api.mistral.ai/v1/models", "auth": "bearer", "env": "MISTRAL_API_KEY"},
    "cohere": {"url": "https://api.cohere.com/v1/models", "auth": "bearer", "env": "COHERE_API_KEY"},
    "anthropic": {"url": "https://api.anthropic.com/v1/models", "auth": "anthropic", "env": "ANTHROPIC_API_KEY"},
    "nvidia_nim": {"url": "https://integrate.api.nvidia.com/v1/models", "auth": "bearer", "env": "NVIDIA_API_KEY"},
    "huggingface_inference": {"url": "https://huggingface.co/api/whoami-v2", "auth": "bearer", "env": "HF_TOKEN"},
    "deepinfra": {"url": "https://api.deepinfra.com/v1/openai/models", "auth": "bearer", "env": "DEEPINFRA_API_KEY"},
    "replicate": {"url": "https://api.replicate.com/v1/account", "auth": "token", "env": "REPLICATE_API_TOKEN"},
    "fireworks": {"url": "https://api.fireworks.ai/inference/v1/models", "auth": "bearer", "env": "FIREWORKS_API_KEY"},
    "together": {"url": "https://api.together.xyz/v1/models", "auth": "bearer", "env": "TOGETHER_API_KEY", "ua": True},
    "ollama": {"url": "http://127.0.0.1:11434/api/tags", "auth": "none", "env": "OLLAMA_BASE_URL"},
}


@dataclass
class ProviderCapabilityRecord:
    provider_id: str
    name: str
    available: bool
    key_configured: bool
    env_refs: list[str] = field(default_factory=list)
    base_url: str | None = None
    modalities: list[str] = field(default_factory=lambda: ["chat"])
    coding_suitability: str = "unknown"  # high|medium|low|unknown|deferred
    cost_policy: str = "unknown"  # zero_spend_ok|paid_blocked|deferred|unknown
    rate_limits: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None
    health: str = "unknown"  # healthy|unhealthy|unprobed|blocked|deferred
    qualification_status: str = "unqualified"  # unqualified|auth_ok|benchmarked|routable
    context_window: int | None = None
    model_count: int | None = None
    notes: str = ""
    probed_at: str | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _paid_allowed() -> bool:
    return os.environ.get("SWARM_ALLOW_PAID", "false").lower() in {"1", "true", "yes"}


def _env_configured(env_vars: list[str]) -> bool:
    if not env_vars:
        # ollama may only need base URL default
        return True
    return all(bool(os.environ.get(v, "").strip()) for v in env_vars)


def _probe(provider_id: str) -> tuple[str, float | None, int | None, str]:
    """Return (health, latency_ms, model_count, note). Never returns secrets."""
    spec = PROBE_SPECS.get(provider_id)
    if not spec:
        return "unprobed", None, None, "no probe spec"
    env_name = spec["env"]
    key = os.environ.get(env_name, "").strip()
    if spec["auth"] != "none" and not key:
        return "unprobed", None, None, f"missing {env_name}"
    if provider_id == "ollama":
        url = "http://127.0.0.1:11434/api/tags"
    elif spec.get("url_fmt"):
        url = spec["url_fmt"].format(key=key)
    else:
        url = spec["url"]
    headers = {"Accept": "application/json", "User-Agent": "SwarmAI/0.2-capability-registry"}
    if spec["auth"] == "bearer":
        headers["Authorization"] = f"Bearer {key}"
    elif spec["auth"] == "token":
        headers["Authorization"] = f"Token {key}"
    elif spec["auth"] == "anthropic":
        headers["x-api-key"] = key
        headers["anthropic-version"] = "2023-06-01"
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
        latency = (time.perf_counter() - start) * 1000.0
        data: Any
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return "healthy", latency, None, "ok non-json"
        count = None
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                count = len(data["data"])
            elif "models" in data and isinstance(data["models"], list):
                count = len(data["models"])
            elif "name" in data:  # HF whoami
                count = 1
        elif isinstance(data, list):
            count = len(data)
        return "healthy", latency, count, "auth probe ok"
    except urllib.error.HTTPError as exc:
        latency = (time.perf_counter() - start) * 1000.0
        return "unhealthy", latency, None, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 — probe must never raise
        latency = (time.perf_counter() - start) * 1000.0
        return "unhealthy", latency, None, type(exc).__name__


def build_capability_registry(*, probe: bool = True, repo: Path | None = None) -> dict[str, Any]:
    root = repo or _repo_root()
    load_repo_dotenv(root)
    catalog = load_catalog()
    paid = _paid_allowed()
    records: list[ProviderCapabilityRecord] = []
    now = datetime.now(timezone.utc).isoformat()

    for entry in catalog.get("providers", []):
        pid = entry["id"]
        retired = pid in RETIRED_PROVIDER_IDS or entry.get("service_status") == "retired"
        env_vars = list(entry.get("env_vars") or [])
        if pid == "ollama" and "OLLAMA_BASE_URL" not in env_vars:
            env_vars = ["OLLAMA_BASE_URL"]
        key_ok = False if retired else _env_configured(env_vars) if env_vars else True
        if pid == "ollama":
            key_ok = True  # local default endpoint

        cost_policy = "unknown"
        coding = "unknown"
        health = "unprobed"
        notes = ""
        latency = None
        model_count = None
        qual = "unqualified"

        if retired:
            cost_policy = "retired"
            health = "blocked"
            notes = "retired"
            key_ok = False
        elif pid in DEFERRED_PROVIDERS:
            cost_policy = "deferred"
            health = "deferred"
            coding = "deferred"
            notes = "payment-gated deferred"
            qual = "deferred"
        elif pid in PAID_INFERENCE_BLOCKED and not paid:
            cost_policy = "paid_blocked"
            notes = "key may exist; paid inference blocked under SWARM_ALLOW_PAID=false"
        else:
            cost_policy = "zero_spend_ok" if not paid else "paid_allowed"

        if key_ok and not retired and pid not in DEFERRED_PROVIDERS and probe and pid in PROBE_SPECS:
            health, latency, model_count, notes2 = _probe(pid)
            notes = (notes + "; " if notes else "") + notes2
            if health == "healthy":
                qual = "auth_ok"
                if pid in {"ollama", "groq", "openrouter", "gemini", "mistral", "cohere", "anthropic", "nvidia_nim", "huggingface_inference", "deepinfra", "replicate", "cloudflare_workers_ai"}:
                    coding = "medium"
                if pid == "ollama":
                    coding = "high"  # local always preferred for zero-spend dogfood

        if pid in PAID_INFERENCE_BLOCKED and not paid and health == "healthy":
            qual = "auth_ok_inference_blocked"

        available = bool(key_ok and health in {"healthy", "unprobed"} and pid not in DEFERRED_PROVIDERS and not retired)
        if pid in PAID_INFERENCE_BLOCKED and not paid:
            available = False  # not available for inference routing

        # Cloudflare needs both token + account; probe is heavier — mark key-only if configured
        if pid == "cloudflare_workers_ai" and key_ok and probe:
            # Prefer treating configured CF as auth_ok without generation
            if health == "unprobed":
                health = "healthy"
                qual = "auth_ok"
                coding = "medium"
                notes = (notes + "; " if notes else "") + "account+token configured; models.search deferred"

        records.append(
            ProviderCapabilityRecord(
                provider_id=pid,
                name=str(entry.get("name") or pid),
                available=available,
                key_configured=key_ok,
                env_refs=env_vars,
                base_url=entry.get("base_url") or DEFAULT_ENDPOINTS.get(pid),
                modalities=["chat"],
                coding_suitability=coding,
                cost_policy=cost_policy,
                rate_limits={},
                latency_ms=latency,
                health=health,
                qualification_status=qual,
                context_window=None,
                model_count=model_count,
                notes=notes,
                probed_at=now if probe else None,
            )
        )

    out = {
        "schema_version": "0.2.0",
        "generated_at": now,
        "swarm_allow_paid": paid,
        "provider_count": len(records),
        "available_for_routing": sum(1 for r in records if r.available or r.qualification_status in {"auth_ok", "auth_ok_inference_blocked"}),
        "auth_ok": sum(1 for r in records if r.qualification_status.startswith("auth_ok")),
        "providers": [asdict(r) for r in records],
    }
    return out


def save_capability_registry(report: dict[str, Any], *, repo: Path | None = None) -> Path:
    root = repo or _repo_root()
    path = root / "var" / "providers" / "capability-registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    return path


def routable_providers(report: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = report or build_capability_registry(probe=False)
    rows = []
    for p in data.get("providers", []):
        if p.get("qualification_status") in {"auth_ok", "benchmarked", "routable"} and p.get("cost_policy") == "zero_spend_ok":
            rows.append(p)
        elif p.get("provider_id") == "ollama" and p.get("health") in {"healthy", "unprobed"}:
            rows.append(p)
    return rows
