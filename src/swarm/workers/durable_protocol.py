"""V2A-003c transport-independent durable worker protocol helpers.

Wraps :class:`~swarm.db.lease_fencing.LeaseLifecycleService` for enrollment-adjacent
drain/cancel/result paths. HTTP/queue transport remains out of scope; PostgreSQL
is authoritative.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from swarm.db.lease_fencing import (
    AcceptedResult,
    ClaimedLease,
    LeaseLifecycleService,
    WorkerRegistrationRepository,
)
from swarm.db.models import TaskLeaseRow, WorkerLeaseRow, WorkerResultRow


class DurableWorkerProtocol:
    """Small sync façade over durable lease/result fencing (ART-V15-WORKER-PROTOCOL)."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.lifecycle = LeaseLifecycleService(session)
        self.workers = WorkerRegistrationRepository(session)

    def request_drain(self, *, worker_id: str) -> WorkerLeaseRow:
        return self.workers.request_drain(worker_id=worker_id)

    def claim(
        self,
        *,
        worker_id: str,
        membership_token: str,
        agent_profile_id: str = "ap_default",
        now: datetime | None = None,
    ) -> ClaimedLease | None:
        return self.lifecycle.claim_eligible_attempt(
            worker_id=worker_id,
            membership_token=membership_token,
            agent_profile_id=agent_profile_id,
            now=now,
        )

    def renew(
        self,
        *,
        lease_id: str,
        worker_id: str,
        worker_generation: int,
        membership_token: str,
        now: datetime | None = None,
    ) -> TaskLeaseRow:
        return self.lifecycle.renew_lease(
            lease_id=lease_id,
            worker_id=worker_id,
            worker_generation=worker_generation,
            membership_token=membership_token,
            now=now,
        )

    def submit_result(
        self,
        *,
        lease_id: str,
        worker_id: str,
        membership_token: str,
        worker_generation: int,
        result_status: str,
        checks: dict[str, Any] | None = None,
        usage: dict[str, Any] | None = None,
        artifact_manifest: dict[str, Any] | None = None,
        effect_receipts: list[Any] | None = None,
        now: datetime | None = None,
    ) -> WorkerResultRow:
        return self.lifecycle.submit_result(
            lease_id=lease_id,
            worker_id=worker_id,
            membership_token=membership_token,
            worker_generation=worker_generation,
            result_status=result_status,
            checks=checks,
            usage=usage,
            artifact_manifest=artifact_manifest,
            effect_receipts=effect_receipts,
            now=now,
        )

    def accept_result(self, *, result_id: str, now: datetime | None = None) -> AcceptedResult:
        return self.lifecycle.accept_result(result_id=result_id, now=now)

    def cancel_lease(
        self, *, lease_id: str, reason: str = "cancelled", now: datetime | None = None
    ) -> TaskLeaseRow:
        return self.lifecycle.cancel_active_lease(lease_id=lease_id, reason=reason, now=now)
