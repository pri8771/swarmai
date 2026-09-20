"""Fake provider adapter — no network, no secrets."""

from __future__ import annotations

from typing import Any

from swarm.contracts.common import utc_now
from swarm.contracts.enums import ErrorClass, ReservationPhase, SettlementState
from swarm.contracts.fixtures import sample_route, sample_route_beta
from swarm.contracts.provider import (
    AttemptReceipt,
    InferenceRequest,
    NormalizedUsage,
    Reservation,
    RouteSnapshot,
)


class FakeProviderAdapter:
    """Deterministic provider for offline tests. Secrets stay as refs only."""

    def __init__(self, routes: list[RouteSnapshot] | None = None) -> None:
        self.routes = {r.route_id: r for r in (routes or [sample_route(), sample_route_beta()])}
        self.calls: list[str] = []
        # Runtime-only; must never appear in durable envelopes.
        self._runtime_secret = object()

    async def discover(self) -> list[RouteSnapshot]:
        return list(self.routes.values())

    async def inspect_account(self, account_id: str) -> dict[str, Any]:
        return {"account_id": account_id, "status": "mock", "secret_present": False}

    async def describe_route(self, route_id: str) -> RouteSnapshot:
        return self.routes[route_id]

    async def execute_one(
        self, request: InferenceRequest, admitted_ticket: Reservation
    ) -> AttemptReceipt:
        if admitted_ticket.route_id not in self.routes:
            raise KeyError(admitted_ticket.route_id)
        self.calls.append(admitted_ticket.route_id)
        return AttemptReceipt(
            logical_call_id=admitted_ticket.logical_call_id,
            send_phase=ReservationPhase.SETTLED,
            finished_at=utc_now(),
            normalized_usage=NormalizedUsage(
                input_tokens=request.estimated_input_tokens or 0,
                output_tokens=8,
                total_tokens=(request.estimated_input_tokens or 0) + 8,
            ),
            actual_route=admitted_ticket.route_id,
            settlement_state=SettlementState.SETTLED,
        )

    async def normalize_usage(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    async def classify_error(self, exc: Exception) -> str:
        if isinstance(exc, TimeoutError):
            return ErrorClass.TRANSIENT.value
        return ErrorClass.UNKNOWN_OUTCOME.value
