"""V2A-003a/b/c/R / ART-V15-LEASE-FENCING — durable worker/attempt/lease/result repos.

V2A-003a: persistence primitives (token_hash only — V2A-H2).
V2A-003b/R: atomic claim/renew/expire (+ H3 eligible skip, authority checks, paginated HOL).
V2A-003c: durable result submission + acceptance fence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import literal, select, tuple_
from sqlalchemy.orm import Session

from swarm.contracts.common import new_id, utc_now
from swarm.db.models import (
    MissionRow,
    OutboxRow,
    TaskAttemptRow,
    TaskLeaseRow,
    TaskRow,
    WorkerLeaseRow,
    WorkerResultRow,
)
from swarm.db.token_hash import (
    hash_membership_token,
    new_token_id,
    verify_membership_token,
)

_ACTIVE_LEASE_STATES = frozenset({"active", "renewed"})
_CLAIMABLE_TASK_STATUS = "ready"
_DEFAULT_LEASE_SECONDS = 60
_DEFAULT_RENEWABLE_HORIZON_SECONDS = 3600
# Page size for SKIP LOCKED scans only — not a correctness ceiling (V2A-003b-R).
_CLAIM_CANDIDATE_PAGE = 32
_RUNNABLE_MISSION_STATUSES = frozenset(
    {
        "planning",
        "running",
        "waiting_capacity",
        "waiting_input",
        "waiting_approval",
        "verifying",
    }
)
# Durable dependency terminals that unblock a dependent claim (V2A-003b-R).
_DEPENDENCY_DONE_STATUSES = frozenset({"accepted", "completed"})
_NON_DISPATCHABLE_ON_STALE_EXPIRE = "superseded"
_CANCELLED_ON_EXPIRE = "cancelled"
# Terminal task states that must never renew even if the mission is still runnable.
_TERMINAL_TASK_STATUSES = frozenset(
    {"accepted", "rejected", "failed", "cancelled", "superseded"}
)
# Attempt statuses that are no longer renewable.
_TERMINAL_ATTEMPT_STATUSES = frozenset(
    {"succeeded", "failed", "cancelled", "expired", "accepted"}
)


class RawTokenPersistenceError(ValueError):
    """Raised when a caller attempts to persist a raw membership token."""


_FORBIDDEN_RAW_KEYS = frozenset(
    {
        "token",
        "membership_token",
        "raw_token",
        "bearer_token",
        "worker_token",
    }
)


def _assert_no_raw_token_fields(payload: Any, *, path: str = "resource_payload") -> None:
    """Recursively reject token-sensitive keys in free-form metadata (V2A-003a-R / H2)."""
    if payload is None:
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_path = f"{path}.{key}"
            if str(key).lower() in _FORBIDDEN_RAW_KEYS:
                raise RawTokenPersistenceError(f"raw_token_field_forbidden:{key_path}")
            _assert_no_raw_token_fields(value, path=key_path)
        return
    if isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            _assert_no_raw_token_fields(value, path=f"{path}[{index}]")
        return


class WorkerRegistrationRepository:
    """Durable worker registration rows (existing worker_leases table)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_registration(
        self,
        *,
        worker_id: str,
        project_id: str,
        node_identity: str,
        architecture: str,
        runtime_version: str,
        capacity_units: float,
        membership_token: str,
        status: str = "online",
        generation: int = 1,
        trust_class: str = "standard",
        labels: list[Any] | None = None,
        capabilities: list[Any] | None = None,
        privacy_classes: list[Any] | None = None,
        resource_payload: dict[str, Any] | None = None,
        policy_version: str | None = None,
        software_version: str | None = None,
        build_sha: str | None = None,
        token_id: str | None = None,
    ) -> tuple[WorkerLeaseRow, str]:
        """Persist registration with token_hash/token_id only.

        Returns (row, token_id). The raw membership_token is never written.
        """
        _assert_no_raw_token_fields(resource_payload)
        now = utc_now()
        tid = token_id or new_token_id()
        digest = hash_membership_token(membership_token)
        existing = self.session.get(WorkerLeaseRow, worker_id)
        if existing is None:
            row = WorkerLeaseRow(
                worker_id=worker_id,
                node_identity=node_identity,
                architecture=architecture,
                runtime_version=runtime_version,
                capacity_units=capacity_units,
                lease_generation=generation,
                status=status,
                heartbeat_at=now,
                labels=list(labels or []),
                capabilities=list(capabilities or []),
                project_id=project_id,
                trust_class=trust_class,
                token_hash=digest,
                token_id=tid,
                registered_at=now,
                updated_at=now,
                policy_version=policy_version,
                software_version=software_version,
                build_sha=build_sha,
                privacy_classes=list(privacy_classes or ["local"]),
                resource_payload=dict(resource_payload or {}),
            )
            self.session.add(row)
            self.session.flush()
            self._assert_row_has_no_raw_token(row)
            return row, tid

        existing.node_identity = node_identity
        existing.architecture = architecture
        existing.runtime_version = runtime_version
        existing.capacity_units = capacity_units
        existing.lease_generation = generation
        existing.status = status
        existing.heartbeat_at = now
        existing.labels = list(labels or [])
        existing.capabilities = list(capabilities or [])
        existing.project_id = project_id
        existing.trust_class = trust_class
        existing.token_hash = digest
        existing.token_id = tid
        existing.updated_at = now
        existing.policy_version = policy_version
        existing.software_version = software_version
        existing.build_sha = build_sha
        existing.privacy_classes = list(privacy_classes or ["local"])
        existing.resource_payload = dict(resource_payload or {})
        self.session.flush()
        self._assert_row_has_no_raw_token(existing)
        return existing, tid

    def get(self, worker_id: str) -> WorkerLeaseRow | None:
        return self.session.get(WorkerLeaseRow, worker_id)

    def list_by_project(self, project_id: str) -> list[WorkerLeaseRow]:
        stmt = select(WorkerLeaseRow).where(WorkerLeaseRow.project_id == project_id)
        return list(self.session.scalars(stmt))

    def rotate_membership_token(
        self,
        *,
        worker_id: str,
        current_token: str,
        new_token: str,
    ) -> tuple[WorkerLeaseRow, str]:
        """Rotate membership credential: increment generation; invalidate prior token."""
        row = self.session.get(WorkerLeaseRow, worker_id)
        if row is None:
            raise WorkerNotEligibleError("worker_not_found")
        if row.revoked_at is not None:
            raise WorkerNotEligibleError("worker_revoked")
        if not row.token_hash or not verify_membership_token(
            token=current_token, token_hash=row.token_hash
        ):
            raise WorkerNotEligibleError("invalid_membership_token")
        if any(k in new_token.lower() for k in ("sk-", "api_key", "secret=")):
            raise WorkerNotEligibleError("provider_secret_forbidden_on_worker_token")
        now = utc_now()
        tid = new_token_id()
        row.token_hash = hash_membership_token(new_token)
        row.token_id = tid
        row.lease_generation = int(row.lease_generation) + 1
        row.updated_at = now
        self.session.flush()
        self._assert_row_has_no_raw_token(row)
        return row, tid

    def revoke_worker(self, *, worker_id: str) -> WorkerLeaseRow:
        """Revoke worker membership: fence generation and invalidate stored credential."""
        row = self.session.get(WorkerLeaseRow, worker_id)
        if row is None:
            raise WorkerNotEligibleError("worker_not_found")
        now = utc_now()
        row.revoked_at = now
        row.status = "quarantined"
        row.lease_generation = int(row.lease_generation) + 1
        row.token_hash = None
        row.token_id = None
        row.updated_at = now
        self.session.flush()
        return row

    def request_drain(self, *, worker_id: str) -> WorkerLeaseRow:
        """Mark worker draining: no new leases; existing leases may finish (V2A-003c)."""
        row = self.session.get(WorkerLeaseRow, worker_id)
        if row is None:
            raise WorkerNotEligibleError("worker_not_found")
        if row.revoked_at is not None or row.status == "quarantined":
            return row
        now = utc_now()
        row.status = "draining"
        row.drain_requested_at = now
        row.updated_at = now
        self.session.flush()
        return row

    def record_heartbeat(
        self,
        *,
        worker_id: str,
        membership_token: str,
        generation: int,
        worker_state: str | None = None,
        active_lease_ids: list[str] | None = None,
        available: dict[str, Any] | None = None,
        health: dict[str, Any] | None = None,
        observed_at: datetime | None = None,
    ) -> WorkerLeaseRow:
        """Record worker-side heartbeat (distinct from coordination heartbeat)."""
        row = self.session.get(WorkerLeaseRow, worker_id)
        if row is None:
            raise WorkerNotEligibleError("worker_not_found")
        if row.revoked_at is not None:
            raise WorkerNotEligibleError("worker_revoked")
        if not row.token_hash or not verify_membership_token(
            token=membership_token, token_hash=row.token_hash
        ):
            raise WorkerNotEligibleError("invalid_membership_token")
        if int(row.lease_generation) != int(generation):
            raise WorkerNotEligibleError("worker_generation_mismatch")
        if row.status == "quarantined":
            raise WorkerNotEligibleError("worker_status:quarantined")
        clock = observed_at or utc_now()
        row.heartbeat_at = clock
        row.updated_at = clock
        if worker_state in {"active", "draining", "offline"}:
            # Worker may request drain via heartbeat; cannot self-clear quarantine/revoke.
            if worker_state == "draining" and row.status == "online":
                row.status = "draining"
                row.drain_requested_at = clock
            elif worker_state == "offline" and row.status == "draining":
                # Offline only after drain when no active work — caller enforces.
                row.status = "offline"
            elif worker_state == "active" and row.status == "offline":
                row.status = "online"
        payload = dict(row.resource_payload or {})
        progress: dict[str, Any] = dict(payload.get("last_heartbeat_progress") or {})
        if active_lease_ids is not None:
            progress["active_lease_ids"] = list(active_lease_ids)
        if available is not None:
            progress["available"] = dict(available)
        if health is not None:
            progress["health"] = dict(health)
        progress["observed_at"] = clock.isoformat()
        payload["last_heartbeat_progress"] = progress
        _assert_no_raw_token_fields(payload)
        row.resource_payload = payload
        self.session.flush()
        return row

    def advertise_capabilities(
        self,
        *,
        worker_id: str,
        membership_token: str,
        generation: int,
        capabilities: list[Any] | None = None,
        capacity_units: float | None = None,
        privacy_classes: list[Any] | None = None,
    ) -> WorkerLeaseRow:
        """Voluntary capability/capacity reduction only (ART-V15: no self-expansion)."""
        row = self.session.get(WorkerLeaseRow, worker_id)
        if row is None:
            raise WorkerNotEligibleError("worker_not_found")
        if row.revoked_at is not None:
            raise WorkerNotEligibleError("worker_revoked")
        if not row.token_hash or not verify_membership_token(
            token=membership_token, token_hash=row.token_hash
        ):
            raise WorkerNotEligibleError("invalid_membership_token")
        if int(row.lease_generation) != int(generation):
            raise WorkerNotEligibleError("worker_generation_mismatch")
        current_caps = set(str(c) for c in (row.capabilities or []))
        if capabilities is not None:
            requested = set(str(c) for c in capabilities)
            if not requested.issubset(current_caps):
                raise WorkerNotEligibleError("capability_expansion_forbidden")
            row.capabilities = sorted(requested)
        if capacity_units is not None:
            if float(capacity_units) > float(row.capacity_units):
                raise WorkerNotEligibleError("capacity_expansion_forbidden")
            row.capacity_units = float(capacity_units)
        if privacy_classes is not None:
            current_privacy = set(str(p) for p in (row.privacy_classes or []))
            requested_privacy = set(str(p) for p in privacy_classes)
            if not requested_privacy.issubset(current_privacy):
                raise WorkerNotEligibleError("privacy_expansion_forbidden")
            row.privacy_classes = sorted(requested_privacy)
        row.updated_at = utc_now()
        self.session.flush()
        return row

    def verify_membership(self, *, worker_id: str, membership_token: str) -> bool:
        """Return True only when the worker is not revoked and token matches durable hash."""
        row = self.session.get(WorkerLeaseRow, worker_id)
        if row is None or row.revoked_at is not None or not row.token_hash:
            return False
        return verify_membership_token(token=membership_token, token_hash=row.token_hash)

    @staticmethod
    def _assert_row_has_no_raw_token(row: WorkerLeaseRow) -> None:
        raw = row.__dict__
        for key in _FORBIDDEN_RAW_KEYS:
            if key in raw and raw[key] is not None:
                raise RawTokenPersistenceError(f"raw_token_column_present:{key}")
        # Defensive: token_hash must not equal the plaintext-looking prefix.
        if row.token_hash and row.token_hash.startswith("wt_"):
            raise RawTokenPersistenceError("token_hash_looks_like_raw_token")


class TaskAttemptRepository:
    """Extend existing task_attempts rows with fencing metadata."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def insert(
        self,
        *,
        task_id: str,
        agent_profile_id: str,
        status: str,
        started_at: datetime | None = None,
        project_id: str | None = None,
        mission_id: str | None = None,
        worker_id: str | None = None,
        lease_generation: int = 0,
        task_revision: int = 1,
        input_digest: str | None = None,
        source_revision: str | None = None,
        cancellation_generation: int = 0,
        selected_route_id: str | None = None,
        payload: dict[str, Any] | None = None,
        attempt_id: str | None = None,
    ) -> TaskAttemptRow:
        row = TaskAttemptRow(
            attempt_id=attempt_id or new_id("att_"),
            task_id=task_id,
            project_id=project_id,
            mission_id=mission_id,
            agent_profile_id=agent_profile_id,
            selected_route_id=selected_route_id,
            worker_id=worker_id,
            lease_generation=lease_generation,
            task_revision=task_revision,
            input_digest=input_digest,
            source_revision=source_revision,
            cancellation_generation=cancellation_generation,
            status=status,
            started_at=started_at or utc_now(),
            payload=dict(payload or {}),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, attempt_id: str) -> TaskAttemptRow | None:
        return self.session.get(TaskAttemptRow, attempt_id)


class TaskLeaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def insert(
        self,
        *,
        attempt_id: str,
        task_id: str,
        mission_id: str,
        project_id: str,
        worker_id: str,
        worker_generation: int,
        expires_at: datetime,
        state: str = "active",
        task_revision: int = 1,
        input_digest: str | None = None,
        source_revision: str | None = None,
        cancellation_generation: int = 0,
        issued_at: datetime | None = None,
        renewable_until: datetime | None = None,
        reservation_refs: list[Any] | None = None,
        effect_scope: str | None = None,
        policy_version: str | None = None,
        lease_id: str | None = None,
    ) -> TaskLeaseRow:
        row = TaskLeaseRow(
            lease_id=lease_id or new_id("tls_"),
            attempt_id=attempt_id,
            task_id=task_id,
            mission_id=mission_id,
            project_id=project_id,
            worker_id=worker_id,
            worker_generation=worker_generation,
            task_revision=task_revision,
            input_digest=input_digest,
            source_revision=source_revision,
            cancellation_generation=cancellation_generation,
            state=state,
            issued_at=issued_at or utc_now(),
            expires_at=expires_at,
            renewable_until=renewable_until,
            reservation_refs=list(reservation_refs or []),
            effect_scope=effect_scope,
            policy_version=policy_version,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, lease_id: str) -> TaskLeaseRow | None:
        return self.session.get(TaskLeaseRow, lease_id)

    def list_active_for_attempt(self, attempt_id: str) -> list[TaskLeaseRow]:
        stmt = select(TaskLeaseRow).where(
            TaskLeaseRow.attempt_id == attempt_id,
            TaskLeaseRow.state.in_(("active", "renewed")),
        )
        return list(self.session.scalars(stmt))

    def list_active_for_worker(self, worker_id: str) -> list[TaskLeaseRow]:
        stmt = (
            select(TaskLeaseRow)
            .where(
                TaskLeaseRow.worker_id == worker_id,
                TaskLeaseRow.state.in_(("active", "renewed")),
            )
            .order_by(TaskLeaseRow.issued_at.asc(), TaskLeaseRow.lease_id.asc())
        )
        return list(self.session.scalars(stmt))

    def list_active_for_mission(self, mission_id: str) -> list[TaskLeaseRow]:
        stmt = (
            select(TaskLeaseRow)
            .where(
                TaskLeaseRow.mission_id == mission_id,
                TaskLeaseRow.state.in_(tuple(_ACTIVE_LEASE_STATES)),
            )
            .order_by(TaskLeaseRow.lease_id.asc())
        )
        return list(self.session.scalars(stmt))


class WorkerResultRepository:

    def __init__(self, session: Session) -> None:
        self.session = session

    def insert(
        self,
        *,
        attempt_id: str,
        lease_id: str,
        task_id: str,
        mission_id: str,
        project_id: str,
        worker_id: str,
        worker_generation: int,
        result_status: str,
        task_revision: int = 1,
        input_digest: str | None = None,
        source_revision: str | None = None,
        artifact_manifest: dict[str, Any] | None = None,
        checks: dict[str, Any] | None = None,
        usage: dict[str, Any] | None = None,
        effect_receipts: list[Any] | None = None,
        acceptance_state: str = "submitted",
        submitted_at: datetime | None = None,
        result_id: str | None = None,
    ) -> WorkerResultRow:
        row = WorkerResultRow(
            result_id=result_id or new_id("wres_"),
            attempt_id=attempt_id,
            lease_id=lease_id,
            task_id=task_id,
            mission_id=mission_id,
            project_id=project_id,
            worker_id=worker_id,
            worker_generation=worker_generation,
            task_revision=task_revision,
            input_digest=input_digest,
            source_revision=source_revision,
            result_status=result_status,
            artifact_manifest=dict(artifact_manifest or {}),
            checks=dict(checks or {}),
            usage=dict(usage or {}),
            effect_receipts=list(effect_receipts or []),
            submitted_at=submitted_at or utc_now(),
            acceptance_state=acceptance_state,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, result_id: str) -> WorkerResultRow | None:
        return self.session.get(WorkerResultRow, result_id)

    def list_for_attempt(self, attempt_id: str) -> list[WorkerResultRow]:
        stmt = (
            select(WorkerResultRow)
            .where(WorkerResultRow.attempt_id == attempt_id)
            .order_by(WorkerResultRow.submitted_at.asc(), WorkerResultRow.result_id.asc())
        )
        return list(self.session.scalars(stmt))

    def get_accepted_for_attempt(self, attempt_id: str) -> WorkerResultRow | None:
        stmt = (
            select(WorkerResultRow)
            .where(
                WorkerResultRow.attempt_id == attempt_id,
                WorkerResultRow.acceptance_state == "accepted",
            )
            .limit(1)
        )
        return self.session.scalar(stmt)


class LeaseClaimError(ValueError):
    """Base error for claim/renew/expire fencing failures."""


class WorkerNotEligibleError(LeaseClaimError):
    """Worker token/generation/status cannot claim or renew."""


class LeaseRenewError(LeaseClaimError):
    """Lease cannot be renewed (expired, wrong generation, past renewable_until)."""


class ResultAcceptanceError(LeaseClaimError):
    """Result cannot be accepted under the durable fencing policy (V2A-003c)."""


@dataclass(frozen=True)
class ClaimedLease:
    """Outcome of an atomic eligible-task claim."""

    task_id: str
    attempt_id: str
    lease_id: str
    mission_id: str
    project_id: str
    worker_id: str
    worker_generation: int
    task_revision: int
    expires_at: datetime
    state: str


@dataclass(frozen=True)
class MissionCancellation:
    """Outcome of a durable mission cancellation-generation bump (MISSION-CANCEL-01)."""

    mission_id: str
    previous_generation: int
    new_generation: int
    terminal: bool
    notified_lease_ids: tuple[str, ...]


@dataclass(frozen=True)
class AcceptedResult:
    """Outcome of a successful V2A-003c acceptance transaction."""

    result_id: str
    attempt_id: str
    lease_id: str
    task_id: str
    mission_id: str
    project_id: str
    acceptance_state: str
    accepted_at: datetime


class LeaseLifecycleService:
    """V2A-003b/R atomic claim / renew / expire (+ V2A-H3 eligible skip).

    Fairness: claim candidates are ordered by ``(priority ASC, created_at ASC, id ASC)``.
    Incompatible or authority-stale locked rows are left unmutated so other workers
    may claim them; the claimer paginates until an eligible row is found or the
    eligible set is exhausted (no fixed 32-row correctness ceiling).
    """

    def __init__(
        self,
        session: Session,
        *,
        default_lease_seconds: int = _DEFAULT_LEASE_SECONDS,
        renewable_horizon_seconds: int = _DEFAULT_RENEWABLE_HORIZON_SECONDS,
        candidate_page_size: int = _CLAIM_CANDIDATE_PAGE,
    ) -> None:
        self.session = session
        self.default_lease_seconds = default_lease_seconds
        self.renewable_horizon_seconds = renewable_horizon_seconds
        self.candidate_page_size = max(1, candidate_page_size)
        self._attempts = TaskAttemptRepository(session)
        self._leases = TaskLeaseRepository(session)
        self._workers = WorkerRegistrationRepository(session)
        self._results = WorkerResultRepository(session)

    def claim_eligible_attempt(
        self,
        *,
        worker_id: str,
        membership_token: str,
        agent_profile_id: str = "ap_default",
        now: datetime | None = None,
        lease_seconds: int | None = None,
    ) -> ClaimedLease | None:
        """Atomically claim one eligible ready task for the worker.

        Uses ``SELECT … FOR UPDATE SKIP LOCKED`` with keyset pagination until an
        eligible authoritative task is found or the set is exhausted. Returns
        ``None`` without mutating queue/task state when nothing is claimable.
        """
        clock = now or utc_now()
        worker = self._require_claimable_worker(worker_id, membership_token)
        project_id = worker.project_id
        if not project_id:
            raise WorkerNotEligibleError("worker_missing_project_id")

        after: tuple[int, datetime, str] | None = None
        while True:
            candidates = self._lock_ready_candidates(
                project_id=project_id,
                limit=self.candidate_page_size,
                after=after,
            )
            if not candidates:
                return None
            for task in candidates:
                after = (task.priority, task.created_at, task.id)
                if not self._worker_eligible_for_task(worker, task):
                    # V2A-H3: leave incompatible head locked-unmutated; keep scanning.
                    continue
                if self._has_active_lease(task.id):
                    continue
                if not self._dependencies_satisfied(task):
                    # Stale/unresolved deps — leave task unmutated; continue scan.
                    continue
                mission = self._load_claimable_mission(task)
                if mission is None:
                    # Authority stale/cancelled/missing — leave task unmutated.
                    continue
                return self._bind_claim(
                    worker=worker,
                    task=task,
                    mission=mission,
                    agent_profile_id=agent_profile_id,
                    clock=clock,
                    lease_seconds=lease_seconds or self.default_lease_seconds,
                )
            if len(candidates) < self.candidate_page_size:
                return None

    def renew_lease(
        self,
        *,
        lease_id: str,
        worker_id: str,
        worker_generation: int,
        membership_token: str,
        extend_seconds: int | None = None,
        now: datetime | None = None,
    ) -> TaskLeaseRow:
        """Extend an active/renewed lease when worker, project, authority, and window match."""
        clock = now or utc_now()
        worker = self._require_claimable_worker(worker_id, membership_token)
        lease = self.session.get(TaskLeaseRow, lease_id)
        if lease is None:
            raise LeaseRenewError("lease_not_found")
        if lease.worker_id != worker_id:
            raise LeaseRenewError("lease_worker_mismatch")
        if worker.project_id != lease.project_id:
            raise LeaseRenewError("lease_project_mismatch")
        if lease.worker_generation != worker_generation:
            raise LeaseRenewError("lease_generation_mismatch")
        if worker.lease_generation != worker_generation:
            raise LeaseRenewError("worker_generation_mismatch")
        if lease.state not in _ACTIVE_LEASE_STATES:
            raise LeaseRenewError(f"lease_not_renewable:{lease.state}")
        if lease.expires_at <= clock:
            raise LeaseRenewError("lease_already_expired")
        self._require_current_lease_authority(lease)
        lease.expires_at = self._renewal_expires_at(
            lease=lease,
            clock=clock,
            extend_seconds=extend_seconds or self.default_lease_seconds,
        )
        lease.state = "renewed"
        lease.updated_at = clock
        self.session.flush()
        return lease

    def expire_leases(
        self,
        *,
        now: datetime | None = None,
        project_id: str | None = None,
        limit: int = 100,
    ) -> list[str]:
        """Expire active leases whose ``expires_at`` has passed (server clock).

        Returns expired lease IDs. Tasks still marked ``leased`` return to
        ``ready`` only when mission/task authority is still current; otherwise
        they are reconciled to a non-dispatchable cancelled/superseded status.
        """
        clock = now or utc_now()
        stmt = (
            select(TaskLeaseRow)
            .where(
                TaskLeaseRow.state.in_(tuple(_ACTIVE_LEASE_STATES)),
                TaskLeaseRow.expires_at <= clock,
            )
            .order_by(TaskLeaseRow.expires_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        if project_id is not None:
            stmt = stmt.where(TaskLeaseRow.project_id == project_id)
        expired_ids: list[str] = []
        for lease in self.session.scalars(stmt):
            lease.state = "expired"
            lease.updated_at = clock
            attempt = self.session.get(TaskAttemptRow, lease.attempt_id)
            if attempt is not None and attempt.status in {"leased", "running", "pending"}:
                attempt.status = "expired"
                attempt.terminal_at = clock
            task = self.session.get(TaskRow, lease.task_id)
            if task is not None and task.status == "leased":
                task.status = self._expire_task_status(task, lease=lease, attempt=attempt)
            expired_ids.append(lease.lease_id)
        self.session.flush()
        return expired_ids

    def get_lease(self, lease_id: str) -> TaskLeaseRow | None:
        return self.session.get(TaskLeaseRow, lease_id)

    def list_active_leases_for_worker(self, worker_id: str) -> list[TaskLeaseRow]:
        return self._leases.list_active_for_worker(worker_id)

    def get_result(self, result_id: str) -> WorkerResultRow | None:
        return self._results.get(result_id)

    def _require_claimable_worker(self, worker_id: str, membership_token: str) -> WorkerLeaseRow:
        worker = self._workers.get(worker_id)
        if worker is None:
            raise WorkerNotEligibleError("worker_not_found")
        if worker.revoked_at is not None:
            raise WorkerNotEligibleError("worker_revoked")
        if worker.status in {"draining", "offline", "quarantined"}:
            raise WorkerNotEligibleError(f"worker_status:{worker.status}")
        if not worker.token_hash or not verify_membership_token(
            token=membership_token, token_hash=worker.token_hash
        ):
            raise WorkerNotEligibleError("invalid_membership_token")
        return worker

    def _lock_ready_candidates(
        self,
        *,
        project_id: str,
        limit: int,
        after: tuple[int, datetime, str] | None = None,
    ) -> list[TaskRow]:
        stmt = (
            select(TaskRow)
            .where(
                TaskRow.project_id == project_id,
                TaskRow.status == _CLAIMABLE_TASK_STATUS,
            )
            .order_by(TaskRow.priority.asc(), TaskRow.created_at.asc(), TaskRow.id.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        if after is not None:
            priority, created_at, task_id = after
            stmt = stmt.where(
                tuple_(TaskRow.priority, TaskRow.created_at, TaskRow.id)
                > tuple_(literal(priority), literal(created_at), literal(task_id))
            )
        return list(self.session.scalars(stmt))

    def _load_claimable_mission(self, task: TaskRow) -> MissionRow | None:
        """Return mission when task/mission/project/graph/source/cancel authority is current.

        On any failure returns None and must not mutate the task row.
        """
        mission = self.session.get(MissionRow, task.mission_id)
        if mission is None:
            return None
        if mission.status not in _RUNNABLE_MISSION_STATUSES:
            return None
        if mission.status == "cancelled" or mission.cancellation_generation < 0:
            return None
        if task.project_id != mission.project_id:
            return None
        if task.graph_revision != mission.revision:
            return None
        payload = task.payload if isinstance(task.payload, dict) else {}
        task_cancel = payload.get("cancellation_generation")
        if task_cancel is not None and int(task_cancel) != int(mission.cancellation_generation):
            return None
        current_source = self._mission_source_revision(mission)
        task_source = payload.get("source_revision")
        if task_source is not None and str(task_source) != current_source:
            return None
        return mission

    def _require_current_lease_authority(self, lease: TaskLeaseRow) -> None:
        """Fail renew when task/mission/attempt authority drifted after claim."""
        task = self.session.get(TaskRow, lease.task_id)
        if task is None:
            raise LeaseRenewError("task_missing")
        if task.status in _TERMINAL_TASK_STATUSES:
            raise LeaseRenewError(f"task_terminal:{task.status}")
        if task.project_id != lease.project_id:
            raise LeaseRenewError("task_project_mismatch")
        if lease.task_revision is not None and int(task.graph_revision) != int(lease.task_revision):
            raise LeaseRenewError("task_revision_mismatch")
        attempt = self.session.get(TaskAttemptRow, lease.attempt_id)
        if attempt is None:
            raise LeaseRenewError("attempt_missing")
        if attempt.task_id != lease.task_id or attempt.mission_id != lease.mission_id:
            raise LeaseRenewError("attempt_lease_mismatch")
        if attempt.project_id is not None and attempt.project_id != lease.project_id:
            raise LeaseRenewError("attempt_project_mismatch")
        if attempt.status in _TERMINAL_ATTEMPT_STATUSES:
            raise LeaseRenewError(f"attempt_terminal:{attempt.status}")
        if attempt.terminal_at is not None:
            raise LeaseRenewError("attempt_terminal_at_set")
        if attempt.completed_at is not None:
            raise LeaseRenewError("attempt_completed")
        if attempt.accepted_result_id:
            raise LeaseRenewError("attempt_accepted_result")
        mission = self._load_claimable_mission(task)
        if mission is None:
            raise LeaseRenewError("authority_stale")
        current_source = self._mission_source_revision(mission)
        if lease.source_revision is not None and str(lease.source_revision) != current_source:
            raise LeaseRenewError("source_revision_stale")
        if (
            lease.cancellation_generation is not None
            and int(lease.cancellation_generation) != int(mission.cancellation_generation)
        ):
            raise LeaseRenewError("cancellation_generation_stale")
        if attempt.source_revision is not None and str(attempt.source_revision) != current_source:
            raise LeaseRenewError("attempt_source_stale")
        if (
            attempt.cancellation_generation is not None
            and int(attempt.cancellation_generation) != int(mission.cancellation_generation)
        ):
            raise LeaseRenewError("attempt_cancellation_stale")
        if int(attempt.task_revision) != int(mission.revision):
            raise LeaseRenewError("attempt_revision_stale")

    @staticmethod
    def _renewal_expires_at(
        *,
        lease: TaskLeaseRow,
        clock: datetime,
        extend_seconds: int,
    ) -> datetime:
        """Compute renew expiry with ``renewable_until`` as a hard upper bound."""
        desired = clock + timedelta(seconds=extend_seconds)
        upper = lease.renewable_until
        if upper is None:
            return desired
        if clock >= upper:
            raise LeaseRenewError("past_renewable_until")
        capped = min(desired, upper)
        if capped <= clock:
            raise LeaseRenewError("no_positive_renewal_window")
        # Already at the horizon: cannot grant additional time.
        if lease.expires_at >= upper:
            raise LeaseRenewError("no_positive_renewal_window")
        # Never accidentally shorten a currently later valid expiry.
        if capped < lease.expires_at:
            return lease.expires_at
        return capped

    def _expire_task_status(
        self,
        task: TaskRow,
        *,
        lease: TaskLeaseRow,
        attempt: TaskAttemptRow | None,
    ) -> str:
        """Return ready only when lease/attempt/task authority is still current.

        Compares lease/attempt stored revision/source/cancellation stamps to the
        current durable mission authority so source drift is caught even when
        TaskRow payload lacks the original source marker (V2A-003b-R2).
        """
        mission = self.session.get(MissionRow, task.mission_id)
        if mission is None or mission.status == "cancelled":
            return _CANCELLED_ON_EXPIRE
        if mission.status not in _RUNNABLE_MISSION_STATUSES:
            return _CANCELLED_ON_EXPIRE
        current_source = self._mission_source_revision(mission)
        if self._lease_stamp_authority_stale(
            lease=lease,
            attempt=attempt,
            task=task,
            mission=mission,
            current_source=current_source,
        ):
            return _NON_DISPATCHABLE_ON_STALE_EXPIRE
        if self._load_claimable_mission(task) is None:
            return _NON_DISPATCHABLE_ON_STALE_EXPIRE
        return _CLAIMABLE_TASK_STATUS

    @staticmethod
    def _lease_stamp_authority_stale(
        *,
        lease: TaskLeaseRow,
        attempt: TaskAttemptRow | None,
        task: TaskRow,
        mission: MissionRow,
        current_source: str,
    ) -> bool:
        """True when lease/attempt stamps disagree with current durable authority."""
        if int(task.graph_revision) != int(mission.revision):
            return True
        if lease.task_revision is not None and int(lease.task_revision) != int(mission.revision):
            return True
        if lease.source_revision is not None and str(lease.source_revision) != current_source:
            return True
        if int(lease.cancellation_generation) != int(mission.cancellation_generation):
            return True
        if attempt is None:
            return False
        if int(attempt.task_revision) != int(mission.revision):
            return True
        if attempt.source_revision is not None and str(attempt.source_revision) != current_source:
            return True
        if int(attempt.cancellation_generation) != int(mission.cancellation_generation):
            return True
        return False

    def _dependencies_satisfied(self, task: TaskRow) -> bool:
        """True when every dependency is accepted/completed for same mission/project/graph."""
        deps = list(task.dependency_ids or [])
        if not deps:
            return True
        for dep_id in deps:
            dep = self.session.get(TaskRow, str(dep_id))
            if dep is None:
                return False
            if dep.mission_id != task.mission_id or dep.project_id != task.project_id:
                return False
            if int(dep.graph_revision) != int(task.graph_revision):
                return False
            if dep.status not in _DEPENDENCY_DONE_STATUSES:
                return False
        return True

    @staticmethod
    def _mission_source_revision(mission: MissionRow) -> str:
        payload = mission.payload if isinstance(mission.payload, dict) else {}
        explicit = payload.get("source_revision")
        if isinstance(explicit, str) and explicit:
            return explicit
        return f"msnrev:{mission.revision}"

    @staticmethod
    def _worker_eligible_for_task(worker: WorkerLeaseRow, task: TaskRow) -> bool:
        payload = task.payload if isinstance(task.payload, dict) else {}
        required = set(payload.get("required_capabilities") or [])
        have = set(worker.capabilities or [])
        if required and not required.issubset(have):
            return False
        scopes = set(task.scopes or [])
        privacy = set(worker.privacy_classes or [])
        if "local_only" in scopes and "local" not in privacy:
            return False
        return True

    def _has_active_lease(self, task_id: str) -> bool:
        stmt = (
            select(TaskLeaseRow.lease_id)
            .where(
                TaskLeaseRow.task_id == task_id,
                TaskLeaseRow.state.in_(tuple(_ACTIVE_LEASE_STATES)),
            )
            .limit(1)
        )
        return self.session.scalar(stmt) is not None

    def _bind_claim(
        self,
        *,
        worker: WorkerLeaseRow,
        task: TaskRow,
        mission: MissionRow,
        agent_profile_id: str,
        clock: datetime,
        lease_seconds: int,
    ) -> ClaimedLease:
        assert worker.project_id is not None
        if worker.project_id != mission.project_id or worker.project_id != task.project_id:
            raise LeaseClaimError("claim_project_mismatch")
        expires_at = clock + timedelta(seconds=lease_seconds)
        renewable_until = clock + timedelta(seconds=self.renewable_horizon_seconds)
        if expires_at > renewable_until:
            expires_at = renewable_until
        payload = task.payload if isinstance(task.payload, dict) else {}
        input_digest = payload.get("input_digest") if isinstance(payload, dict) else None
        source_revision = self._mission_source_revision(mission)
        cancel_gen = int(mission.cancellation_generation)
        attempt = self._attempts.insert(
            task_id=task.id,
            agent_profile_id=agent_profile_id,
            status="leased",
            started_at=clock,
            project_id=worker.project_id,
            mission_id=task.mission_id,
            worker_id=worker.worker_id,
            lease_generation=worker.lease_generation,
            task_revision=task.graph_revision,
            input_digest=input_digest if isinstance(input_digest, str) else None,
            source_revision=source_revision,
            cancellation_generation=cancel_gen,
        )
        lease = self._leases.insert(
            attempt_id=attempt.attempt_id,
            task_id=task.id,
            mission_id=task.mission_id,
            project_id=worker.project_id,
            worker_id=worker.worker_id,
            worker_generation=worker.lease_generation,
            expires_at=expires_at,
            state="active",
            task_revision=task.graph_revision,
            input_digest=attempt.input_digest,
            source_revision=attempt.source_revision,
            cancellation_generation=cancel_gen,
            issued_at=clock,
            renewable_until=renewable_until,
            policy_version=worker.policy_version,
        )
        task.status = "leased"
        self.session.add(
            OutboxRow(
                id=new_id("ob_"),
                stable_workflow_id=f"attempt:{attempt.attempt_id}",
                aggregate_type="task_attempt",
                aggregate_id=attempt.attempt_id,
                event_type="task_lease.claimed",
                payload={
                    "task_id": task.id,
                    "lease_id": lease.lease_id,
                    "worker_id": worker.worker_id,
                    "worker_generation": worker.lease_generation,
                },
                status="pending",
            )
        )
        self.session.flush()
        return ClaimedLease(
            task_id=task.id,
            attempt_id=attempt.attempt_id,
            lease_id=lease.lease_id,
            mission_id=task.mission_id,
            project_id=worker.project_id,
            worker_id=worker.worker_id,
            worker_generation=worker.lease_generation,
            task_revision=task.graph_revision,
            expires_at=expires_at,
            state=lease.state,
        )

    def submit_result(
        self,
        *,
        lease_id: str,
        worker_id: str,
        membership_token: str,
        worker_generation: int,
        result_status: str,
        artifact_manifest: dict[str, Any] | None = None,
        checks: dict[str, Any] | None = None,
        usage: dict[str, Any] | None = None,
        effect_receipts: list[Any] | None = None,
        now: datetime | None = None,
        result_id: str | None = None,
    ) -> WorkerResultRow:
        """Persist an immutable worker result for audit (V2A-003c).

        Submission does not imply acceptance. Late/stale/expired results remain
        durable non-accepted records when the accept fence rejects them.
        """
        clock = now or utc_now()
        worker = self._require_authenticated_worker(worker_id, membership_token)
        lease = self.session.get(TaskLeaseRow, lease_id, with_for_update=True)
        if lease is None:
            raise ResultAcceptanceError("lease_not_found")
        if lease.worker_id != worker_id:
            raise ResultAcceptanceError("lease_worker_mismatch")
        if worker.project_id != lease.project_id:
            raise ResultAcceptanceError("lease_project_mismatch")
        if int(lease.worker_generation) != int(worker_generation):
            raise ResultAcceptanceError("lease_generation_mismatch")
        attempt = self.session.get(TaskAttemptRow, lease.attempt_id, with_for_update=True)
        if attempt is None:
            raise ResultAcceptanceError("attempt_missing")
        row = self._results.insert(
            result_id=result_id,
            attempt_id=attempt.attempt_id,
            lease_id=lease.lease_id,
            task_id=lease.task_id,
            mission_id=lease.mission_id,
            project_id=lease.project_id,
            worker_id=worker_id,
            worker_generation=worker_generation,
            result_status=result_status,
            task_revision=int(lease.task_revision),
            input_digest=lease.input_digest,
            source_revision=lease.source_revision,
            artifact_manifest=artifact_manifest,
            checks=checks,
            usage=usage,
            effect_receipts=effect_receipts,
            acceptance_state="submitted",
            submitted_at=clock,
        )
        self.session.add(
            OutboxRow(
                id=new_id("ob_"),
                stable_workflow_id=f"result:{row.result_id}",
                aggregate_type="worker_result",
                aggregate_id=row.result_id,
                event_type="worker_result.submitted",
                payload={
                    "result_id": row.result_id,
                    "attempt_id": attempt.attempt_id,
                    "lease_id": lease.lease_id,
                    "worker_id": worker_id,
                    "worker_generation": worker_generation,
                },
                status="pending",
            )
        )
        self.session.flush()
        return row

    def accept_result(
        self,
        *,
        result_id: str,
        now: datetime | None = None,
    ) -> AcceptedResult:
        """Atomically accept one durable result under the V2A-003c fencing policy.

        Idempotent for an already-accepted ``result_id``. Concurrent/conflicting
        submissions remain durable with non-accepted acceptance_state.
        """
        clock = now or utc_now()
        result = self.session.get(WorkerResultRow, result_id, with_for_update=True)
        if result is None:
            raise ResultAcceptanceError("result_not_found")
        if result.acceptance_state == "accepted":
            assert result.accepted_at is not None
            return AcceptedResult(
                result_id=result.result_id,
                attempt_id=result.attempt_id,
                lease_id=result.lease_id,
                task_id=result.task_id,
                mission_id=result.mission_id,
                project_id=result.project_id,
                acceptance_state=result.acceptance_state,
                accepted_at=result.accepted_at,
            )
        if result.acceptance_state in {"rejected", "superseded"}:
            raise ResultAcceptanceError(f"result_terminal:{result.acceptance_state}")

        lease = self.session.get(TaskLeaseRow, result.lease_id, with_for_update=True)
        attempt = self.session.get(TaskAttemptRow, result.attempt_id, with_for_update=True)
        task = self.session.get(TaskRow, result.task_id, with_for_update=True)
        if lease is None or attempt is None or task is None:
            self._mark_rejected(result, reason="missing_fence_rows", clock=clock)
            raise ResultAcceptanceError("missing_fence_rows")

        try:
            self._assert_accept_fence(
                result=result, lease=lease, attempt=attempt, task=task, clock=clock
            )
        except ResultAcceptanceError as exc:
            self._mark_rejected(result, reason=str(exc), clock=clock)
            raise

        result.acceptance_state = "accepted"
        result.accepted_at = clock
        result.rejection_reason = None
        attempt.status = "accepted"
        attempt.accepted_result_id = result.result_id
        attempt.completed_at = clock
        attempt.terminal_at = clock
        if lease.state in _ACTIVE_LEASE_STATES:
            lease.state = "released"
            lease.updated_at = clock
        if task.status not in _TERMINAL_TASK_STATUSES:
            task.status = "accepted"
        self.session.add(
            OutboxRow(
                id=new_id("ob_"),
                stable_workflow_id=f"result-accept:{result.result_id}",
                aggregate_type="worker_result",
                aggregate_id=result.result_id,
                event_type="worker_result.accepted",
                payload={
                    "result_id": result.result_id,
                    "attempt_id": attempt.attempt_id,
                    "lease_id": lease.lease_id,
                    "task_id": task.id,
                },
                status="pending",
            )
        )
        self.session.flush()
        return AcceptedResult(
            result_id=result.result_id,
            attempt_id=result.attempt_id,
            lease_id=result.lease_id,
            task_id=result.task_id,
            mission_id=result.mission_id,
            project_id=result.project_id,
            acceptance_state=result.acceptance_state,
            accepted_at=clock,
        )

    def revoke_mission_work(
        self,
        *,
        mission_id: str,
        reason: str = "revoked",
        notify_leases: bool = True,
        now: datetime | None = None,
    ) -> MissionCancellation:
        """Durable cancellation authority (ART-V15-WORKER-PROTOCOL).

        Increments the mission's ``cancellation_generation`` under a row lock so every
        in-flight lease, result and renewal carrying the old generation is fenced
        (``cancellation_generation_stale``) even if no worker is ever notified. The
        mission itself stays runnable: cancelled attempts return their task to
        ``ready`` and a fresh claim carries the new generation. Advisory per-lease
        cancellation (worker notification) follows the durable bump and can be skipped
        with ``notify_leases=False``; a lost notification never weakens the fence.
        """
        clock = now or utc_now()
        mission = self.session.get(MissionRow, mission_id, with_for_update=True)
        if mission is None:
            raise ResultAcceptanceError("mission_missing")
        previous = int(mission.cancellation_generation)
        mission.cancellation_generation = previous + 1
        self.session.add(
            OutboxRow(
                id=new_id("ob_"),
                stable_workflow_id=f"mission-cancel-gen:{mission_id}:{previous + 1}",
                aggregate_type="mission",
                aggregate_id=mission_id,
                event_type="mission.cancellation_generation_bumped",
                payload={
                    "mission_id": mission_id,
                    "previous_generation": previous,
                    "new_generation": previous + 1,
                    "reason": reason,
                },
                status="pending",
            )
        )
        self.session.flush()
        notified: list[str] = []
        if notify_leases:
            for lease in self._leases.list_active_for_mission(mission_id):
                # "revoked" returns the task to ready so it can be re-claimed under the
                # new generation; "cancelled" makes the task terminal.
                self.cancel_active_lease(lease_id=lease.lease_id, reason=reason, now=clock)
                notified.append(lease.lease_id)
        return MissionCancellation(
            mission_id=mission_id,
            previous_generation=previous,
            new_generation=previous + 1,
            terminal=False,
            notified_lease_ids=tuple(notified),
        )

    def cancel_mission(
        self,
        *,
        mission_id: str,
        reason: str = "cancelled",
        now: datetime | None = None,
    ) -> MissionCancellation:
        """Terminal mission cancellation: durable generation bump, then status ``cancelled``.

        The generation bump happens first so the fence holds even if the status write
        were lost; afterwards accept/renew/claim are denied by ``mission_cancelled`` /
        non-runnable status, and cancelled tasks are terminal.
        """
        clock = now or utc_now()
        outcome = self.revoke_mission_work(
            mission_id=mission_id, reason="cancelled", notify_leases=True, now=clock
        )
        mission = self.session.get(MissionRow, mission_id, with_for_update=True)
        assert mission is not None
        mission.status = "cancelled"
        mission.updated_at = clock
        self.session.flush()
        return MissionCancellation(
            mission_id=mission_id,
            previous_generation=outcome.previous_generation,
            new_generation=outcome.new_generation,
            terminal=True,
            notified_lease_ids=outcome.notified_lease_ids,
        )

    def cancel_active_lease(
        self,
        *,
        lease_id: str,
        reason: str = "cancelled",
        now: datetime | None = None,
    ) -> TaskLeaseRow:
        """Cancel an active lease and fence its attempt (V2A-003c drain/cancel path)."""
        clock = now or utc_now()
        lease = self.session.get(TaskLeaseRow, lease_id, with_for_update=True)
        if lease is None:
            raise ResultAcceptanceError("lease_not_found")
        if lease.state not in _ACTIVE_LEASE_STATES:
            raise ResultAcceptanceError(f"lease_not_active:{lease.state}")
        lease.state = "cancelled"
        lease.updated_at = clock
        attempt = self.session.get(TaskAttemptRow, lease.attempt_id, with_for_update=True)
        if attempt is not None and attempt.accepted_result_id is None:
            if attempt.status not in _TERMINAL_ATTEMPT_STATUSES:
                attempt.status = "cancelled"
                attempt.terminal_at = clock
        task = self.session.get(TaskRow, lease.task_id, with_for_update=True)
        if task is not None and task.status == "leased":
            task.status = "cancelled" if reason == "cancelled" else "ready"
        self.session.add(
            OutboxRow(
                id=new_id("ob_"),
                stable_workflow_id=f"lease-cancel:{lease.lease_id}:{int(clock.timestamp())}",
                aggregate_type="task_lease",
                aggregate_id=lease.lease_id,
                event_type="task_lease.cancelled",
                payload={"lease_id": lease.lease_id, "reason": reason},
                status="pending",
            )
        )
        self.session.flush()
        return lease

    def _require_authenticated_worker(
        self, worker_id: str, membership_token: str
    ) -> WorkerLeaseRow:
        """Authenticate membership without requiring claimable (active) status.

        Drain/offline workers may still submit late results for audit; accept
        fencing decides whether those results can become authoritative.
        """
        worker = self._workers.get(worker_id)
        if worker is None:
            raise WorkerNotEligibleError("worker_not_found")
        if worker.revoked_at is not None:
            raise WorkerNotEligibleError("worker_revoked")
        if worker.status == "quarantined":
            raise WorkerNotEligibleError("worker_status:quarantined")
        if not worker.token_hash or not verify_membership_token(
            token=membership_token, token_hash=worker.token_hash
        ):
            raise WorkerNotEligibleError("invalid_membership_token")
        return worker

    def _assert_accept_fence(
        self,
        *,
        result: WorkerResultRow,
        lease: TaskLeaseRow,
        attempt: TaskAttemptRow,
        task: TaskRow,
        clock: datetime,
    ) -> None:
        if result.project_id != lease.project_id or result.project_id != task.project_id:
            raise ResultAcceptanceError("project_mismatch")
        if result.attempt_id != lease.attempt_id or attempt.attempt_id != lease.attempt_id:
            raise ResultAcceptanceError("attempt_lease_mismatch")
        if result.task_id != lease.task_id or result.mission_id != lease.mission_id:
            raise ResultAcceptanceError("result_task_mismatch")
        if int(result.worker_generation) != int(lease.worker_generation):
            raise ResultAcceptanceError("result_generation_mismatch")
        worker = self._workers.get(result.worker_id)
        if worker is None:
            raise ResultAcceptanceError("worker_not_found")
        if worker.revoked_at is not None:
            raise ResultAcceptanceError("worker_revoked")
        if int(worker.lease_generation) != int(result.worker_generation):
            raise ResultAcceptanceError("worker_generation_stale")
        if worker.project_id != result.project_id:
            raise ResultAcceptanceError("worker_project_mismatch")
        if attempt.accepted_result_id and attempt.accepted_result_id != result.result_id:
            raise ResultAcceptanceError("attempt_already_accepted")
        if lease.state not in _ACTIVE_LEASE_STATES:
            raise ResultAcceptanceError(f"lease_not_current:{lease.state}")
        if lease.expires_at <= clock:
            raise ResultAcceptanceError("lease_expired")
        if attempt.status in _TERMINAL_ATTEMPT_STATUSES and attempt.status != "accepted":
            raise ResultAcceptanceError(f"attempt_terminal:{attempt.status}")
        if task.status in _TERMINAL_TASK_STATUSES and task.status != "accepted":
            raise ResultAcceptanceError(f"task_terminal:{task.status}")
        if int(result.task_revision) != int(lease.task_revision):
            raise ResultAcceptanceError("result_task_revision_mismatch")
        if int(task.graph_revision) != int(lease.task_revision):
            raise ResultAcceptanceError("task_revision_mismatch")
        if result.input_digest != lease.input_digest:
            raise ResultAcceptanceError("input_digest_mismatch")
        if result.source_revision != lease.source_revision:
            raise ResultAcceptanceError("source_revision_mismatch")
        mission = self.session.get(MissionRow, task.mission_id)
        if mission is None:
            raise ResultAcceptanceError("mission_missing")
        if mission.project_id != result.project_id:
            raise ResultAcceptanceError("mission_project_mismatch")
        if mission.status == "cancelled":
            raise ResultAcceptanceError("mission_cancelled")
        if mission.status not in _RUNNABLE_MISSION_STATUSES:
            raise ResultAcceptanceError(f"mission_not_runnable:{mission.status}")
        current_source = self._mission_source_revision(mission)
        if lease.source_revision is not None and str(lease.source_revision) != current_source:
            raise ResultAcceptanceError("source_revision_stale")
        if int(lease.cancellation_generation) != int(mission.cancellation_generation):
            raise ResultAcceptanceError("cancellation_generation_stale")
        payload = task.payload if isinstance(task.payload, dict) else {}
        task_cancel = payload.get("cancellation_generation")
        if task_cancel is not None and int(task_cancel) != int(mission.cancellation_generation):
            raise ResultAcceptanceError("task_cancellation_stale")
        if not self._review_checks_pass(result.checks):
            raise ResultAcceptanceError("review_checks_failed")
        if not self._reservations_reconciled(lease=lease, result=result):
            raise ResultAcceptanceError("reservations_unreconciled")
        # Exactly-one accepted result per attempt (race-safe under row lock).
        existing = self._results.get_accepted_for_attempt(attempt.attempt_id)
        if existing is not None and existing.result_id != result.result_id:
            raise ResultAcceptanceError("duplicate_accepted_result")

    @staticmethod
    def _review_checks_pass(checks: dict[str, Any] | None) -> bool:
        """Deterministic review gate: require explicit pass markers when present."""
        if not checks:
            return False
        if checks.get("review_passed") is True:
            return True
        if checks.get("verification_passed") is True and checks.get("review_passed") is not False:
            return True
        return False

    @staticmethod
    def _reservations_reconciled(*, lease: TaskLeaseRow, result: WorkerResultRow) -> bool:
        """Require listed lease reservation refs to appear in result usage/effects."""
        refs = list(lease.reservation_refs or [])
        if not refs:
            return True
        usage = result.usage if isinstance(result.usage, dict) else {}
        usage_refs = usage.get("reservation_refs") if isinstance(usage, dict) else None
        claimed = set(usage_refs or [])
        for receipt in result.effect_receipts or []:
            if isinstance(receipt, dict) and receipt.get("reservation_ref"):
                claimed.add(str(receipt["reservation_ref"]))
        return set(str(r) for r in refs).issubset(claimed)

    @staticmethod
    def _mark_rejected(result: WorkerResultRow, *, reason: str, clock: datetime) -> None:
        if result.acceptance_state == "accepted":
            return
        result.acceptance_state = "rejected"
        result.rejection_reason = reason[:512]
        result.accepted_at = None
        # Keep submitted_at; rejection is a disposition only.
