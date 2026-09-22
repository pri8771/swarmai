"""Remote call reservations are durable, single winner, and fail closed.

The integration fixture creates its own PostgreSQL schema and never clears
tables in a product or shared test schema.
"""

from __future__ import annotations

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import create_engine, text

from swarm.broker.broker import SharedInferenceBroker
from swarm.broker.durable_remote import (
    DurableRemoteCallGate,
    RemoteAdmissionDenied,
    remote_request_hash,
)
from swarm.broker.errors import AmbiguousSendError, BrokerBypassError
from swarm.broker.policy import RoutePolicyContext
from swarm.contracts.common import utc_now
from swarm.contracts.enums import (
    AvailabilityStatus,
    BillingMode,
    ErrorClass,
    PurposeEligibility,
    ReservationPhase,
    SettlementState,
)
from swarm.contracts.provider import (
    AttemptReceipt,
    BucketAmount,
    InferenceRequest,
    NormalizedUsage,
    RouteSnapshot,
)
from swarm.db.engine import make_session_factory
from swarm.db.models import (
    ApprovalRow,
    AttemptReceiptRow,
    Base,
    ProviderAccountRow,
    QuotaBucketRow,
    ReservationRow,
    RouteSnapshotRow,
)
from swarm.providers.core.adapters import OpenRouterAdapter, OpenRouterFreeRoute

pytestmark = pytest.mark.integration
SOURCE_TREE = "a" * 40
EVIDENCE = "account-zero-price-ref"
QUOTA_EVIDENCE = "account-quota-ref"


@pytest.fixture()
def factory():
    url = os.environ.get("SWARM_DATABASE_URL")
    if not url:
        pytest.skip("SWARM_DATABASE_URL required")
    schema = f"swarm_remote_test_{uuid4().hex}"
    admin = create_engine(url, pool_pre_ping=True)
    try:
        with admin.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA {schema}"))
    except Exception as exc:  # noqa: BLE001
        admin.dispose()
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={schema}"},
    )
    try:
        Base.metadata.create_all(engine)
        yield make_session_factory(engine)
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        admin.dispose()


def _seed(factory, *, remaining: int = 1, observed_age: timedelta = timedelta()) -> tuple:
    now = utc_now()
    route = RouteSnapshot(
        route_id="route-free",
        provider="openrouter",
        account_id="account-free",
        model_id="liquid/lfm-2.5-2.6b:free",
        endpoint="https://openrouter.ai/api/v1/chat/completions",
        hosted_by="liquid",
        billing_origin="openrouter",
        availability_status=AvailabilityStatus.AVAILABLE,
        quota_bucket_ids=["request-quota"],
    )
    request = InferenceRequest(
        project_id="project-one",
        attempt_id="attempt-one",
        route_id=route.route_id,
        purpose="probe",
        messages=[{"role": "user", "content": "one short answer"}],
        estimated_input_tokens=12,
        max_output_tokens=16,
    )
    grant = ApprovalRow(
        id="grant-one",
        payload_hash=remote_request_hash(request, route),
        permitted_operation="infer",
        destination=route.route_id,
        grantor="operator",
        expires_at=now + timedelta(minutes=5),
        project_id=request.project_id,
        actor="operator",
        integration_id="swarm.remote_inference",
        integration_version="1",
        operation="infer",
        max_effect_count=1,
        used_count=0,
        constraints={
            "source_tree": SOURCE_TREE,
            "account_id": route.account_id,
            "model_id": route.model_id,
            "backend_slug": route.hosted_by,
            "max_output_tokens": request.max_output_tokens,
            "zero_charge_evidence_ref": EVIDENCE,
            "quota_evidence_ref": QUOTA_EVIDENCE,
        },
    )
    with factory.begin() as session:
        session.add_all(
            [
                ProviderAccountRow(
                    id=route.account_id,
                    service_id=route.provider,
                    account_alias="free-account",
                    owner="operator",
                    account_status="authenticated",
                    purpose_eligibility="prototype",
                    billing_mode="free",
                    verified_at=now - observed_age,
                    payload={
                        "tier": "free",
                        "zero_charge_evidence_ref": EVIDENCE,
                        "byok_disabled_verified": True,
                    },
                ),
                RouteSnapshotRow(
                    route_id=route.route_id,
                    provider=route.provider,
                    account_id=route.account_id,
                    model_id=route.model_id,
                    endpoint=route.endpoint,
                    billing_origin=route.billing_origin,
                    availability_status="available",
                    status="observed",
                    observed_at=now - observed_age,
                    payload={
                        "backend_slug": route.hosted_by,
                        "zero_price_verified": True,
                        "zero_charge_evidence_ref": EVIDENCE,
                    },
                ),
                QuotaBucketRow(
                    bucket_id="request-quota",
                    scope_type="account",
                    scope_id=route.account_id,
                    dimension="requests",
                    limit=remaining,
                    remaining=remaining,
                    window_type="fixed",
                    version=1,
                    observed_at=now - observed_age,
                    payload={"confidence": "exact", "quota_evidence_ref": QUOTA_EVIDENCE},
                ),
                grant,
            ]
        )
    return request, route, grant


def test_durable_unknown_call_never_resends_after_restart(factory):
    request, route, grant = _seed(factory)
    gate = DurableRemoteCallGate(factory, source_tree=SOURCE_TREE)
    ticket = gate.reserve(request, route, grant_id=grant.id)
    gate.mark_sending(ticket)
    restarted = DurableRemoteCallGate(factory, source_tree=SOURCE_TREE)
    with pytest.raises(RemoteAdmissionDenied, match="remote_call_not_resendable"):
        restarted.mark_sending(ticket)
    with pytest.raises(RemoteAdmissionDenied, match="cannot_release_sent_or_unknown_call"):
        restarted.release_unsent(ticket)
    receipt = AttemptReceipt(
        logical_call_id=ticket.logical_call_id,
        actual_route=ticket.route_id,
        send_phase=ReservationPhase.UNKNOWN,
        settlement_state=SettlementState.UNKNOWN,
    )
    restarted.record_result(ticket, receipt)
    assert restarted.read_state(ticket.reservation_id)["state"] == "unknown"
    with factory() as session:
        assert session.get(QuotaBucketRow, "request-quota").remaining == 0
        assert session.get(ApprovalRow, grant.id).used_count == 1


def test_unsent_release_refunds_quota_but_not_operator_grant(factory):
    request, route, grant = _seed(factory)
    gate = DurableRemoteCallGate(factory, source_tree=SOURCE_TREE)
    ticket = gate.reserve(request, route, grant_id=grant.id)
    forged = ticket.model_copy(
        update={"bucket_amounts": [BucketAmount(bucket_id="request-quota", dimension="requests", amount=99)]}
    )
    gate.release_unsent(forged)
    with factory() as session:
        assert session.get(QuotaBucketRow, "request-quota").remaining == 1
        assert session.get(ApprovalRow, grant.id).used_count == 1
    with pytest.raises(RemoteAdmissionDenied, match="stored_owner_grant_mismatch_or_expired"):
        gate.reserve(request, route, grant_id=grant.id)


def test_fresh_exact_evidence_and_request_binding_required(factory):
    request, route, grant = _seed(factory, observed_age=timedelta(minutes=11))
    gate = DurableRemoteCallGate(factory, source_tree=SOURCE_TREE)
    with pytest.raises(RemoteAdmissionDenied, match="account_or_route_evidence_unverified"):
        gate.reserve(request, route, grant_id=grant.id)
    with factory.begin() as session:
        now = utc_now()
        session.get(ProviderAccountRow, route.account_id).verified_at = now
        session.get(RouteSnapshotRow, route.route_id).observed_at = now
        session.get(QuotaBucketRow, "request-quota").observed_at = now
    changed = request.model_copy(update={"tools_requested": ["browser"]})
    with pytest.raises(RemoteAdmissionDenied, match="stored_owner_grant_mismatch_or_expired"):
        gate.reserve(changed, route, grant_id=grant.id)
    with factory.begin() as session:
        session.get(QuotaBucketRow, "request-quota").payload = {
            "confidence": "exact", "quota_evidence_ref": "different"
        }
    with pytest.raises(RemoteAdmissionDenied, match="request_allowance_unverified_or_exhausted"):
        gate.reserve(request, route, grant_id=grant.id)
    with factory() as session:
        assert session.get(ApprovalRow, grant.id).used_count == 0
        assert session.get(ReservationRow, "missing") is None


def test_settlement_needs_zero_cost_and_selected_free_backend(factory):
    request, route, grant = _seed(factory)
    gate = DurableRemoteCallGate(factory, source_tree=SOURCE_TREE)
    ticket = gate.reserve(request, route, grant_id=grant.id)
    gate.mark_sending(ticket)
    receipt = AttemptReceipt(
        logical_call_id=ticket.logical_call_id,
        actual_route=ticket.route_id,
        send_phase=ReservationPhase.SETTLED,
        settlement_state=SettlementState.SETTLED,
        normalized_usage=NormalizedUsage(
            extras={
                "provider_cost_status": "reported",
                "provider_cost_usd": "0.0000",
                "provider_cost_source": "response.usage.cost",
                "openrouter_routing": {
                    "selected_provider": "Liquid",
                    "selected_model": route.model_id,
                    "attempt": 1,
                    "is_byok": False,
                    "usage_is_byok": False,
                },
            }
        ),
    )
    gate.record_result(ticket, receipt)
    assert gate.read_state(ticket.reservation_id)["state"] == "committed"


def test_missing_cost_report_retains_unknown_even_on_success(factory):
    request, route, grant = _seed(factory)
    gate = DurableRemoteCallGate(factory, source_tree=SOURCE_TREE)
    ticket = gate.reserve(request, route, grant_id=grant.id)
    gate.mark_sending(ticket)
    receipt = AttemptReceipt(
        logical_call_id=ticket.logical_call_id,
        actual_route=ticket.route_id,
        send_phase=ReservationPhase.SETTLED,
        settlement_state=SettlementState.SETTLED,
        normalized_usage=NormalizedUsage(extras={"provider_cost_status": "unknown"}),
    )
    gate.record_result(ticket, receipt)
    assert gate.read_state(ticket.reservation_id)["state"] == "unknown"
    with factory() as session:
        stored = session.get(AttemptReceiptRow, receipt.network_attempt_id)
        assert stored.settlement_state == "unknown"
        assert stored.payload["settlement_state"] == "settled"


def test_parallel_reservations_have_one_postgres_winner(factory):
    request, route, grant = _seed(factory)
    request_two = request.model_copy(update={"attempt_id": "attempt-two"})
    with factory.begin() as session:
        session.add(
            ApprovalRow(
                id="grant-two",
                payload_hash=remote_request_hash(request_two, route),
                permitted_operation="infer",
                destination=route.route_id,
                grantor="operator",
                expires_at=utc_now() + timedelta(minutes=5),
                project_id=request.project_id,
                actor="operator",
                integration_id="swarm.remote_inference",
                integration_version="1",
                operation="infer",
                max_effect_count=1,
                used_count=0,
                constraints=grant.constraints,
            )
        )
    barrier = threading.Barrier(2)

    def reserve_one(args):
        req, grant_id = args
        gate = DurableRemoteCallGate(factory, source_tree=SOURCE_TREE)
        barrier.wait()
        try:
            return gate.reserve(req, route, grant_id=grant_id)
        except RemoteAdmissionDenied as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(reserve_one, [(request, grant.id), (request_two, "grant-two")]))
    assert sum(not isinstance(result, Exception) for result in outcomes) == 1
    assert sum(isinstance(result, RemoteAdmissionDenied) for result in outcomes) == 1
    with factory() as session:
        assert session.get(QuotaBucketRow, "request-quota").remaining == 0
        assert sum(session.get(ApprovalRow, gid).used_count for gid in (grant.id, "grant-two")) == 1


class _ReceiptAdapter:
    provider_id = "openrouter"

    def __init__(self, route: RouteSnapshot, *, cost_known: bool = True) -> None:
        self.route = route
        self.free_route = OpenRouterFreeRoute(
            model_id=route.model_id, provider_slug=route.hosted_by
        )
        self.cost_known = cost_known
        self.calls = []

    async def discover(self):
        return [self.route]

    async def execute_one(self, request, ticket):
        self.calls.append((request, ticket))
        extras = {"provider_cost_status": "unknown"}
        if self.cost_known:
            extras = {
                "provider_cost_status": "reported",
                "provider_cost_usd": "0",
                "provider_cost_source": "response.usage.cost",
                "openrouter_routing": {
                    "selected_provider": "Liquid",
                    "selected_model": self.route.model_id,
                    "attempt": 1,
                    "is_byok": False,
                    "usage_is_byok": False,
                },
            }
        return AttemptReceipt(
            logical_call_id=ticket.logical_call_id,
            actual_route=ticket.route_id,
            send_phase=ReservationPhase.SETTLED,
            settlement_state=SettlementState.SETTLED,
            normalized_usage=NormalizedUsage(extras=extras),
        )

    async def classify_error(self, exc):
        return ErrorClass.UNKNOWN_OUTCOME


def _broker(factory, route: RouteSnapshot, *, cost_known: bool = True):
    adapter = _ReceiptAdapter(route, cost_known=cost_known)
    broker = SharedInferenceBroker(
        adapter,
        route_contexts={
            route.route_id: RoutePolicyContext(
                route=route,
                billing_mode=BillingMode.FREE,
                purpose_eligibility=PurposeEligibility.PROTOTYPE,
                charge_verified_free=True,
            )
        },
        remote_gate=DurableRemoteCallGate(factory, source_tree=SOURCE_TREE),
    )
    return broker, adapter


@pytest.mark.asyncio
async def test_broker_needs_exact_grant_before_any_remote_adapter_call(factory):
    request, route, grant = _seed(factory)
    broker, adapter = _broker(factory, route)
    assert [r.route_id for r in await broker.assess(request)] == [route.route_id]
    with pytest.raises(RemoteAdmissionDenied, match="exact_grant_missing"):
        await broker.reserve(request, route)
    assert adapter.calls == []
    ticket = await broker.reserve(request, route, grant_id=grant.id)
    receipt = await broker.invoke(ticket)
    assert receipt.settlement_state == SettlementState.SETTLED
    assert broker.remote_gate.read_state(ticket.reservation_id)["state"] == "committed"
    assert adapter.calls and broker.request_count == 1
    with pytest.raises(RemoteAdmissionDenied, match="already_sent"):
        await broker.invoke(ticket)
    with pytest.raises(BrokerBypassError, match="remote_settlement_requires_durable_gate"):
        await broker.reconcile(receipt)


@pytest.mark.asyncio
async def test_broker_unknown_charge_stays_unknown_and_cannot_retry(factory):
    request, route, grant = _seed(factory)
    broker, adapter = _broker(factory, route, cost_known=False)
    ticket = await broker.reserve(request, route, grant_id=grant.id)
    with pytest.raises(AmbiguousSendError):
        await broker.invoke(ticket)
    assert broker.remote_gate.read_state(ticket.reservation_id)["state"] == "unknown"
    assert len(adapter.calls) == 1
    with pytest.raises(RemoteAdmissionDenied, match="already_sent"):
        await broker.invoke(ticket)
    assert len(adapter.calls) == 1


@pytest.mark.asyncio
async def test_adapter_pin_cannot_change_between_reserve_and_send(factory):
    request, route, grant = _seed(factory)
    broker, adapter = _broker(factory, route)
    original_pin = adapter.free_route
    adapter.free_route = OpenRouterFreeRoute(
        model_id=route.model_id, provider_slug="modelrun"
    )
    with pytest.raises(RemoteAdmissionDenied, match="adapter_pin_mismatch"):
        await broker.reserve(request, route, grant_id=grant.id)
    adapter.free_route = original_pin
    ticket = await broker.reserve(request, route, grant_id=grant.id)
    adapter.free_route = OpenRouterFreeRoute(
        model_id=route.model_id, provider_slug="modelrun"
    )
    with pytest.raises(RemoteAdmissionDenied, match="adapter_pin_mismatch"):
        await broker.invoke(ticket)
    assert adapter.calls == []
    adapter.free_route = original_pin
    await broker.expire_unsent(ticket.reservation_id)
    assert broker.remote_gate.read_state(ticket.reservation_id)["state"] == "released"
    with pytest.raises(RemoteAdmissionDenied, match="remote_call_not_resendable"):
        await broker.invoke(ticket)
    assert adapter.calls == []


@pytest.mark.asyncio
async def test_actual_openrouter_adapter_is_fenced_through_mock_http(
    factory, monkeypatch: pytest.MonkeyPatch
):
    request, route, grant = _seed(factory)
    sent = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(http_request.content))
        return httpx.Response(
            200,
            json={
                "id": "offline-generation",
                "model": route.model_id,
                "openrouter_metadata": {
                    "attempt": 1,
                    "is_byok": False,
                    "endpoints": {
                        "available": [
                            {
                                "provider": "Liquid",
                                "model": route.model_id,
                                "selected": True,
                            }
                        ]
                    },
                },
                "usage": {"cost": 0, "is_byok": False},
            },
        )

    original = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    adapter = OpenRouterAdapter(
        mode="live",
        enabled=True,
        secret_ref_names=[],
        account_id=route.account_id,
        free_route=OpenRouterFreeRoute(model_id=route.model_id, provider_slug="liquid"),
    )
    adapter._routes = {route.route_id: route}
    broker = SharedInferenceBroker(
        adapter,
        route_contexts={
            route.route_id: RoutePolicyContext(
                route=route,
                billing_mode=BillingMode.FREE,
                purpose_eligibility=PurposeEligibility.PROTOTYPE,
                charge_verified_free=True,
            )
        },
        remote_gate=DurableRemoteCallGate(factory, source_tree=SOURCE_TREE),
    )
    ticket = await broker.reserve(request, route, grant_id=grant.id)
    await broker.invoke(ticket)
    assert broker.remote_gate.read_state(ticket.reservation_id)["state"] == "committed"
    assert len(sent) == 1
    assert sent[0]["provider"] == {
        "only": ["liquid"],
        "allow_fallbacks": False,
        "max_price": {"prompt": 0, "completion": 0},
        "require_parameters": True,
    }
    with pytest.raises(RemoteAdmissionDenied, match="already_sent"):
        await broker.invoke(ticket)
    assert len(sent) == 1
