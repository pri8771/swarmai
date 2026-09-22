"""PostgreSQL reservation fence for explicitly granted remote inference calls.

This gate has no grant-creation or network path. An operator-issued grant and
fresh account, route and quota records must already exist in the same database.
"""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
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


def verified_source_tree(checkout: Path) -> str:
    """Read the exact committed source tree from a clean Git worktree root."""
    root = checkout.resolve()

    def git(*args: str) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RemoteAdmissionDenied("source_checkout_unverifiable") from exc
        if result.returncode != 0:
            raise RemoteAdmissionDenied("source_checkout_unverifiable")
        return result.stdout.strip()

    if Path(git("rev-parse", "--show-toplevel")).resolve() != root:
        raise RemoteAdmissionDenied("source_checkout_not_git_root")
    if git("status", "--porcelain=v1", "--untracked-files=normal"):
        raise RemoteAdmissionDenied("source_checkout_dirty")
    tree = git("rev-parse", "HEAD^{tree}")
    if len(tree) != 40 or any(char not in "0123456789abcdef" for char in tree):
        raise RemoteAdmissionDenied("source_tree_invalid")
    return tree


def remote_request_hash(request: InferenceRequest, route: RouteSnapshot) -> str:
    """Exact payload binding for one approved provider request."""
    return payload_hash(
        {
            "project_id": request.project_id,
            "attempt_id": request.attempt_id,
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
        source_checkout: Path,
        max_evidence_age: timedelta = timedelta(minutes=10),
    ) -> None:
        self.factory = factory
        self.source_checkout = source_checkout.resolve()
        self.source_tree = verified_source_tree(self.source_checkout)
        self.max_evidence_age = max_evidence_age

    def _assert_source_unchanged(self) -> None:
        if verified_source_tree(self.source_checkout) != self.source_tree:
            raise RemoteAdmissionDenied("source_tree_changed")

    def reserve(
        self, request: InferenceRequest, route: RouteSnapshot, *, grant_id: str
    ) -> Reservation:
        """Atomically consume the grant and every observed route quota bucket."""
        self._assert_source_unchanged()
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
                buckets = session.scalars(
                    select(QuotaBucketRow)
                    .where(QuotaBucketRow.bucket_id.in_(sorted(route.quota_bucket_ids)))
                    .order_by(QuotaBucketRow.bucket_id)
                    .with_for_update()
                ).all()
                amounts = self._admit_buckets(request, route, grant, buckets, now)
                for bucket, amount in zip(buckets, amounts, strict=True):
                    assert bucket.remaining is not None
                    bucket.remaining -= amount.amount
                    bucket.version += 1
                grant.used_count += 1
                ticket = Reservation(
                    logical_call_id=logical_call_id,
                    attempt_id=request.attempt_id,
                    route_id=route.route_id,
                    bucket_amounts=amounts,
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
        self._assert_source_unchanged()
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
        """Settle certified usage; keep every hold after an uncertain send."""
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
            certified = (
                receipt.settlement_state == SettlementState.SETTLED
                and self._zero_cost_result(session, row, receipt)
                and self._usage_within_hold(row, receipt)
            )
            if certified:
                self._settle_usage_holds(session, row, receipt)
            session.add(
                AttemptReceiptRow(
                    network_attempt_id=receipt.network_attempt_id,
                    logical_call_id=receipt.logical_call_id,
                    idempotency_key=receipt.idempotency_key,
                    provider_request_id=receipt.provider_request_id,
                    actual_route=receipt.actual_route,
                    send_phase=receipt.send_phase.value,
                    settlement_state=(
                        SettlementState.SETTLED.value
                        if certified
                        else SettlementState.UNKNOWN.value
                    ),
                    error_class=receipt.error_class.value if receipt.error_class else None,
                    started_at=receipt.started_at,
                    finished_at=receipt.finished_at,
                    payload={
                        **receipt.model_dump(mode="json"),
                        "gate_settlement_state": "settled" if certified else "unknown",
                    },
                )
            )
            # A successful provider response alone cannot certify a free call.
            # Charge and route evidence are retained in the receipt payload.
            if certified:
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
            for amount in self._stored_amounts(row):
                bucket = session.scalar(
                    select(QuotaBucketRow)
                    .where(QuotaBucketRow.bucket_id == amount.bucket_id)
                    .with_for_update()
                )
                if bucket is None or bucket.remaining is None:
                    raise RemoteAdmissionDenied("held_bucket_missing")
                bucket.remaining += amount.amount
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

    def _stored_amounts(self, row: ReservationRow) -> list[BucketAmount]:
        raw = (row.payload or {}).get("bucket_amounts")
        if not isinstance(raw, list) or not 1 <= len(raw) <= 3:
            raise RemoteAdmissionDenied("stored_hold_missing")
        amounts: list[BucketAmount] = []
        seen_ids: set[str] = set()
        seen_dims: set[str] = set()
        for item in raw:
            if not isinstance(item, dict):
                raise RemoteAdmissionDenied("stored_hold_invalid")
            bucket_id = item.get("bucket_id")
            dimension = item.get("dimension")
            amount = item.get("amount")
            if (
                not isinstance(bucket_id, str)
                or bucket_id in seen_ids
                or dimension in seen_dims
                or dimension not in {"requests", "total_tokens", "concurrency"}
                or not isinstance(amount, int)
                or isinstance(amount, bool)
                or amount < 1
                or (dimension in {"requests", "concurrency"} and amount != 1)
            ):
                raise RemoteAdmissionDenied("stored_hold_invalid")
            seen_ids.add(bucket_id)
            seen_dims.add(dimension)
            amounts.append(
                BucketAmount(
                    bucket_id=bucket_id,
                    dimension=QuotaDimension(dimension),
                    amount=amount,
                )
            )
        if "requests" not in seen_dims:
            raise RemoteAdmissionDenied("stored_hold_invalid")
        return sorted(amounts, key=lambda amount: amount.bucket_id)

    def _admit_buckets(
        self,
        request: InferenceRequest,
        route: RouteSnapshot,
        grant: ApprovalRow,
        buckets: Sequence[QuotaBucketRow],
        now: Any,
    ) -> list[BucketAmount]:
        ids = route.quota_bucket_ids
        if not 1 <= len(ids) <= 3 or len(set(ids)) != len(ids) or len(buckets) != len(ids):
            raise RemoteAdmissionDenied("remote_quota_bucket_set_invalid")
        refs = (grant.constraints or {}).get("quota_evidence_refs")
        refs = refs if isinstance(refs, dict) else {}
        amounts: list[BucketAmount] = []
        dimensions: set[QuotaDimension] = set()
        for bucket in buckets:
            try:
                dimension = QuotaDimension(bucket.dimension)
            except ValueError as exc:
                raise RemoteAdmissionDenied("remote_quota_dimension_unsupported") from exc
            if dimension in dimensions or dimension not in {
                QuotaDimension.REQUESTS,
                QuotaDimension.TOTAL_TOKENS,
                QuotaDimension.CONCURRENCY,
            }:
                raise RemoteAdmissionDenied("remote_quota_dimension_unsupported")
            dimensions.add(dimension)
            if dimension == QuotaDimension.TOTAL_TOKENS:
                assert request.estimated_input_tokens is not None
                assert request.max_output_tokens is not None
                need = request.estimated_input_tokens + request.max_output_tokens
            else:
                need = 1
            evidence_ref = refs.get(dimension.value)
            if dimension == QuotaDimension.REQUESTS and evidence_ref is None:
                evidence_ref = (grant.constraints or {}).get("quota_evidence_ref")
            if (
                not evidence_ref
                or bucket.scope_type != "account"
                or bucket.scope_id != route.account_id
                or bucket.remaining is None
                or bucket.remaining < need
                or not self._fresh(bucket.observed_at, now)
                or (bucket.payload or {}).get("confidence") != "exact"
                or (bucket.payload or {}).get("quota_evidence_ref") != evidence_ref
            ):
                raise RemoteAdmissionDenied("remote_allowance_unverified_or_exhausted")
            amounts.append(
                BucketAmount(bucket_id=bucket.bucket_id, dimension=dimension, amount=need)
            )
        if QuotaDimension.REQUESTS not in dimensions:
            raise RemoteAdmissionDenied("request_allowance_missing")
        if request.purpose in {"mission", "production"} and dimensions != {
            QuotaDimension.REQUESTS,
            QuotaDimension.TOTAL_TOKENS,
            QuotaDimension.CONCURRENCY,
        }:
            raise RemoteAdmissionDenied("mission_token_and_concurrency_allowance_missing")
        return amounts

    def _usage_within_hold(self, row: ReservationRow, receipt: AttemptReceipt) -> bool:
        usage = receipt.normalized_usage
        if usage is None or usage.requests != 1:
            return False
        for amount in self._stored_amounts(row):
            if amount.dimension == QuotaDimension.TOTAL_TOKENS:
                observed = usage.total_tokens
                if observed is None or observed < 0 or observed > amount.amount:
                    return False
        return True

    def _settle_usage_holds(
        self, session: Session, row: ReservationRow, receipt: AttemptReceipt
    ) -> None:
        usage = receipt.normalized_usage
        assert usage is not None
        for amount in self._stored_amounts(row):
            if amount.dimension == QuotaDimension.REQUESTS:
                continue
            if amount.dimension == QuotaDimension.TOTAL_TOKENS:
                if usage.total_tokens is None:
                    raise RemoteAdmissionDenied("token_usage_missing")
                refund = amount.amount - usage.total_tokens
            else:
                refund = 1
            if refund <= 0:
                continue
            bucket = session.scalar(
                select(QuotaBucketRow)
                .where(QuotaBucketRow.bucket_id == amount.bucket_id)
                .with_for_update()
            )
            if bucket is None or bucket.remaining is None:
                raise RemoteAdmissionDenied("held_bucket_missing")
            bucket.remaining += refund
            bucket.version += 1

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
                and isinstance(routing.get("selected_provider"), str)
                and routing["selected_provider"].casefold()
                == (route.payload or {}).get("backend_slug")
                and routing.get("selected_model") == route.model_id
                and routing.get("attempt") == 1
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
