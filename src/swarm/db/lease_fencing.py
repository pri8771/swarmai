"""V2A-003a / ART-V15-LEASE-FENCING — durable worker/attempt/lease/result repos.

Claim/renew/accept fencing transactions land in V2A-003b/c. This module provides
persistence primitives only and never stores raw membership tokens (V2A-H2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from swarm.contracts.common import new_id, utc_now
from swarm.db.models import TaskAttemptRow, TaskLeaseRow, WorkerLeaseRow, WorkerResultRow
from swarm.db.token_hash import hash_membership_token, new_token_id


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
