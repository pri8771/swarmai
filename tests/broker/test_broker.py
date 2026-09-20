"""Broker unit tests — contention, policy, settlement, retries."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from swarm.broker.broker import SharedInferenceBroker
from swarm.broker.circuit import CircuitBreaker, CircuitConfig
from swarm.broker.errors import (
    AmbiguousSendError,
    BrokerBypassError,
    CircuitOpenError,
    DuplicateSettlementError,
    PolicyDeniedError,
    QuotaExhaustedError,
    UnknownChargeDeniedError,
)
from swarm.broker.explain import build_mock_broker, explain_capacity
from swarm.broker.ledger import LedgerConfig, QuotaLedger
from swarm.broker.policy import AdmissionPolicy, RoutePolicyContext
from swarm.broker.retry import RetryOwner
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import (
    AvailabilityStatus,
    BillingMode,
    ErrorClass,
    PurposeEligibility,
    QuotaDimension,
    ReservationPhase,
    SettlementState,
    WindowType,
)
from swarm.contracts.fixtures import sample_quota, sample_route, sample_route_beta
from swarm.contracts.provider import (
    AttemptReceipt,
    InferenceRequest,
    NormalizedUsage,
    QuotaBucket,
    Reservation,
    RouteSnapshot,
)
from swarm.fakes.provider import FakeProviderAdapter


def _ctx(
    route: RouteSnapshot,
    *,
    qualified: bool = True,
    billing: BillingMode = BillingMode.NONE,
    purpose: PurposeEligibility = PurposeEligibility.PROTOTYPE,
    free: bool = True,
    deprecated: bool = False,
) -> RoutePolicyContext:
    return RoutePolicyContext(
        route=route,
        qualified=qualified,
        qualification_rationale="test_qualified" if qualified else "unassessed",
        billing_mode=billing,
        purpose_eligibility=purpose,
        charge_verified_free=free,
        deprecated=deprecated,
        shared_upstream_group="upstream_shared",
    )


def _request(
    *,
    purpose: str = "mission",
    route_id: str | None = "rt_fake_alpha",
    attempt_id: str | None = None,
    input_tokens: int = 40,
    max_out: int = 100,
) -> InferenceRequest:
    return InferenceRequest(
        project_id="proj_demo",
        attempt_id=attempt_id or new_id("att_"),
        route_id=route_id,
        purpose=purpose,
        messages=[{"role": "user", "content": "hello"}],
        estimated_input_tokens=input_tokens,
        max_output_tokens=max_out,
        secret_ref_names=["FAKE_API_KEY"],
    )


def _broker(
    buckets: list[QuotaBucket] | None = None,
    routes: list[RouteSnapshot] | None = None,
    **kwargs: Any,
) -> SharedInferenceBroker:
    routes = routes or [sample_route(), sample_route_beta()]
    adapter = FakeProviderAdapter(routes=routes)
    buckets = buckets or [sample_quota()]
    contexts = {r.route_id: _ctx(r) for r in routes}
    return SharedInferenceBroker(
        adapter,
        buckets,
        route_contexts=contexts,
        policy=AdmissionPolicy(allow_paid=False, allow_unknown_billing=False),
        **kwargs,
    )


@pytest.mark.asyncio
async def test_happy_path_assess_reserve_invoke_reconcile() -> None:
    broker = _broker()
    req = _request()
    eligible = await broker.assess(req)
    assert len(eligible) == 1
    ticket = await broker.reserve(req, eligible[0])
    receipt = await broker.invoke(ticket)
    assert receipt.settlement_state == SettlementState.SETTLED
    broker.assert_all_calls_accounted()
    explanation = await broker.explain(broker.last_decision_id or "")
    assert explanation["selected_route"] == "rt_fake_alpha"
    assert explanation["reserved"]
    assert "quota_units_note" in explanation


@pytest.mark.asyncio
async def test_concurrent_admission_no_oversubscribe() -> None:
    bucket = QuotaBucket(
        bucket_id="qb_tiny",
        scope_type="account",
        scope_id="a",
        dimension=QuotaDimension.REQUESTS,
        limit=5,
        remaining=5,
        window_type=WindowType.LIFETIME,
        source="test",
        confidence="exact",
    )
    route = sample_route()
    route.quota_bucket_ids = ["qb_tiny"]
    broker = _broker(buckets=[bucket], routes=[route])

    async def one_call(i: int) -> str:
        req = _request(route_id=route.route_id, attempt_id=f"att_c_{i}")
        await broker.assess(req)
        try:
            ticket = await broker.reserve(req, route)
            await broker.invoke(ticket)
            return "ok"
        except QuotaExhaustedError:
            return "denied"

    results = await asyncio.gather(*[one_call(i) for i in range(20)])
    assert results.count("ok") == 5
    assert results.count("denied") == 15
    remaining = broker.ledger.get("qb_tiny")
    assert remaining is not None
    assert remaining.remaining == 0


@pytest.mark.asyncio
async def test_byok_and_direct_share_bucket_no_double_count() -> None:
    """Direct and BYOK routes share the same upstream bucket_id — reserved once."""
    shared = sample_quota()
    shared.remaining = 3
    direct = sample_route()
    byok = sample_route_beta()
    byok.route_id = "rt_byok"
    byok.billing_origin = "byok_custom_key"
    byok.quota_bucket_ids = list(direct.quota_bucket_ids)  # same upstream group
    broker = _broker(buckets=[shared], routes=[direct, byok])

    for i, rid in enumerate([direct.route_id, byok.route_id, direct.route_id]):
        req = _request(route_id=rid, attempt_id=f"att_share_{i}")
        routes = await broker.assess(req)
        ticket = await broker.reserve(req, routes[0])
        await broker.invoke(ticket)

    snap = broker.ledger.get(shared.bucket_id)
    assert snap is not None
    assert snap.remaining == 0

    req = _request(route_id=byok.route_id, attempt_id="att_share_fail")
    await broker.assess(req)
    with pytest.raises(QuotaExhaustedError):
        await broker.reserve(req, byok)


@pytest.mark.asyncio
async def test_zero_remaining_versus_unknown() -> None:
    zero = QuotaBucket(
        bucket_id="qb_zero",
        scope_type="account",
        scope_id="a",
        dimension=QuotaDimension.REQUESTS,
        limit=10,
        remaining=0,
        window_type=WindowType.FIXED,
        source="test",
        confidence="exact",
    )
    unknown = QuotaBucket(
        bucket_id="qb_unk",
        scope_type="account",
        scope_id="a",
        dimension=QuotaDimension.CREDIT,
        limit=None,
        remaining=None,
        window_type=WindowType.UNKNOWN,
        source="unobserved",
        confidence="unknown",
    )
    ledger = QuotaLedger(
        [zero, unknown],
        config=LedgerConfig(allow_unknown_probe=True, verified_no_charge_routes={"rt_free"}),
    )
    from swarm.contracts.provider import BucketAmount

    with pytest.raises(QuotaExhaustedError, match="zero_remaining"):
        await ledger.reserve(
            [BucketAmount(bucket_id="qb_zero", dimension=QuotaDimension.REQUESTS, amount=1)],
            route_id="rt_x",
            purpose="mission",
        )
    with pytest.raises(UnknownChargeDeniedError):
        await ledger.reserve(
            [BucketAmount(bucket_id="qb_unk", dimension=QuotaDimension.CREDIT, amount=1)],
            route_id="rt_paid_unknown",
            purpose="mission",
        )
    # Bounded probe on verified no-charge permitted.
    reserved = await ledger.reserve(
        [BucketAmount(bucket_id="qb_unk", dimension=QuotaDimension.CREDIT, amount=1)],
        route_id="rt_free",
        purpose="probe",
        probe=True,
    )
    assert reserved


@pytest.mark.asyncio
async def test_fixed_window_reset_and_dst_safe_clock() -> None:
    start = datetime(2026, 3, 8, 6, 0, tzinfo=UTC)  # near US DST spring forward
    clock = {"now": start}

    def now() -> datetime:
        return clock["now"]

    bucket = QuotaBucket(
        bucket_id="qb_day",
        scope_type="account",
        scope_id="a",
        dimension=QuotaDimension.REQUESTS,
        limit=2,
        remaining=0,
        window_type=WindowType.FIXED,
        reset_at=start + timedelta(hours=1),
        observed_at=start - timedelta(hours=23),
        source="test",
        confidence="exact",
    )
    ledger = QuotaLedger([bucket], clock=now)
    from swarm.contracts.provider import BucketAmount

    amt = [BucketAmount(bucket_id="qb_day", dimension=QuotaDimension.REQUESTS, amount=1)]
    with pytest.raises(QuotaExhaustedError):
        await ledger.reserve(amt, route_id="rt", purpose="mission")
    clock["now"] = start + timedelta(hours=2)
    reserved = await ledger.reserve(amt, route_id="rt", purpose="mission")
    assert reserved[0].amount == 1
    snap = ledger.get("qb_day")
    assert snap is not None
    assert snap.remaining == 2  # reset to limit then reserved still held separately
    # remaining field is limit after reset; reserved tracked on live bucket
    live_remaining = snap.remaining
    assert live_remaining == 2


@pytest.mark.asyncio
async def test_request_and_token_constraints() -> None:
    req_b = QuotaBucket(
        bucket_id="qb_req",
        scope_type="account",
        scope_id="a",
        dimension=QuotaDimension.REQUESTS,
        limit=100,
        remaining=100,
        window_type=WindowType.LIFETIME,
        source="t",
        confidence="exact",
    )
    tok_b = QuotaBucket(
        bucket_id="qb_tok",
        scope_type="account",
        scope_id="a",
        dimension=QuotaDimension.TOTAL_TOKENS,
        limit=50,
        remaining=50,
        window_type=WindowType.ROLLING,
        source="t",
        confidence="exact",
    )
    route = sample_route()
    route.quota_bucket_ids = ["qb_req", "qb_tok"]
    broker = _broker(buckets=[req_b, tok_b], routes=[route])
    req = _request(input_tokens=40, max_out=20)  # needs 60 tokens
    await broker.assess(req)
    with pytest.raises(QuotaExhaustedError, match="insufficient"):
        await broker.reserve(req, route)


@pytest.mark.asyncio
async def test_spending_denied_before_network() -> None:
    route = sample_route()
    broker = _broker(routes=[route])
    broker.register_route(
        _ctx(route, billing=BillingMode.PAID, free=False, purpose=PurposeEligibility.PRODUCTION)
    )
    req = _request(purpose="production")
    eligible = await broker.assess(req)
    assert eligible == []
    explanation = await broker.explain(broker.last_decision_id or "")
    assert any(b["reason"] == "spending_denied_before_network" for b in explanation["blocked_routes"])
    # Direct reserve also denies before adapter call.
    with pytest.raises(UnknownChargeDeniedError):
        await broker.reserve(req, route)
    assert broker.adapter.calls == []


@pytest.mark.asyncio
async def test_deprecated_model_blocked() -> None:
    route = sample_route()
    broker = _broker(routes=[route])
    broker.register_route(_ctx(route, deprecated=True))
    req = _request()
    eligible = await broker.assess(req)
    assert eligible == []


@pytest.mark.asyncio
async def test_hidden_retry_detection_via_accounting() -> None:
    broker = _broker()
    req = _request()
    eligible = await broker.assess(req)
    ticket = await broker.reserve(req, eligible[0])
    await broker.invoke(ticket)
    # Simulate hidden retry that bypassed broker:
    broker.adapter.calls.append("sneaky")
    with pytest.raises(BrokerBypassError, match="bypass"):
        broker.assert_all_calls_accounted()


@pytest.mark.asyncio
async def test_ambiguous_send_retained() -> None:
    class FlakyAdapter(FakeProviderAdapter):
        async def execute_one(
            self, request: InferenceRequest, admitted_ticket: Reservation
        ) -> AttemptReceipt:
            self.calls.append(admitted_ticket.route_id)
            return AttemptReceipt(
                logical_call_id=admitted_ticket.logical_call_id,
                send_phase=ReservationPhase.SENT,
                actual_route=admitted_ticket.route_id,
                error_class=ErrorClass.UNKNOWN_OUTCOME,
                settlement_state=SettlementState.UNKNOWN,
            )

    route = sample_route()
    adapter = FlakyAdapter(routes=[route])
    broker = SharedInferenceBroker(
        adapter,
        [sample_quota()],
        route_contexts={route.route_id: _ctx(route)},
    )
    req = _request()
    await broker.assess(req)
    ticket = await broker.reserve(req, route)
    with pytest.raises(AmbiguousSendError):
        await broker.invoke(ticket)
    # Ticket retained as unknown; second invoke returns retained receipt.
    receipt = await broker.invoke(ticket)
    assert receipt.settlement_state == SettlementState.UNKNOWN
    assert len(adapter.calls) == 1


@pytest.mark.asyncio
async def test_duplicate_settlement_rejected() -> None:
    broker = _broker()
    req = _request()
    eligible = await broker.assess(req)
    ticket = await broker.reserve(req, eligible[0])
    receipt = await broker.invoke(ticket)
    with pytest.raises(DuplicateSettlementError):
        await broker.reconcile(receipt)


@pytest.mark.asyncio
async def test_partial_stream_marked_unknown() -> None:
    class PartialAdapter(FakeProviderAdapter):
        async def execute_one(
            self, request: InferenceRequest, admitted_ticket: Reservation
        ) -> AttemptReceipt:
            self.calls.append(admitted_ticket.route_id)
            return AttemptReceipt(
                logical_call_id=admitted_ticket.logical_call_id,
                send_phase=ReservationPhase.SENT,
                actual_route=admitted_ticket.route_id,
                error_class=ErrorClass.PARTIAL_STREAM,
                normalized_usage=NormalizedUsage(input_tokens=10, output_tokens=None, total_tokens=None),
                settlement_state=SettlementState.PENDING,
            )

    route = sample_route()
    broker = SharedInferenceBroker(
        PartialAdapter(routes=[route]),
        [sample_quota()],
        route_contexts={route.route_id: _ctx(route)},
    )
    req = _request()
    await broker.assess(req)
    ticket = await broker.reserve(req, route)
    receipt = await broker.invoke(ticket)
    assert receipt.error_class == ErrorClass.PARTIAL_STREAM
    assert receipt.settlement_state == SettlementState.UNKNOWN


@pytest.mark.asyncio
async def test_control_reserve_protected() -> None:
    control = QuotaBucket(
        bucket_id="qb_control_reserve",
        scope_type="mission",
        scope_id="m",
        dimension=QuotaDimension.REQUESTS,
        limit=5,
        remaining=5,
        window_type=WindowType.LIFETIME,
        source="t",
        confidence="exact",
    )
    route = sample_route()
    route.quota_bucket_ids = ["qb_control_reserve"]
    broker = _broker(
        buckets=[control],
        routes=[route],
        ledger_config=LedgerConfig(planning_review_reserve=2),
    )
    # Mission may consume down to floor=2 → 3 ok then deny.
    for i in range(3):
        req = _request(purpose="mission", attempt_id=f"att_m_{i}", route_id=route.route_id)
        await broker.assess(req)
        ticket = await broker.reserve(req, route)
        await broker.invoke(ticket)
    req = _request(purpose="mission", attempt_id="att_m_fail", route_id=route.route_id)
    await broker.assess(req)
    with pytest.raises(QuotaExhaustedError, match="control_reserve"):
        await broker.reserve(req, route)
    # Planning may use the reserve.
    req = _request(purpose="planning", attempt_id="att_plan", route_id=route.route_id)
    await broker.assess(req)
    ticket = await broker.reserve(req, route)
    await broker.invoke(ticket)


@pytest.mark.asyncio
async def test_circuit_opens_on_overload_not_confused_with_auth() -> None:
    breaker = CircuitBreaker(CircuitConfig(failure_threshold=2, open_for=timedelta(seconds=60)))
    breaker.record_error("rt_x", ErrorClass.RATE_LIMIT)
    breaker.record_error("rt_x", ErrorClass.RATE_LIMIT)
    with pytest.raises(CircuitOpenError):
        breaker.assert_closed("rt_x")
    auth = CircuitBreaker(CircuitConfig(failure_threshold=5))
    auth.record_error("rt_y", ErrorClass.AUTHENTICATION)
    assert auth.health("rt_y").auth_failures == 1
    assert auth.health("rt_y").overloads == 0
    with pytest.raises(CircuitOpenError):
        auth.assert_closed("rt_y")


def test_retry_owner_honors_retry_after_and_retains_unknown() -> None:
    owner = RetryOwner()
    owner.note_attempt("lc_1")
    d = owner.decide("lc_1", ErrorClass.RATE_LIMIT, retry_after=1.5)
    assert d.should_retry
    assert d.wait_seconds == 1.5
    assert d.allow_route_change
    owner.note_attempt("lc_2")
    d2 = owner.decide("lc_2", ErrorClass.UNKNOWN_OUTCOME, post_send=True)
    assert not d2.should_retry
    assert d2.reason == "retain_ambiguous_send"
    owner.note_attempt("lc_3")
    d3 = owner.decide("lc_3", ErrorClass.AUTHENTICATION)
    assert not d3.should_retry


@pytest.mark.asyncio
async def test_invoke_without_ticket_is_bypass() -> None:
    broker = _broker()
    fake = Reservation(
        logical_call_id="lc_x",
        attempt_id="att_x",
        route_id="rt_fake_alpha",
        expires_at=utc_now() + timedelta(minutes=1),
    )
    with pytest.raises(BrokerBypassError):
        await broker.invoke(fake)


@pytest.mark.asyncio
async def test_capacity_explain_mock_cli_helper() -> None:
    result = await explain_capacity(mode="mock")
    assert result["mode"] == "mock"
    assert result["mock_vs_live"] == "mock_fixtures_only"
    assert result["eligible_route_count"] >= 1
    assert result["buckets"]
    live = await explain_capacity(mode="live")
    assert live["mock_vs_live"] == "observed_or_empty_not_mock_broker"
    assert live["eligible_route_count"] == 0
    assert live["buckets"] == []


@pytest.mark.asyncio
async def test_build_mock_broker_smoke() -> None:
    broker = build_mock_broker()
    req = _request(route_id=None)
    eligible = await broker.assess(req)
    assert len(eligible) >= 1
    ticket = await broker.reserve(req, eligible[0])
    await broker.invoke(ticket)
    broker.assert_all_calls_accounted()


@pytest.mark.asyncio
async def test_not_qualified_blocks_mission() -> None:
    route = sample_route()
    broker = _broker(routes=[route])
    broker.register_route(_ctx(route, qualified=False))
    req = _request(purpose="mission")
    assert await broker.assess(req) == []
    with pytest.raises(PolicyDeniedError):
        await broker.reserve(req, route)


@pytest.mark.asyncio
async def test_unavailable_route_blocked() -> None:
    route = sample_route()
    route.availability_status = AvailabilityStatus.UNAVAILABLE
    broker = _broker(routes=[route])
    req = _request()
    assert await broker.assess(req) == []
