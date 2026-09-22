"""PostgreSQL reservation fence for explicitly granted remote inference calls.

This gate has no grant-creation or network path. An operator-issued grant and
fresh account, route and quota records must already exist in the same database.
"""

from __future__ import annotations

import hashlib
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from swarm.contracts.common import payload_hash, utc_now
from swarm.contracts.enums import (
    AccountStatus,
    AvailabilityStatus,
    BillingMode,
    QuotaDimension,
    ReservationPhase,
    ReservationState,
    SettlementState,
)
from swarm.contracts.provider import (
    AttemptReceipt,
    BucketAmount,
    InferenceRequest,
    Reservation,
    RouteSnapshot,
)
from swarm.db.engine import session_scope
from swarm.db.models import (
    ApprovalRow,
    AttemptReceiptRow,
    ProviderAccountRow,
    QuotaBucketRow,
    ReservationRow,
    RouteSnapshotRow,
)


class RemoteAdmissionDenied(PermissionError):
    """A remote call was refused before any provider network request."""


def remote_request_hash(request: InferenceRequest, route: RouteSnapshot) -> str:
    """Exact payload binding for one approved provider request."""
    return payload_hash(
        {
            "project_id": request.project_id,
            "route_id": route.route_id,
            "provider": route.provider,
            "account_id": route.account_id,
            "model_id": route.model_id,
            "backend": route.hosted_by,
            "purpose": request.purpose,
            "messages": request.messages,
            "estimated_input_tokens": request.estimated_input_tokens,
            "max_output_tokens": request.max_output_tokens,
            "tools_requested": request.tools_requested,
            "secret_ref_names": request.secret_ref_names,
        }
    )


class DurableRemoteCallGate:
    """One-attempt call fence; PostgreSQL rows remain after process restart."""

    def __init__(
        self,
        factory: sessionmaker[Session],
        *,
        source_tree: str,
        max_evidence_age: timedelta = timedelta(minutes=10),
    ) -> None:
        if len(source_tree) != 40 or any(c not in "0123456789abcdef" for c in source_tree):
            raise ValueError("source_tree must be an exact Git tree SHA")
        self.factory = factory
        self.source_tree = source_tree
        self.max_evidence_age = max_evidence_age

    def reserve(
        self, request: InferenceRequest, route: RouteSnapshot, *, grant_id: str
    ) -> Reservation:
        """Atomically consume one grant use and one observed request allowance."""
        if route.provider not in {"groq", "openrouter"}:
            raise RemoteAdmissionDenied("provider_not_released_for_remote_gate")
        if request.route_id != route.route_id or request.max_output_tokens is None:
            raise RemoteAdmissionDenied("request_route_or_output_unbound")
        if request.estimated_input_tokens is None or request.estimated_input_tokens < 0:
            raise RemoteAdmissionDenied("input_estimate_missing")
        now = utc_now()
        request_hash = remote_request_hash(request, route)
        logical_call_id = "lc_" + hashlib.sha256(
            f"{request.project_id}:{request.attempt_id}:{route.route_id}".encode()
        ).hexdigest()[:32]
        try:
            with session_scope(self.factory) as session:
                grant = session.scalar(
                    select(ApprovalRow)
                    .where(ApprovalRow.id == grant_id)
                    .with_for_update()
                )
                self._check_grant(grant, request, route, request_hash, now)
                assert grant is not None
                self._check_account_route(session, route, grant, now)
                if len(route.quota_bucket_ids) != 1:
                    raise RemoteAdmissionDenied("exactly_one_request_bucket_required")
                bucket_id = route.quota_bucket_ids[0]
                bucket = session.scalar(
                    select(QuotaBucketRow)
                    .where(QuotaBucketRow.bucket_id == bucket_id)
                    .with_for_update()
                )
                if (
                    bucket is None
                    or bucket.scope_type != "account"
                    or bucket.scope_id != route.account_id
                    or bucket.dimension != QuotaDimension.REQUESTS.value
                    or bucket.remaining is None
                    or bucket.remaining < 1
                    or not self._fresh(bucket.observed_at, now)
                    or (bucket.payload or {}).get("confidence") != "exact"
                    or (bucket.payload or {}).get("quota_evidence_ref")
                    != (grant.constraints or {}).get("quota_evidence_ref")
                ):
                    raise RemoteAdmissionDenied("request_allowance_unverified_or_exhausted")
                bucket.remaining -= 1
                bucket.version += 1
                grant.used_count += 1
                ticket = Reservation(
                    logical_call_id=logical_call_id,
                    attempt_id=request.attempt_id,
                    route_id=route.route_id,
                    bucket_amounts=[
                        BucketAmount(
                            bucket_id=bucket_id, dimension=QuotaDimension.REQUESTS, amount=1
                        )
                    ],
                    expires_at=min(grant.expires_at, now + timedelta(minutes=2)),
                )
                session.add(
                    ReservationRow(
                        reservation_id=ticket.reservation_id,
                        logical_call_id=ticket.logical_call_id,
                        attempt_id=ticket.attempt_id,
                        route_id=ticket.route_id,
                        state=ticket.state.value,
                        phase=ticket.phase.value,
                        fence_token=ticket.fence_token,
                        expires_at=ticket.expires_at,
                        payload={
                            **ticket.model_dump(mode="json"),
                            "grant_id": grant_id,
                            "request_hash": request_hash,
                            "source_tree": self.source_tree,
                        },
                    )
                )
                session.flush()
                return ticket
        except IntegrityError as exc:
            raise RemoteAdmissionDenied("duplicate_attempt_reservation") from exc

    def mark_sending(self, ticket: Reservation) -> None:
        """Commit SENDING before the adapter can put bytes on the wire."""
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ReservationRow)
                .where(ReservationRow.reservation_id == ticket.reservation_id)
                .with_for_update()
            )
            if (
                row is None
                or row.fence_token != ticket.fence_token
                or row.logical_call_id != ticket.logical_call_id
                or row.route_id != ticket.route_id
                or row.state != ReservationState.OPEN.value
                or row.phase != ReservationPhase.RESERVED.value
                or row.expires_at <= utc_now()
            ):
                raise RemoteAdmissionDenied("remote_call_not_resendable")
            row.phase = ReservationPhase.SENDING.value
            row.payload = {**(row.payload or {}), "phase": row.phase}

    def record_result(self, ticket: Reservation, receipt: AttemptReceipt) -> None:
        """Persist terminal or unknown outcome; never replenish a sent call."""
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ReservationRow)
                .where(ReservationRow.reservation_id == ticket.reservation_id)
                .with_for_update()
            )
            if (
                row is None
                or row.fence_token != ticket.fence_token
                or row.logical_call_id != receipt.logical_call_id
                or row.route_id != receipt.actual_route
                or row.phase != ReservationPhase.SENDING.value
            ):
                raise RemoteAdmissionDenied("remote_result_without_sending_fence")
            session.add(
                AttemptReceiptRow(
                    network_attempt_id=receipt.network_attempt_id,
                    logical_call_id=receipt.logical_call_id,
                    idempotency_key=receipt.idempotency_key,
                    provider_request_id=receipt.provider_request_id,
                    actual_route=receipt.actual_route,
                    send_phase=receipt.send_phase.value,
                    settlement_state=receipt.settlement_state.value,
                    error_class=receipt.error_class.value if receipt.error_class else None,
                    started_at=receipt.started_at,
                    finished_at=receipt.finished_at,
                    payload=receipt.model_dump(mode="json"),
                )
            )
            # A successful provider response alone cannot certify a free call.
            # Charge and route evidence are retained in the receipt payload.
            if receipt.settlement_state == SettlementState.SETTLED and self._zero_cost_result(
                session, row, receipt
            ):
                row.state = ReservationState.COMMITTED.value
                row.phase = ReservationPhase.SETTLED.value
            else:
                row.state = ReservationState.UNKNOWN.value
                row.phase = ReservationPhase.UNKNOWN.value
            row.payload = {**(row.payload or {}), "state": row.state, "phase": row.phase}

    def release_unsent(self, ticket: Reservation) -> None:
        """Refund quota only when the durable row proves the call never sent."""
        with session_scope(self.factory) as session:
            row = session.scalar(
                select(ReservationRow)
                .where(ReservationRow.reservation_id == ticket.reservation_id)
                .with_for_update()
            )
            if (
                row is None
                or row.fence_token != ticket.fence_token
                or row.phase != ReservationPhase.RESERVED.value
                or row.state != ReservationState.OPEN.value
            ):
                raise RemoteAdmissionDenied("cannot_release_sent_or_unknown_call")
            # The caller's ticket is mutable. Refund only the stored hold.
            stored_amounts = (row.payload or {}).get("bucket_amounts")
            if not isinstance(stored_amounts, list) or len(stored_amounts) != 1:
                raise RemoteAdmissionDenied("stored_hold_missing")
            for amount in stored_amounts:
                if (
                    not isinstance(amount, dict)
                    or amount.get("dimension") != QuotaDimension.REQUESTS.value
                    or amount.get("amount") != 1
                ):
                    raise RemoteAdmissionDenied("stored_hold_invalid")
                bucket = session.scalar(
                    select(QuotaBucketRow)
                    .where(QuotaBucketRow.bucket_id == amount.get("bucket_id"))
                    .with_for_update()
                )
                if bucket is None or bucket.remaining is None:
                    raise RemoteAdmissionDenied("held_bucket_missing")
                bucket.remaining += 1
                bucket.version += 1
            row.state = ReservationState.RELEASED.value
            row.payload = {**(row.payload or {}), "state": row.state}
            # Deliberately do not renew the owner's one-use grant.

    def read_state(self, reservation_id: str) -> dict[str, Any] | None:
        with session_scope(self.factory) as session:
            row = session.get(ReservationRow, reservation_id)
            if row is None:
                return None
            return {
                "reservation_id": row.reservation_id,
                "logical_call_id": row.logical_call_id,
                "route_id": row.route_id,
                "state": row.state,
                "phase": row.phase,
                "grant_id": (row.payload or {}).get("grant_id"),
            }

    def _fresh(self, observed_at: Any, now: Any) -> bool:
        return (
            observed_at is not None
            and timedelta(0) <= now - observed_at <= self.max_evidence_age
        )

    def _zero_cost_result(
        self, session: Session, row: ReservationRow, receipt: AttemptReceipt
    ) -> bool:
        usage = receipt.normalized_usage
        if usage is None or receipt.send_phase != ReservationPhase.SETTLED:
            return False
        extras = usage.extras
        if (
            extras.get("provider_cost_status") != "reported"
            or extras.get("provider_cost_source") != "response.usage.cost"
        ):
            return False
        cost_raw = extras.get("provider_cost_usd")
        if not isinstance(cost_raw, str):
            return False
        try:
            cost = Decimal(cost_raw)
        except (InvalidOperation, TypeError, ValueError):
            return False
        if not cost.is_finite() or cost != 0:
            return False
        route = session.get(RouteSnapshotRow, row.route_id)
        if route is None:
            return False
        if route.provider == "openrouter":
            routing = extras.get("openrouter_routing")
            return (
                isinstance(routing, dict)
                and routing.get("selected_provider") == (route.payload or {}).get("backend_slug")
                and routing.get("is_byok") is False
                and routing.get("usage_is_byok") is False
            )
        return route.provider == "groq"

    def _check_grant(
        self,
        grant: ApprovalRow | None,
        request: InferenceRequest,
        route: RouteSnapshot,
        request_hash: str,
        now: Any,
    ) -> None:
        if grant is None:
            raise RemoteAdmissionDenied("stored_owner_grant_missing")
        constraints = grant.constraints or {}
        if (
            grant.project_id != request.project_id
            or grant.grantor != "operator"
            or grant.integration_id != "swarm.remote_inference"
            or grant.integration_version != "1"
            or grant.permitted_operation != "infer"
            or grant.operation != "infer"
            or grant.destination != route.route_id
            or grant.payload_hash != request_hash
            or grant.revoked_at is not None
            or grant.expires_at <= now
            or grant.max_effect_count != 1
            or grant.used_count != 0
            or constraints.get("source_tree") != self.source_tree
            or constraints.get("account_id") != route.account_id
            or constraints.get("model_id") != route.model_id
            or constraints.get("backend_slug") != route.hosted_by
            or constraints.get("max_output_tokens") != request.max_output_tokens
            or not constraints.get("zero_charge_evidence_ref")
            or not constraints.get("quota_evidence_ref")
        ):
            raise RemoteAdmissionDenied("stored_owner_grant_mismatch_or_expired")

    def _check_account_route(
        self, session: Session, route: RouteSnapshot, grant: ApprovalRow, now: Any
    ) -> None:
        account = session.get(ProviderAccountRow, route.account_id)
        observed = session.get(RouteSnapshotRow, route.route_id)
        constraints = grant.constraints or {}
        if (
            account is None
            or account.service_id != route.provider
            or account.account_status != AccountStatus.AUTHENTICATED.value
            or account.billing_mode != BillingMode.FREE.value
            or not self._fresh(account.verified_at, now)
            or (account.payload or {}).get("tier") != "free"
            or (account.payload or {}).get("zero_charge_evidence_ref")
            != constraints.get("zero_charge_evidence_ref")
            or observed is None
            or observed.account_id != route.account_id
            or observed.provider != route.provider
            or observed.model_id != route.model_id
            or observed.endpoint != route.endpoint
            or observed.billing_origin != route.billing_origin
            or observed.availability_status != AvailabilityStatus.AVAILABLE.value
            or not self._fresh(observed.observed_at, now)
            or (observed.payload or {}).get("zero_price_verified") is not True
            or (observed.payload or {}).get("zero_charge_evidence_ref")
            != constraints.get("zero_charge_evidence_ref")
        ):
            raise RemoteAdmissionDenied("account_or_route_evidence_unverified")
        if route.provider == "openrouter":
            if (
                not route.model_id.endswith(":free")
                or not route.hosted_by
                or (observed.payload or {}).get("backend_slug") != route.hosted_by
                or (account.payload or {}).get("byok_disabled_verified") is not True
            ):
                raise RemoteAdmissionDenied("openrouter_free_backend_unverified")
