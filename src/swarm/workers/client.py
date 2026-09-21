"""V2A-004 worker client — transport-independent enrollment/dispatch/result path."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.db.lease_fencing import AcceptedResult
from swarm.db.models import WorkerLeaseRow
from swarm.workers.envelopes import (
    CancelLeaseRequest,
    CancelLeaseResponse,
    CapabilityAdvertisement,
    ClaimDispatchRequest,
    ClaimDispatchResponse,
    DrainRequest,
    DrainResponse,
    EnrollmentRequest,
    EnrollmentResponse,
    ReconnectRequest,
    ReconnectResponse,
    RenewLeaseRequest,
    RenewLeaseResponse,
    ResultSubmitRequest,
    ResultSubmitResponse,
    WorkerHeartbeatRequest,
    WorkerHeartbeatResponse,
)
from swarm.workers.transport import WorkerTransport


@dataclass
class WorkerClient:
    """Authenticated worker-side client. Never self-accepts results."""

    transport: WorkerTransport
    worker_id: str | None = None
    generation: int | None = None
    membership_token: str | None = None
    project_id: str | None = None
    active_lease_ids: list[str] = field(default_factory=list)

    def enroll(self, request: EnrollmentRequest) -> EnrollmentResponse:
        response = self.transport.enroll(request)
        self.worker_id = response.worker_id
        self.generation = response.generation
        self.membership_token = response.membership_token
        self.project_id = response.project_id
        return response

    def _require_credentials(self) -> tuple[str, int, str]:
        if not self.worker_id or self.generation is None or not self.membership_token:
            raise RuntimeError("worker_not_enrolled")
        return self.worker_id, int(self.generation), self.membership_token

    def heartbeat(
        self,
        *,
        worker_state: str = "active",
        available: dict[str, Any] | None = None,
        health: dict[str, Any] | None = None,
        progress_class: str | None = None,
    ) -> WorkerHeartbeatResponse:
        worker_id, generation, token = self._require_credentials()
        response = self.transport.heartbeat(
            WorkerHeartbeatRequest(
                worker_id=worker_id,
                generation=generation,
                membership_token=token,
                worker_state=worker_state,
                active_lease_ids=list(self.active_lease_ids),
                available=dict(available or {}),
                health=dict(health or {}),
                progress_class=progress_class,
            )
        )
        self.active_lease_ids = list(response.active_lease_ids)
        return response

    def advertise(
        self,
        *,
        capabilities: list[str] | None = None,
        capacity_units: float | None = None,
        privacy_classes: list[str] | None = None,
    ) -> WorkerLeaseRow:
        worker_id, generation, token = self._require_credentials()
        return self.transport.advertise(
            CapabilityAdvertisement(
                worker_id=worker_id,
                generation=generation,
                membership_token=token,
                capabilities=capabilities,
                capacity_units=capacity_units,
                privacy_classes=privacy_classes,
            )
        )

    def claim(self, *, agent_profile_id: str = "ap_default") -> ClaimDispatchResponse:
        worker_id, generation, token = self._require_credentials()
        response = self.transport.claim(
            ClaimDispatchRequest(
                worker_id=worker_id,
                generation=generation,
                membership_token=token,
                agent_profile_id=agent_profile_id,
            )
        )
        if response.claimed and response.lease_id:
            if response.lease_id not in self.active_lease_ids:
                self.active_lease_ids.append(response.lease_id)
        return response

    def renew(
        self,
        *,
        lease_id: str,
        progress_class: str = "running",
        extend_seconds: int | None = None,
    ) -> RenewLeaseResponse:
        worker_id, generation, token = self._require_credentials()
        return self.transport.renew(
            RenewLeaseRequest(
                lease_id=lease_id,
                worker_id=worker_id,
                generation=generation,
                membership_token=token,
                progress_class=progress_class,
                extend_seconds=extend_seconds,
            )
        )

    def submit_result(
        self,
        *,
        lease_id: str,
        status: str,
        checks: dict[str, Any] | None = None,
        usage: dict[str, Any] | None = None,
        artifact_manifest: dict[str, Any] | None = None,
        effect_receipts: list[Any] | None = None,
        summary: str | None = None,
        result_id: str | None = None,
    ) -> ResultSubmitResponse:
        """Submit immutable result evidence. Does not accept."""
        worker_id, generation, token = self._require_credentials()
        return self.transport.submit_result(
            ResultSubmitRequest(
                lease_id=lease_id,
                worker_id=worker_id,
                generation=generation,
                membership_token=token,
                status=status,
                summary=summary,
                artifact_manifest=dict(artifact_manifest or {}),
                checks=dict(checks or {}),
                usage=dict(usage or {}),
                effect_receipts=list(effect_receipts or []),
                result_id=result_id,
            )
        )

    def drain(self) -> DrainResponse:
        worker_id, generation, token = self._require_credentials()
        response = self.transport.drain(
            DrainRequest(
                worker_id=worker_id,
                generation=generation,
                membership_token=token,
            )
        )
        self.active_lease_ids = list(response.active_lease_ids)
        return response

    def cancel_lease(self, *, lease_id: str, reason: str = "cancelled") -> CancelLeaseResponse:
        response = self.transport.cancel_lease(
            CancelLeaseRequest(lease_id=lease_id, reason=reason)
        )
        if lease_id in self.active_lease_ids:
            self.active_lease_ids = [x for x in self.active_lease_ids if x != lease_id]
        return response

    def reconnect(self) -> ReconnectResponse:
        worker_id, generation, token = self._require_credentials()
        response = self.transport.reconnect(
            ReconnectRequest(
                worker_id=worker_id,
                generation=generation,
                membership_token=token,
            )
        )
        self.active_lease_ids = [row["lease_id"] for row in response.active_leases]
        return response

    def control_plane_accept(self, *, result_id: str) -> AcceptedResult:
        """Explicit control-plane path — not a worker self-accept API."""
        return self.transport.accept_result(result_id=result_id)
