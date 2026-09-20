"""Fake inference broker that accounts every model request."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import (
    QuotaDimension,
    ReservationPhase,
    ReservationState,
    SettlementState,
)
from swarm.contracts.provider import (
    AttemptReceipt,
    BucketAmount,
    InferenceRequest,
    QuotaBucket,
    Reservation,
    RouteSnapshot,
)
from swarm.fakes.provider import FakeProviderAdapter


class BrokerBypassError(RuntimeError):
    """Raised when a model call is attempted without admission."""


class FakeInferenceBroker:
    """Counts every admitted invoke. Hidden retries must still call invoke()."""

    def __init__(
        self, adapter: FakeProviderAdapter, buckets: list[QuotaBucket] | None = None
    ) -> None:
        self.adapter = adapter
        self.buckets = {b.bucket_id: b for b in (buckets or [])}
        self.request_count = 0
        self.invocations: list[Reservation] = []
        self._tickets: dict[str, Reservation] = {}

    async def assess(self, request: InferenceRequest) -> list[RouteSnapshot]:
        routes = await self.adapter.discover()
        if request.route_id:
            return [r for r in routes if r.route_id == request.route_id]
        return routes

    async def reserve(self, request: InferenceRequest, route: RouteSnapshot) -> Reservation:
        amounts: list[BucketAmount] = []
        for bucket_id in route.quota_bucket_ids:
            bucket = self.buckets.get(bucket_id)
            if bucket is None:
                continue
            if bucket.remaining is not None and bucket.remaining < 1:
                raise RuntimeError("quota_exhausted")
            if bucket.remaining is not None:
                bucket.remaining -= 1
            amounts.append(
                BucketAmount(bucket_id=bucket_id, dimension=bucket.dimension, amount=1)
            )
        ticket = Reservation(
            logical_call_id=new_id("lc_"),
            attempt_id=request.attempt_id,
            route_id=route.route_id,
            bucket_amounts=amounts or [
                BucketAmount(
                    bucket_id="qb_unbounded_mock",
                    dimension=QuotaDimension.REQUESTS,
                    amount=1,
                )
            ],
            expires_at=utc_now() + timedelta(minutes=5),
            phase=ReservationPhase.RESERVED,
            state=ReservationState.OPEN,
        )
        self._tickets[ticket.reservation_id] = ticket
        return ticket

    async def invoke(self, ticket: Reservation) -> AttemptReceipt:
        if ticket.reservation_id not in self._tickets:
            raise BrokerBypassError("invoke requires a reserved ticket")
        ticket.phase = ReservationPhase.SENDING
        self.request_count += 1
        self.invocations.append(ticket)
        # Build a minimal request envelope for the adapter; secrets remain refs.
        request = InferenceRequest(
            project_id="proj_demo",
            attempt_id=ticket.attempt_id,
            route_id=ticket.route_id,
            purpose="broker_invoke",
            messages=[{"role": "user", "content": "brokered"}],
            secret_ref_names=[],
        )
        ticket.phase = ReservationPhase.SENT
        receipt = await self.adapter.execute_one(request, ticket)
        ticket.phase = ReservationPhase.SETTLED
        ticket.state = ReservationState.COMMITTED
        return receipt

    async def reconcile(self, receipt: AttemptReceipt) -> AttemptReceipt:
        if receipt.settlement_state == SettlementState.PENDING:
            receipt.settlement_state = SettlementState.SETTLED
        return receipt

    async def explain(self, decision_id: str) -> dict[str, Any]:
        return {
            "decision_id": decision_id,
            "request_count": self.request_count,
            "routes_used": [t.route_id for t in self.invocations],
        }

    def assert_all_calls_accounted(self) -> None:
        if self.request_count != len(self.adapter.calls):
            raise BrokerBypassError(
                f"broker={self.request_count} adapter={len(self.adapter.calls)} — bypass detected"
            )
