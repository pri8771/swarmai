"""Capacity explain helpers for CLI and operator console."""

from __future__ import annotations

from typing import Any

from swarm.broker.broker import SharedInferenceBroker
from swarm.broker.ledger import LedgerConfig
from swarm.broker.policy import AdmissionPolicy, RoutePolicyContext
from swarm.contracts.enums import (
    AvailabilityStatus,
    BillingMode,
    PurposeEligibility,
    QuotaDimension,
    WindowType,
)
from swarm.contracts.fixtures import sample_quota, sample_route, sample_route_beta
from swarm.contracts.provider import InferenceRequest, ProviderAccount, QuotaBucket, RouteSnapshot
from swarm.fakes.provider import FakeProviderAdapter


def build_mock_broker() -> SharedInferenceBroker:
    """Offline mock capacity plane — not live inference."""
    routes = [sample_route(), sample_route_beta()]
    # Shared upstream quota group (BYOK + direct share qb_demo_requests).
    buckets = [
        sample_quota(),
        QuotaBucket(
            bucket_id="qb_control_reserve",
            scope_type="mission",
            scope_id="mission_demo",
            dimension=QuotaDimension.REQUESTS,
            limit=20,
            remaining=20,
            window_type=WindowType.LIFETIME,
            source="fixture",
            confidence="exact",
        ),
        QuotaBucket(
            bucket_id="qb_benchmark",
            scope_type="project",
            scope_id="proj_demo",
            dimension=QuotaDimension.REQUESTS,
            limit=10,
            remaining=10,
            window_type=WindowType.LIFETIME,
            source="fixture",
            confidence="exact",
        ),
        QuotaBucket(
            bucket_id="qb_tokens",
            scope_type="account",
            scope_id="pa_openrouter_demo",
            dimension=QuotaDimension.TOTAL_TOKENS,
            limit=50_000,
            remaining=50_000,
            window_type=WindowType.ROLLING,
            source="fixture",
            confidence="exact",
        ),
    ]
    for r in routes:
        if "qb_tokens" not in r.quota_bucket_ids:
            r.quota_bucket_ids = [*r.quota_bucket_ids, "qb_tokens", "qb_control_reserve"]

    adapter = FakeProviderAdapter(routes=routes)
    account = ProviderAccount(
        id="pa_openrouter_demo",
        service_id="fake",
        account_alias="mock",
        secret_ref_names=["FAKE_API_KEY"],
        owner="operator",
        purpose_eligibility=PurposeEligibility.PROTOTYPE,
        billing_mode=BillingMode.NONE,
    )
    contexts = {
        r.route_id: RoutePolicyContext(
            route=r,
            account=account,
            qualified=True,
            qualification_rationale="fixture_qualified",
            billing_mode=BillingMode.NONE,
            purpose_eligibility=PurposeEligibility.PROTOTYPE,
            charge_verified_free=True,
            shared_upstream_group="upstream_fake_demo",
        )
        for r in routes
    }
    return SharedInferenceBroker(
        adapter,
        buckets,
        route_contexts=contexts,
        policy=AdmissionPolicy(allow_unknown_billing=False, allow_paid=False),
        ledger_config=LedgerConfig(
            planning_review_reserve=2,
            allow_unknown_probe=True,
            verified_no_charge_routes={r.route_id for r in routes},
        ),
    )


async def explain_capacity(*, mode: str, purpose: str = "mission") -> dict[str, Any]:
    if mode != "mock":
        return {
            "mode": mode,
            "error": "live_capacity_explain_requires_configured_accounts",
            "mock_vs_live": "not_live",
        }
    broker = build_mock_broker()
    request = InferenceRequest(
        project_id="proj_demo",
        attempt_id="att_capacity_explain",
        route_id=None,
        purpose=purpose,
        messages=[{"role": "user", "content": "capacity explain"}],
        estimated_input_tokens=40,
        max_output_tokens=100,
        secret_ref_names=[],
    )
    eligible = await broker.assess(request)
    decision_id = broker.last_decision_id or ""
    explanation = await broker.explain(decision_id)
    bucket_views = []
    for b in broker.ledger.snapshot():
        bucket_views.append(
            {
                "bucket_id": b.bucket_id,
                "dimension": b.dimension.value,
                "remaining": b.remaining,
                "limit": b.limit,
                "window_type": b.window_type.value,
            }
        )
    return {
        "mode": "mock",
        "mock_vs_live": "mock_fixtures_only",
        "eligible_route_count": len(eligible),
        "buckets": bucket_views,
        "explanation": explanation,
    }


def disabled_route_example() -> RouteSnapshot:
    r = sample_route()
    r.route_id = "rt_disabled"
    r.availability_status = AvailabilityStatus.DISABLED
    r.status = "disabled"
    return r
