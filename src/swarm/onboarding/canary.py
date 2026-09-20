"""Bounded canary probes — mock by default; live blocked without policy."""

from __future__ import annotations

from typing import Any

from swarm.broker.explain import build_mock_broker
from swarm.contracts.provider import InferenceRequest
from swarm.onboarding.status import RouteOnboardingStatus


class CanaryDeniedError(PermissionError):
    pass


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

    Live network probes are not executed in this offline scaffolding.
    """
    if policy != "bounded_probe":
        raise CanaryDeniedError(f"unsupported_policy:{policy}")
    if allow_paid:
        raise CanaryDeniedError("paid_routes_denied_in_no_spend_mode")
    if not billing_known_zero and mode == "live":
        return {
            "route_id": route_id,
            "status": RouteOnboardingStatus.UNKNOWN_COST_DENIED.value,
            "denied": True,
            "reason": "unknown_or_paid_cost_cannot_canary",
            "mock_vs_live": "live_blocked",
            "consumed_allowance": 0,
        }
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
                "--policy bounded_probe --mode live",
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
