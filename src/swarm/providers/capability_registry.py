"""Live provider capability registry (V0.2 P27).

Joins static catalog + env key presence + optional auth health probes.
Never logs secret values. Honors SWARM_ALLOW_PAID=false.

Fail-closed readiness (LEAD-009 / AUD-08):
- configured ≠ authenticated ≠ free-eligible ≠ inference-tested ≠ task-qualified
- Unknown stays unknown; key presence alone cannot promote a provider
- paid-mode=false alone never yields zero_spend_ok
- unprobed never becomes healthy/auth_ok/available/routable
- coding suitability stays unknown until measured qualification exists
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from swarm.envfile import load_repo_dotenv
from swarm.providers.catalog import DEFAULT_ENDPOINTS, RETIRED_PROVIDER_IDS, load_catalog

# Providers deferred / inference-blocked under zero-spend policy this pass.
DEFERRED_PROVIDERS = frozenset({"openai"})
PAID_INFERENCE_BLOCKED = frozenset({"together", "fireworks"})
# Local runtime whose free eligibility is proven only after a healthy probe.
LOCAL_FREE_PROVIDERS = frozenset({"ollama"})

# Auth probe endpoints (models.list style) — metadata only, no generation.
PROBE_SPECS: dict[str, dict[str, Any]] = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/models",
        "auth": "bearer",
        "env": "OPENROUTER_API_KEY",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/models",
        "auth": "bearer",
        "env": "GROQ_API_KEY",
    },
    "gemini": {
        "url_env": "GEMINI_API_KEY",
        "url_fmt": (
            "https://generativelanguage.googleapis.com/v1beta/models"
            "?key={key}&pageSize=1"
        ),
        "auth": "query",
        "env": "GEMINI_API_KEY",
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/models",
        "auth": "bearer",
        "env": "MISTRAL_API_KEY",
    },
    "cohere": {
        "url": "https://api.cohere.com/v1/models",
        "auth": "bearer",
        "env": "COHERE_API_KEY",
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/models",
        "auth": "anthropic",
        "env": "ANTHROPIC_API_KEY",
    },
    "nvidia_nim": {
        "url": "https://integrate.api.nvidia.com/v1/models",
        "auth": "bearer",
        "env": "NVIDIA_API_KEY",
    },
    "huggingface_inference": {
        "url": "https://huggingface.co/api/whoami-v2",
        "auth": "bearer",
        "env": "HF_TOKEN",
    },
    "deepinfra": {
        "url": "https://api.deepinfra.com/v1/openai/models",
        "auth": "bearer",
        "env": "DEEPINFRA_API_KEY",
    },
    "replicate": {
        "url": "https://api.replicate.com/v1/account",
        "auth": "token",
        "env": "REPLICATE_API_TOKEN",
    },
    "fireworks": {
        "url": "https://api.fireworks.ai/inference/v1/models",
        "auth": "bearer",
        "env": "FIREWORKS_API_KEY",
    },
    "together": {
        "url": "https://api.together.xyz/v1/models",
        "auth": "bearer",
        "env": "TOGETHER_API_KEY",
        "ua": True,
    },
    "ollama": {
        "url": "http://127.0.0.1:11434/api/tags",
        "auth": "none",
        "env": "OLLAMA_BASE_URL",
    },
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
    # high|medium|low|unknown|deferred — unknown until measured qualification
    coding_suitability: str = "unknown"
    # zero_spend_ok|paid_blocked|deferred|price_unverified|retired|unknown
    cost_policy: str = "unknown"
    rate_limits: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None
    health: str = "unknown"  # healthy|unhealthy|unprobed|blocked|deferred
    # unqualified|auth_ok|auth_ok_inference_blocked|benchmarked|routable|deferred
    qualification_status: str = "unqualified"
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


def _resolve_cost_policy(
    *,
    pid: str,
    retired: bool,
    paid: bool,
    health: str,
) -> tuple[str, str]:
    """Return (cost_policy, note_fragment). Never derives free from paid=false alone.

    OpenRouter free eligibility is route-level (see ``openrouter_free`` allowlist),
    never provider-level: a healthy auth probe does not make openrouter zero_spend_ok.
    """
    if retired:
        return "retired", "retired"
    if pid in DEFERRED_PROVIDERS:
        return "deferred", "payment-gated deferred"
    if pid in PAID_INFERENCE_BLOCKED and not paid:
        return (
            "paid_blocked",
            "key may exist; paid inference blocked under SWARM_ALLOW_PAID=false",
        )
    if paid:
        return "paid_allowed", "SWARM_ALLOW_PAID=true; exact-route pricing still unverified"
    # Local free only after a healthy probe proves the runtime is reachable.
    if pid in LOCAL_FREE_PROVIDERS and health == "healthy":
        return "zero_spend_ok", "local free route verified by healthy probe"
    # Remote / unprobed / unhealthy: price and free-eligibility remain unknown.
    # OpenRouter :free allowlist is checked at canary/admission route scope only.
    if pid == "openrouter":
        return (
            "price_unverified",
            "provider-level free not granted; use openrouter_free allowlisted routes only",
        )
    return "price_unverified", "free eligibility not proven; paid-mode=false is not sufficient"


def build_capability_registry(*, probe: bool = True, repo: Path | None = None) -> dict[str, Any]:
    root = repo or _repo_root()
    load_repo_dotenv(root)
    catalog = load_catalog()
    paid = _paid_allowed()
    records: list[ProviderCapabilityRecord] = []
    now = datetime.now(UTC).isoformat()

    for entry in catalog.get("providers", []):
        pid = entry["id"]
        retired = pid in RETIRED_PROVIDER_IDS or entry.get("service_status") == "retired"
        env_vars = list(entry.get("env_vars") or [])
        if pid == "ollama" and "OLLAMA_BASE_URL" not in env_vars:
            env_vars = ["OLLAMA_BASE_URL"]
        key_ok = False if retired else _env_configured(env_vars) if env_vars else True
        if pid == "ollama":
            key_ok = True  # local default endpoint; still requires healthy probe

        health = "unprobed"
        notes = ""
        latency = None
        model_count = None
        qual = "unqualified"
        # Never invent task suitability from provider identity.
        coding = "unknown"

        if retired:
            health = "blocked"
            key_ok = False
        elif pid in DEFERRED_PROVIDERS:
            health = "deferred"
            coding = "deferred"
            qual = "deferred"

        if (
            key_ok
            and not retired
            and pid not in DEFERRED_PROVIDERS
            and probe
            and pid in PROBE_SPECS
        ):
            health, latency, model_count, notes2 = _probe(pid)
            notes = (notes + "; " if notes else "") + notes2
            if health == "healthy":
                # Metadata/auth probe only — not inference permission or quality.
                qual = "auth_ok"

        cost_policy, cost_note = _resolve_cost_policy(
            pid=pid, retired=retired, paid=paid, health=health
        )
        notes = (notes + "; " if notes else "") + cost_note

        if pid in PAID_INFERENCE_BLOCKED and not paid and health == "healthy":
            qual = "auth_ok_inference_blocked"

        # Cloudflare (and any provider without a live probe this pass) stays
        # unprobed when not probed — never promote key presence to healthy/auth_ok.
        if pid == "cloudflare_workers_ai" and health == "unprobed":
            notes = (notes + "; " if notes else "") + (
                "account+token may be configured; models.search deferred; "
                "unprobed remains unqualified"
            )

        # Fail closed: unprobed/unknown/price-unverified never count as available.
        if paid:
            available = bool(
                key_ok
                and health == "healthy"
                and pid not in DEFERRED_PROVIDERS
                and not retired
                and cost_policy not in {"paid_blocked", "deferred", "retired"}
            )
        else:
            available = bool(
                key_ok
                and health == "healthy"
                and cost_policy == "zero_spend_ok"
                and pid not in DEFERRED_PROVIDERS
                and not retired
            )

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
        # Only truly available rows — not inference-blocked auth_ok entries.
        "available_for_routing": sum(1 for r in records if r.available),
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
    """Providers safe for zero-spend routing. Fail closed on unknown/unprobed."""
    data = report or build_capability_registry(probe=False)
    rows = []
    for p in data.get("providers", []):
        health = p.get("health")
        qual = p.get("qualification_status")
        cost = p.get("cost_policy")
        if health != "healthy":
            continue
        if cost != "zero_spend_ok":
            continue
        if qual not in {"auth_ok", "benchmarked", "routable"}:
            continue
        rows.append(p)
    return rows
