"""Broker admission must not inherit mock authority or caller route metadata."""

from __future__ import annotations

import pytest
from tests.broker.test_broker import _request

from swarm.broker.broker import SharedInferenceBroker
from swarm.broker.errors import BrokerBypassError
from swarm.broker.policy import AdmissionPolicy, RoutePolicyContext
from swarm.contracts.enums import BillingMode, PurposeEligibility
from swarm.contracts.fixtures import sample_quota, sample_route
from swarm.contracts.provider import QuotaBucket
from swarm.fakes.provider import FakeProviderAdapter


@pytest.mark.asyncio
async def test_missing_registered_context_denies_assess_and_reserve() -> None:
    route = sample_route()
    broker = SharedInferenceBroker(
        FakeProviderAdapter(routes=[route]),
        [sample_quota()],
        policy=AdmissionPolicy(allow_unknown_billing=True),
    )
    request = _request(route_id=route.route_id, purpose="probe")
    assert await broker.assess(request) == []
    explanation = await broker.explain(broker.last_decision_id or "")
    assert any(
        row["reason"] == "route_context_unregistered" for row in explanation["blocked_routes"]
    )
    with pytest.raises(BrokerBypassError, match="route_context_unregistered"):
        await broker.reserve(request, route)
    assert broker.adapter.calls == []


@pytest.mark.asyncio
async def test_caller_cannot_swap_quota_bucket_after_registration() -> None:
    route = sample_route()
    extra = QuotaBucket(
        bucket_id="qb_other",
        scope_type="account",
        scope_id=route.account_id,
        dimension=sample_quota().dimension,
        limit=100,
        remaining=100,
    )
    broker = SharedInferenceBroker(
        FakeProviderAdapter(routes=[route]),
        [sample_quota(), extra],
        route_contexts={
            route.route_id: RoutePolicyContext(
                route=route,
                qualified=True,
                billing_mode=BillingMode.NONE,
                purpose_eligibility=PurposeEligibility.PROTOTYPE,
            )
        },
    )
    forged = route.model_copy(deep=True)
    forged.quota_bucket_ids = ["qb_other"]
    request = _request(route_id=route.route_id)
    with pytest.raises(BrokerBypassError, match="route_snapshot_changed"):
        await broker.reserve(request, forged)
    bucket = broker.ledger.get("qb_other")
    assert bucket is not None and bucket.remaining == 100


@pytest.mark.asyncio
async def test_request_route_must_match_reserved_route() -> None:
    route = sample_route()
    broker = SharedInferenceBroker(
        FakeProviderAdapter(routes=[route]),
        [sample_quota()],
        route_contexts={
            route.route_id: RoutePolicyContext(
                route=route,
                qualified=True,
                purpose_eligibility=PurposeEligibility.PROTOTYPE,
            )
        },
        policy=AdmissionPolicy(allow_unknown_billing=True),
    )
    request = _request(route_id="rt_other")
    with pytest.raises(BrokerBypassError, match="request_route_mismatch"):
        await broker.reserve(request, route)
