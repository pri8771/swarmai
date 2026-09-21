"""V2A-003a/b / ART-V15-LEASE-FENCING — durable worker/attempt/lease/result repos.

V2A-003a: persistence primitives (token_hash only — V2A-H2).
V2A-003b: atomic claim/renew/expire (+ V2A-H3 eligible-task skip).
Accept fencing remains V2A-003c.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from swarm.contracts.common import new_id, utc_now
from swarm.db.models import (
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
_CLAIM_CANDIDATE_BATCH = 32


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


def _assert_no_raw_token_fields(payload: dict[str, Any] | None) -> None:
    if not payload:
        return
    for key in payload:
        if key.lower() in _FORBIDDEN_RAW_KEYS:
            raise RawTokenPersistenceError(f"raw_token_field_forbidden:{key}")


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
    """V2A-003b atomic claim / renew / expire (+ V2A-H3 eligible skip).

    Fairness: claim candidates are ordered by ``(priority ASC, created_at ASC)``.
    Incompatible locked rows are left unmutated so other workers may claim them;
    the claimer continues scanning rather than head-of-line blocking.
    """

    def __init__(
        self,
        session: Session,
        *,
        default_lease_seconds: int = _DEFAULT_LEASE_SECONDS,
        renewable_horizon_seconds: int = _DEFAULT_RENEWABLE_HORIZON_SECONDS,
    ) -> None:
        self.session = session
        self.default_lease_seconds = default_lease_seconds
        self.renewable_horizon_seconds = renewable_horizon_seconds
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
        candidate_batch: int = _CLAIM_CANDIDATE_BATCH,
    ) -> ClaimedLease | None:
        """Atomically claim one eligible ready task for the worker.

        Uses ``SELECT … FOR UPDATE SKIP LOCKED``. Returns ``None`` when no
        eligible task exists; does not mutate queue/task state in that case.
        """
        clock = now or utc_now()
        worker = self._require_claimable_worker(worker_id, membership_token)
        project_id = worker.project_id
        if not project_id:
            raise WorkerNotEligibleError("worker_missing_project_id")

        candidates = self._lock_ready_candidates(
            project_id=project_id,
            limit=candidate_batch,
        )
        for task in candidates:
            if not self._worker_eligible_for_task(worker, task):
                # V2A-H3: leave incompatible head locked-unmutated; keep scanning.
                continue
            if self._has_active_lease(task.id):
                continue
            return self._bind_claim(
                worker=worker,
                task=task,
                agent_profile_id=agent_profile_id,
                clock=clock,
                lease_seconds=lease_seconds or self.default_lease_seconds,
            )
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
        """Extend an active/renewed lease when generation and renewable window match."""
        clock = now or utc_now()
        worker = self._require_claimable_worker(worker_id, membership_token)
        lease = self.session.get(TaskLeaseRow, lease_id)
        if lease is None:
            raise LeaseRenewError("lease_not_found")
        if lease.worker_id != worker_id:
            raise LeaseRenewError("lease_worker_mismatch")
        if lease.worker_generation != worker_generation:
            raise LeaseRenewError("lease_generation_mismatch")
        if worker.lease_generation != worker_generation:
            raise LeaseRenewError("worker_generation_mismatch")
        if lease.state not in _ACTIVE_LEASE_STATES:
            raise LeaseRenewError(f"lease_not_renewable:{lease.state}")
        if lease.expires_at <= clock:
            raise LeaseRenewError("lease_already_expired")
        if lease.renewable_until is not None and clock > lease.renewable_until:
            raise LeaseRenewError("past_renewable_until")
        extension = timedelta(seconds=extend_seconds or self.default_lease_seconds)
        lease.expires_at = clock + extension
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

        Returns expired lease IDs. Tasks still marked ``leased`` are returned to
        ``ready`` so a later claim can reassign them.
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
                task.status = _CLAIMABLE_TASK_STATUS
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

    def _lock_ready_candidates(self, *, project_id: str, limit: int) -> list[TaskRow]:
        stmt = (
            select(TaskRow)
            .where(
                TaskRow.project_id == project_id,
                TaskRow.status == _CLAIMABLE_TASK_STATUS,
            )
            .order_by(TaskRow.priority.asc(), TaskRow.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(self.session.scalars(stmt))

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
        agent_profile_id: str,
        clock: datetime,
        lease_seconds: int,
    ) -> ClaimedLease:
        assert worker.project_id is not None
        expires_at = clock + timedelta(seconds=lease_seconds)
        renewable_until = clock + timedelta(seconds=self.renewable_horizon_seconds)
        payload = task.payload if isinstance(task.payload, dict) else {}
        input_digest = payload.get("input_digest") if isinstance(payload, dict) else None
        source_revision = payload.get("source_revision") if isinstance(payload, dict) else None
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
            source_revision=source_revision if isinstance(source_revision, str) else None,
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
