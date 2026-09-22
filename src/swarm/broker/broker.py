"""Shared inference broker — assess, reserve, invoke, reconcile, explain."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from swarm.broker.circuit import CircuitBreaker
from swarm.broker.errors import (
    AmbiguousSendError,
    BrokerBypassError,
    DuplicateSettlementError,
)
from swarm.broker.ledger import LedgerConfig, QuotaLedger
from swarm.broker.policy import AdmissionPolicy, RoutePolicyContext
from swarm.broker.retry import RetryOwner
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import (
    ErrorClass,
    QuotaDimension,
    ReservationPhase,
    ReservationState,
    SettlementState,
)
from swarm.contracts.provider import (
    AttemptReceipt,
    InferenceRequest,
    QuotaBucket,
    Reservation,
    RouteSnapshot,
)

Clock = Callable[[], datetime]


@dataclass
class PendingCall:
    request: InferenceRequest
    ticket: Reservation
    route: RouteSnapshot
    decision_id: str
    sent: bool = False
    settled: bool = False
    receipt: AttemptReceipt | None = None


@dataclass
class DecisionRecord:
    decision_id: str
    request: InferenceRequest
    eligible: list[str] = field(default_factory=list)
    blocked: list[dict[str, str]] = field(default_factory=list)
    selected_route: str | None = None
    qualification_rationale: str | None = None
    bottleneck: dict[str, object] | None = None
    reserved: list[dict[str, object]] = field(default_factory=list)
    wake_condition: str | None = None
    purpose: str = ""


class SharedInferenceBroker:
    """Mandatory call boundary. Every model request must pass through invoke()."""

    def __init__(
        self,
        adapter: Any,
        buckets: list[QuotaBucket] | None = None,
        *,
        route_contexts: dict[str, RoutePolicyContext] | None = None,
        policy: AdmissionPolicy | None = None,
        ledger_config: LedgerConfig | None = None,
        circuit: CircuitBreaker | None = None,
        retry_owner: RetryOwner | None = None,
        clock: Clock | None = None,
        reservation_ttl: timedelta | None = None,
    ) -> None:
        self.adapter = adapter
        self.policy = policy or AdmissionPolicy()
        self.ledger = QuotaLedger(buckets, config=ledger_config, clock=clock)
        self.circuit = circuit or CircuitBreaker(clock=clock)
        self.retry = retry_owner or RetryOwner(clock=clock)
        self._clock: Clock = clock or utc_now
        self._ttl = reservation_ttl or timedelta(minutes=5)
        self._contexts: dict[str, RoutePolicyContext] = {}
        for route_id, ctx in (route_contexts or {}).items():
            if route_id != ctx.route.route_id:
                raise BrokerBypassError("route_context_key_mismatch")
            self.register_route(ctx)
        self._tickets: dict[str, PendingCall] = {}
        self._decisions: dict[str, DecisionRecord] = {}
        self._attempt_decisions: dict[str, str] = {}
        self._settlement_keys: set[str] = set()
        self._logical_attempts: dict[str, set[str]] = {}
        self.request_count = 0
        self.invocations: list[Reservation] = []
        self._fair_queue: asyncio.Lock = asyncio.Lock()
        self._queue_weights: dict[str, float] = {}
        self.last_decision_id: str | None = None

    def register_route(self, ctx: RoutePolicyContext) -> None:
        self._contexts[ctx.route.route_id] = deepcopy(ctx)

    @staticmethod
    def _same_admission_route(left: RouteSnapshot, right: RouteSnapshot) -> bool:
        """Compare every field that can change admission, origin or accounting."""
        fields = (
            "route_id",
            "provider",
            "account_id",
            "model_id",
            "endpoint",
            "hosted_by",
            "billing_origin",
            "availability_status",
            "status",
            "quota_bucket_ids",
            "privacy_policy_ref",
            "model_terms_ref",
        )
        return all(getattr(left, name) == getattr(right, name) for name in fields)

    async def assess(self, request: InferenceRequest) -> list[RouteSnapshot]:
        routes = await self.adapter.discover()
        if request.route_id:
            routes = [r for r in routes if r.route_id == request.route_id]

        decision_id = new_id("dec_")
        record = DecisionRecord(
            decision_id=decision_id,
            request=request,
            purpose=request.purpose,
        )
        eligible: list[RouteSnapshot] = []
        for route in routes:
            ctx = self._contexts.get(route.route_id)
            if ctx is None or not self._same_admission_route(ctx.route, route):
                record.blocked.append(
                    {
                        "route_id": route.route_id,
                        "reason": "route_context_unregistered"
                        if ctx is None
                        else "route_snapshot_changed",
                        "dimension": "authority",
                    }
                )
                continue
            decision = self.policy.evaluate(request, ctx)
            if decision.allowed:
                try:
                    self.circuit.assert_closed(route.route_id)
                except Exception as exc:  # CircuitOpenError
                    record.blocked.append(
                        {"route_id": route.route_id, "reason": str(exc), "dimension": "health"}
                    )
                    continue
                eligible.append(route)
                record.eligible.append(route.route_id)
                record.qualification_rationale = ctx.qualification_rationale
            else:
                record.blocked.append(
                    {
                        "route_id": route.route_id,
                        "reason": decision.reason,
                        "dimension": decision.blocked_dimension or "policy",
                    }
                )
        self._decisions[decision_id] = record
        self._attempt_decisions[request.attempt_id] = decision_id
        self.last_decision_id = decision_id
        return eligible

    async def reserve(self, request: InferenceRequest, route: RouteSnapshot) -> Reservation:
        if request.route_id is not None and request.route_id != route.route_id:
            raise BrokerBypassError("request_route_mismatch")
        ctx = self._contexts.get(route.route_id)
        if ctx is None:
            raise BrokerBypassError("route_context_unregistered")
        if not self._same_admission_route(ctx.route, route):
            raise BrokerBypassError("route_snapshot_changed")
        self.policy.assert_allowed(request, ctx)
        self.circuit.assert_closed(route.route_id)

        # Fair queue admission: age priority by purpose weight.
        async with self._fair_queue:
            weight = self._queue_weights.get(request.purpose, 1.0)
            self._queue_weights[request.purpose] = weight + 0.01

        amounts = self.ledger.estimate_amounts(
            bucket_ids=list(ctx.route.quota_bucket_ids),
            estimated_input_tokens=request.estimated_input_tokens,
            max_output_tokens=request.max_output_tokens,
            purpose=request.purpose,
        )
        probe = request.purpose in {"probe", "catalog"}
        reserved = await self.ledger.reserve(
            amounts, route_id=route.route_id, purpose=request.purpose, probe=probe
        )

        logical_call_id = new_id("lc_")
        # Unique logical-call/attempt keys.
        attempts = self._logical_attempts.setdefault(logical_call_id, set())
        if request.attempt_id in attempts:
            await self.ledger.release(reserved)
            raise BrokerBypassError("duplicate_attempt_id_for_logical_call")
        attempts.add(request.attempt_id)
        self.retry.note_attempt(logical_call_id)

        ticket = Reservation(
            logical_call_id=logical_call_id,
            attempt_id=request.attempt_id,
            route_id=route.route_id,
            bucket_amounts=reserved,
            expires_at=self._clock() + self._ttl,
            phase=ReservationPhase.RESERVED,
            state=ReservationState.OPEN,
        )
        decision_id = self._attempt_decisions.get(request.attempt_id) or self.last_decision_id
        if decision_id is None or decision_id not in self._decisions:
            decision_id = new_id("dec_")
            self._decisions[decision_id] = DecisionRecord(
                decision_id=decision_id, request=request, purpose=request.purpose
            )
            self._attempt_decisions[request.attempt_id] = decision_id
            self.last_decision_id = decision_id
        rec = self._decisions[decision_id]
        rec.selected_route = route.route_id
        rec.qualification_rationale = ctx.qualification_rationale
        rec.reserved = [
            {"bucket_id": a.bucket_id, "dimension": a.dimension.value, "amount": a.amount}
            for a in reserved
        ]
        rec.bottleneck = self.ledger.bottleneck(reserved)

        self._tickets[ticket.reservation_id] = PendingCall(
            request=request,
            ticket=ticket,
            route=route,
            decision_id=decision_id,
        )
        return ticket

    async def invoke(self, ticket: Reservation) -> AttemptReceipt:
        pending = self._tickets.get(ticket.reservation_id)
        if pending is None:
            raise BrokerBypassError("invoke requires a reserved ticket")
        if pending.sent and pending.receipt is not None:
            # Idempotent re-entry after ambiguous send: return retained receipt.
            return pending.receipt

        now = self._clock()
        if ticket.expires_at < now and ticket.phase == ReservationPhase.RESERVED:
            await self.ledger.release(ticket.bucket_amounts)
            ticket.state = ReservationState.EXPIRED
            raise BrokerBypassError("reservation_expired_unsent")

        ticket.phase = ReservationPhase.SENDING
        pending.sent = True
        self.request_count += 1
        self.invocations.append(ticket)

        try:
            raw_receipt = await self.adapter.execute_one(pending.request, ticket)
            receipt: AttemptReceipt = raw_receipt
            ticket.phase = ReservationPhase.SENT
            # Partial stream surfaces as error class on receipt.
            if receipt.error_class == ErrorClass.PARTIAL_STREAM:
                pending.receipt = receipt
                receipt.settlement_state = SettlementState.UNKNOWN
                ticket.phase = ReservationPhase.UNKNOWN
                ticket.state = ReservationState.UNKNOWN
                self.circuit.record_error(ticket.route_id, ErrorClass.PARTIAL_STREAM)
                return receipt
            if receipt.error_class == ErrorClass.UNKNOWN_OUTCOME:
                pending.receipt = receipt
                ticket.phase = ReservationPhase.UNKNOWN
                ticket.state = ReservationState.UNKNOWN
                self.circuit.record_error(ticket.route_id, ErrorClass.UNKNOWN_OUTCOME)
                raise AmbiguousSendError(receipt.logical_call_id)

            ticket.phase = ReservationPhase.SETTLED
            pending.receipt = receipt
            self.circuit.record_success(ticket.route_id)
            await self.reconcile(receipt)
            return receipt
        except AmbiguousSendError:
            raise
        except Exception as exc:
            classified = await self.adapter.classify_error(exc)
            self.circuit.record_error(ticket.route_id, classified)
            # Post-send unknown: if we already flipped to SENDING, retain.
            if pending.sent and ticket.phase in {
                ReservationPhase.SENDING,
                ReservationPhase.SENT,
                ReservationPhase.UNKNOWN,
            }:
                receipt = AttemptReceipt(
                    logical_call_id=ticket.logical_call_id,
                    send_phase=ReservationPhase.UNKNOWN,
                    actual_route=ticket.route_id,
                    error_class=ErrorClass(classified)
                    if classified in ErrorClass._value2member_map_
                    else ErrorClass.UNKNOWN_OUTCOME,
                    settlement_state=SettlementState.UNKNOWN,
                )
                pending.receipt = receipt
                ticket.phase = ReservationPhase.UNKNOWN
                ticket.state = ReservationState.UNKNOWN
                raise AmbiguousSendError(str(exc)) from exc
            await self.ledger.release(ticket.bucket_amounts)
            ticket.state = ReservationState.RELEASED
            raise

    async def reconcile(self, receipt: AttemptReceipt) -> AttemptReceipt:
        key = receipt.idempotency_key or f"{receipt.logical_call_id}:{receipt.network_attempt_id}"
        if key in self._settlement_keys:
            raise DuplicateSettlementError(key)

        pending = None
        for p in self._tickets.values():
            if p.ticket.logical_call_id == receipt.logical_call_id:
                pending = p
                break

        actual: dict[QuotaDimension, int] | None = None
        if receipt.normalized_usage is not None:
            u = receipt.normalized_usage
            actual = {
                QuotaDimension.REQUESTS: u.requests,
            }
            if u.input_tokens is not None:
                actual[QuotaDimension.INPUT_TOKENS] = u.input_tokens
            if u.output_tokens is not None:
                actual[QuotaDimension.OUTPUT_TOKENS] = u.output_tokens
            if u.total_tokens is not None:
                actual[QuotaDimension.TOTAL_TOKENS] = u.total_tokens
            if u.uncached_tokens is not None:
                actual[QuotaDimension.UNCACHED_TOKENS] = u.uncached_tokens

        if pending is not None:
            await self.ledger.settle(
                pending.ticket.bucket_amounts,
                settlement_key=key,
                actual_usage=actual,
            )
            pending.settled = True
            pending.ticket.state = ReservationState.COMMITTED
            pending.ticket.phase = ReservationPhase.SETTLED
        else:
            # Still mark settlement key to prevent duplicates.
            self._settlement_keys.add(key)

        self._settlement_keys.add(key)
        receipt.settlement_state = SettlementState.SETTLED
        return receipt

    async def explain(self, decision_id: str) -> dict[str, Any]:
        rec = self._decisions.get(decision_id)
        if rec is None:
            # Fall back: search by attempt.
            for r in self._decisions.values():
                if r.request.attempt_id == decision_id or r.decision_id == decision_id:
                    rec = r
                    break
        if rec is None:
            return {
                "decision_id": decision_id,
                "eligible_routes": [],
                "blocked_routes": [],
                "error": "decision_not_found",
            }
        wake = rec.wake_condition
        if rec.bottleneck and wake is None:
            dim = rec.bottleneck.get("dimension")
            reason = rec.bottleneck.get("reason")
            wake = f"wait_until:{dim}:{reason}"
        return {
            "decision_id": rec.decision_id,
            "purpose": rec.purpose,
            "eligible_routes": list(rec.eligible),
            "blocked_routes": list(rec.blocked),
            "selected_route": rec.selected_route,
            "qualification_rationale": rec.qualification_rationale,
            "bottleneck": rec.bottleneck,
            "reserved": list(rec.reserved),
            "expected_wake_condition": wake,
            "request_count": self.request_count,
            # Distinct quota units are not collapsed.
            "quota_units_note": "dimensions kept separate; do not sum incompatible units",
        }

    def assert_all_calls_accounted(self) -> None:
        adapter_calls = getattr(self.adapter, "calls", None)
        if adapter_calls is None:
            return
        if self.request_count != len(adapter_calls):
            raise BrokerBypassError(
                f"broker={self.request_count} adapter={len(adapter_calls)} — bypass detected"
            )

    async def expire_unsent(self, reservation_id: str) -> None:
        pending = self._tickets.get(reservation_id)
        if pending is None or pending.sent:
            return
        await self.ledger.release(pending.ticket.bucket_amounts)
        pending.ticket.state = ReservationState.EXPIRED
