"""Bounded canary probes — mock by default; live only for known-zero routes.

Known-zero live paths (fail-closed):
- loopback local runtimes in ``LOCAL_ZERO_COST_PROVIDERS`` (ollama)
- explicit OpenRouter free-route allowlist (``:free`` model + pinned backend)
"""

from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from swarm.broker.explain import build_mock_broker
from swarm.contracts.common import utc_now
from swarm.contracts.enums import ReservationPhase, SettlementState
from swarm.contracts.provider import InferenceRequest, Reservation
from swarm.envfile import load_repo_dotenv
from swarm.onboarding.status import RouteOnboardingStatus
from swarm.providers.catalog import DEFAULT_ENDPOINTS
from swarm.providers.openrouter_free import resolve_openrouter_free_route

# Local operator compute — no cloud bill when bound to loopback.
LOCAL_ZERO_COST_PROVIDERS = frozenset({"ollama"})
OPENROUTER_SECRET_REF = "OPENROUTER_API_KEY"


class CanaryDeniedError(PermissionError):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _is_loopback_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def _provider_from_route(route_id: str) -> str | None:
    if not route_id.startswith("rt_"):
        return None
    rest = route_id[3:]
    for pid in sorted(LOCAL_ZERO_COST_PROVIDERS, key=len, reverse=True):
        if rest == pid or rest.startswith(f"{pid}_"):
            return pid
    return None


def _model_from_route(route_id: str, provider_id: str) -> str | None:
    prefix = f"rt_{provider_id}_"
    if not route_id.startswith(prefix):
        return None
    model = route_id[len(prefix) :]
    if not model or model == "default":
        return None
    return model


def _canary_evidence_dir() -> Path:
    path = _repo_root() / "var" / "onboarding" / "canaries"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_canary_evidence(route_id: str, payload: dict[str, Any]) -> Path:
    safe = route_id.replace("/", "_").replace(":", "_")
    path = _canary_evidence_dir() / f"{safe}.json"
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def load_canary_evidence(route_id: str) -> dict[str, Any] | None:
    safe = route_id.replace("/", "_").replace(":", "_")
    path = _canary_evidence_dir() / f"{safe}.json"
    if not path.is_file():
        return None
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else None


async def _live_local_zero_canary(
    *,
    route_id: str,
    provider_id: str,
    purpose: str,
) -> dict[str, Any]:
    """Execute one synthetic live probe against a loopback local runtime."""
    load_repo_dotenv(_repo_root())
    if provider_id == "ollama":
        base_url = (
            os.environ.get("OLLAMA_BASE_URL") or DEFAULT_ENDPOINTS["ollama"]
        ).rstrip("/")
    else:
        return {
            "route_id": route_id,
            "status": RouteOnboardingStatus.DISABLED.value,
            "denied": True,
            "reason": f"live_canary_unsupported_provider:{provider_id}",
            "mock_vs_live": "not_live",
            "consumed_allowance": 0,
        }

    if not _is_loopback_url(base_url):
        return {
            "route_id": route_id,
            "status": RouteOnboardingStatus.UNKNOWN_COST_DENIED.value,
            "denied": True,
            "reason": "local_provider_endpoint_not_loopback",
            "mock_vs_live": "live_blocked",
            "user_action_required": [
                "Point OLLAMA_BASE_URL at http://127.0.0.1:11434/v1 for known-zero local canary",
            ],
            "consumed_allowance": 0,
        }

    from swarm.providers.core.adapters import OllamaAdapter

    preferred = _model_from_route(route_id, provider_id)
    adapter = OllamaAdapter(
        mode="live",
        enabled=True,
        base_url=base_url,
        secret_ref_names=[],
        account_id="pa_local_ollama",
    )
    if preferred:
        adapter.default_model = preferred
        adapter._routes.clear()
        adapter._seed_default_route()

    routes = await adapter.discover()
    discovered = [r for r in routes if r.route_id != f"rt_{provider_id}_default"]
    by_model = {r.model_id: r for r in discovered}
    target = None
    if preferred and preferred in by_model:
        target = by_model[preferred]
    if target is None:
        for mid in ("gemma3:4b", "qwen2.5vl:3b", "qwen3.5:4b"):
            if mid in by_model:
                target = by_model[mid]
                break
    if target is None and discovered:
        target = discovered[0]
    if target is None:
        return {
            "route_id": route_id,
            "status": RouteOnboardingStatus.DISABLED.value,
            "denied": True,
            "reason": "no_local_models_discovered",
            "mock_vs_live": "not_live",
            "user_action_required": [
                "Start Ollama locally and pull at least one chat model (e.g. gemma3:4b)",
            ],
            "consumed_allowance": 0,
        }

    request = InferenceRequest(
        project_id="proj_onboarding",
        attempt_id="att_canary_live_local",
        route_id=target.route_id,
        purpose=purpose,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        estimated_input_tokens=16,
        max_output_tokens=8,
        secret_ref_names=[],
    )
    ticket = Reservation(
        logical_call_id="lc_canary_live_local",
        attempt_id=request.attempt_id,
        route_id=target.route_id,
        expires_at=utc_now() + timedelta(minutes=2),
        phase=ReservationPhase.RESERVED,
    )
    receipt = await adapter.execute_one(request, ticket)
    ok = (
        receipt.error_class is None
        and receipt.settlement_state == SettlementState.SETTLED
    )
    result: dict[str, Any] = {
        "route_id": target.route_id,
        "requested_route_id": route_id,
        "provider_id": provider_id,
        "model_id": target.model_id,
        "status": (
            RouteOnboardingStatus.CANARIED.value
            if ok
            else RouteOnboardingStatus.DISABLED.value
        ),
        "denied": not ok,
        "probe_counted": True,
        "consumed_allowance": 1,
        "mock_vs_live": "live_local_zero_cost",
        "billing_known_zero": True,
        "endpoint_loopback": True,
        "purpose": purpose,
        "settlement_state": receipt.settlement_state.value,
        "error_class": None if receipt.error_class is None else receipt.error_class.value,
        "provider_request_id": receipt.provider_request_id,
        "model_fingerprint": (
            (receipt.normalized_usage.extras or {}).get("upstream_model")
            if receipt.normalized_usage is not None
            else None
        )
        or target.model_id,
        "layers": {
            "cataloged": True,
            "configured": bool(os.environ.get("OLLAMA_BASE_URL")),
            "authenticated": ok,
            "inference_tested": ok,
        },
    }
    if not ok:
        result["reason"] = "live_local_probe_failed"
    result["cost_usd"] = 0.0
    evidence_path = _write_canary_evidence(target.route_id, result)
    result["evidence_path"] = str(evidence_path.relative_to(_repo_root()))
    # Also alias requested route id when it differed (e.g. rt_ollama_default).
    if target.route_id != route_id:
        _write_canary_evidence(route_id, result)
    return result


async def _live_openrouter_free_canary(
    *,
    route_id: str,
    purpose: str,
) -> dict[str, Any]:
    """Execute one synthetic live probe against an allowlisted OpenRouter free route."""
    load_repo_dotenv(_repo_root())
    free = resolve_openrouter_free_route(route_id)
    if free is None:
        return {
            "route_id": route_id,
            "status": RouteOnboardingStatus.DISABLED.value,
            "denied": True,
            "reason": "openrouter_route_not_on_free_allowlist",
            "mock_vs_live": "not_live",
            "cost_usd": 0.0,
            "secret_ref_names": [OPENROUTER_SECRET_REF],
            "consumed_allowance": 0,
        }

    if not os.environ.get(OPENROUTER_SECRET_REF, "").strip():
        return {
            "route_id": route_id,
            "model_id": free.model_id,
            "provider_id": "openrouter",
            "status": RouteOnboardingStatus.DISABLED.value,
            "denied": True,
            "reason": "missing_OPENROUTER_API_KEY",
            "mock_vs_live": "not_live",
            "cost_usd": 0.0,
            "secret_ref_names": [OPENROUTER_SECRET_REF],
            "user_action_required": [
                "USER_ACTION: Set OPENROUTER_API_KEY in the gitignored repo .env "
                "(or process environment). Do not paste the key into chat.",
                "Then re-run: swarm providers canary "
                f"--route {free.route_id} --policy bounded_probe "
                "--mode live --billing-known-zero",
            ],
            "consumed_allowance": 0,
        }

    from swarm.providers.core.adapters import OpenRouterAdapter

    adapter = OpenRouterAdapter(
        mode="live",
        enabled=True,
        free_route=free,
        secret_ref_names=[OPENROUTER_SECRET_REF],
        account_id="pa_openrouter_operator",
    )
    routes = await adapter.discover()
    target = next((r for r in routes if r.route_id == free.route_id), None)
    if target is None:
        return {
            "route_id": route_id,
            "status": RouteOnboardingStatus.DISABLED.value,
            "denied": True,
            "reason": "openrouter_free_route_not_seeded",
            "mock_vs_live": "not_live",
            "cost_usd": 0.0,
            "secret_ref_names": [OPENROUTER_SECRET_REF],
            "consumed_allowance": 0,
        }

    request = InferenceRequest(
        project_id="proj_onboarding",
        attempt_id="att_canary_live_openrouter_free",
        route_id=target.route_id,
        purpose=purpose,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        estimated_input_tokens=16,
        max_output_tokens=8,
        secret_ref_names=[OPENROUTER_SECRET_REF],
    )
    ticket = Reservation(
        logical_call_id="lc_canary_live_openrouter_free",
        attempt_id=request.attempt_id,
        route_id=target.route_id,
        expires_at=utc_now() + timedelta(minutes=2),
        phase=ReservationPhase.RESERVED,
    )
    receipt = await adapter.execute_one(request, ticket)
    ok = (
        receipt.error_class is None
        and receipt.settlement_state == SettlementState.SETTLED
    )
    result: dict[str, Any] = {
        "route_id": target.route_id,
        "requested_route_id": route_id,
        "provider_id": "openrouter",
        "model_id": free.model_id,
        "hosted_by": free.provider_slug,
        "status": (
            RouteOnboardingStatus.CANARIED.value
            if ok
            else RouteOnboardingStatus.DISABLED.value
        ),
        "denied": not ok,
        "probe_counted": True,
        "consumed_allowance": 1,
        "mock_vs_live": "live_remote_zero_cost",
        "billing_known_zero": True,
        "cost_usd": 0.0,
        "secret_ref_names": [OPENROUTER_SECRET_REF],
        "purpose": purpose,
        "settlement_state": receipt.settlement_state.value,
        "error_class": None if receipt.error_class is None else receipt.error_class.value,
        "provider_request_id": receipt.provider_request_id,
        "model_fingerprint": (
            (receipt.normalized_usage.extras or {}).get("upstream_model")
            if receipt.normalized_usage is not None
            else None
        )
        or free.model_id,
        "layers": {
            "cataloged": True,
            "configured": True,
            "authenticated": ok,
            "inference_tested": ok,
            "free_allowlisted": True,
        },
    }
    if not ok:
        result["reason"] = "live_openrouter_free_probe_failed"
    evidence_path = _write_canary_evidence(target.route_id, result)
    result["evidence_path"] = str(evidence_path.relative_to(_repo_root()))
    if target.route_id != route_id:
        _write_canary_evidence(route_id, result)
    return result


async def bounded_canary(
    *,
    route_id: str,
    policy: str = "bounded_probe",
    mode: str = "mock",
    allow_paid: bool = False,
    billing_known_zero: bool = False,
    purpose: str = "prototype",
) -> dict[str, Any]:
    """Run a counted synthetic probe through the broker when allowed.

    Live probes run only for known-zero local runtimes (loopback Ollama) or
    explicit OpenRouter free-route allowlist entries.
    """
    if policy != "bounded_probe":
        raise CanaryDeniedError(f"unsupported_policy:{policy}")
    if allow_paid:
        raise CanaryDeniedError("paid_routes_denied_in_no_spend_mode")
    if mode == "live" and not billing_known_zero:
        return {
            "route_id": route_id,
            "status": RouteOnboardingStatus.UNKNOWN_COST_DENIED.value,
            "denied": True,
            "reason": "unknown_or_paid_cost_cannot_canary",
            "mock_vs_live": "live_blocked",
            "consumed_allowance": 0,
        }
    if mode == "live" and billing_known_zero:
        free = resolve_openrouter_free_route(route_id)
        if free is not None:
            return await _live_openrouter_free_canary(route_id=route_id, purpose=purpose)
        # Non-allowlisted openrouter (including :free models not pinned) stay denied.
        if route_id.startswith("rt_openrouter_"):
            return {
                "route_id": route_id,
                "status": RouteOnboardingStatus.DISABLED.value,
                "denied": True,
                "reason": "openrouter_route_not_on_free_allowlist",
                "mock_vs_live": "not_live",
                "cost_usd": 0.0,
                "secret_ref_names": [OPENROUTER_SECRET_REF],
                "user_action_required": [
                    "Only allowlisted OpenRouter :free routes may live-canary "
                    "under SWARM_ALLOW_PAID=false",
                    "Use an allowlisted route id (see openrouter_free_route_ids)",
                ],
                "consumed_allowance": 0,
            }
        provider_id = _provider_from_route(route_id)
        if provider_id is None or provider_id not in LOCAL_ZERO_COST_PROVIDERS:
            return {
                "route_id": route_id,
                "status": RouteOnboardingStatus.DISABLED.value,
                "denied": True,
                "reason": "live_canary_requires_operator_keys_and_zero_charge_proof",
                "mock_vs_live": "not_live",
                "user_action_required": [
                    "Only loopback local runtimes (ollama) or allowlisted "
                    "OpenRouter free routes are live-canary eligible under spend=zero",
                    "For OpenRouter: set OPENROUTER_API_KEY in local .env, use an "
                    "allowlisted rt_openrouter_<model:free> route, then re-run with "
                    "--billing-known-zero",
                    "Re-run: swarm providers canary --route ROUTE_ID "
                    "--policy bounded_probe --mode live --billing-known-zero",
                ],
                "consumed_allowance": 0,
            }
        return await _live_local_zero_canary(
            route_id=route_id, provider_id=provider_id, purpose=purpose
        )
    if mode != "mock":
        return {
            "route_id": route_id,
            "status": RouteOnboardingStatus.DISABLED.value,
            "denied": True,
            "reason": "live_canary_requires_operator_keys_and_zero_charge_proof",
            "mock_vs_live": "not_live",
            "user_action_required": [
                "Set provider API key in local secret store (env ref only)",
                "Confirm zero-charge eligibility for the exact route",
                "Re-run: swarm providers canary --route ROUTE_ID "
                "--policy bounded_probe --mode live --billing-known-zero",
            ],
            "consumed_allowance": 0,
        }

    broker = build_mock_broker()
    request = InferenceRequest(
        project_id="proj_onboarding",
        attempt_id="att_canary_bounded",
        route_id=route_id if route_id.startswith("rt_") else None,
        purpose=purpose,
        messages=[{"role": "user", "content": "synthetic onboarding canary"}],
        estimated_input_tokens=16,
        max_output_tokens=8,
        secret_ref_names=[],
    )
    eligible = await broker.assess(request)
    counted = True
    return {
        "route_id": route_id,
        "status": RouteOnboardingStatus.CANARIED.value,
        "denied": False,
        "eligible_route_count": len(eligible),
        "probe_counted": counted,
        "consumed_allowance": 1 if eligible else 0,
        "mock_vs_live": "mock_broker_fixtures_only",
        "purpose": purpose,
    }
