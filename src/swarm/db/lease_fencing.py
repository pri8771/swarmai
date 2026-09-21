"""V2A-003a/b/R / ART-V15-LEASE-FENCING — durable worker/attempt/lease/result repos.

V2A-003a: persistence primitives (token_hash only — V2A-H2).
V2A-003b/R: atomic claim/renew/expire (+ H3 eligible skip, authority checks, paginated HOL).
Accept fencing remains V2A-003c.
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


class LeaseClaimError(ValueError):
    """Base error for claim/renew/expire fencing failures."""


class WorkerNotEligibleError(LeaseClaimError):
    """Worker token/generation/status cannot claim or renew."""


class LeaseRenewError(LeaseClaimError):
    """Lease cannot be renewed (expired, wrong generation, past renewable_until)."""


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
                task.status = self._expire_task_status(task)
            expired_ids.append(lease.lease_id)
        self.session.flush()
        return expired_ids

    def get_lease(self, lease_id: str) -> TaskLeaseRow | None:
        return self.session.get(TaskLeaseRow, lease_id)

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

    def _expire_task_status(self, task: TaskRow) -> str:
        """Return ready only when authority is still current; else non-dispatchable."""
        mission = self._load_claimable_mission(task)
        if mission is not None:
            return _CLAIMABLE_TASK_STATUS
        mission_row = self.session.get(MissionRow, task.mission_id)
        if mission_row is None or mission_row.status == "cancelled":
            return _CANCELLED_ON_EXPIRE
        if mission_row.status not in _RUNNABLE_MISSION_STATUSES:
            return _CANCELLED_ON_EXPIRE
        return _NON_DISPATCHABLE_ON_STALE_EXPIRE

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
