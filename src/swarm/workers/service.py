"""V2A-004 / ART-V15-WORKER-PROTOCOL — durable control-plane worker service.

PostgreSQL remains authoritative. Transport (HTTP/queue/DBOS) is intentionally
absent here; callers use :class:`~swarm.workers.transport.WorkerTransport`.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from swarm.contracts.common import new_id, utc_now
from swarm.db.lease_fencing import (
    AcceptedResult,
    LeaseLifecycleService,
    MissionCancellation,
    WorkerNotEligibleError,
    WorkerRegistrationRepository,
)
from swarm.db.models import TaskLeaseRow, WorkerLeaseRow, WorkerResultRow
from swarm.workers.envelopes import (
    SUPPORTED_PROTOCOL_RANGE,
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

# Trust classes the control plane may grant without extra policy (strict subset ok).
_DEFAULT_TRUST_ALLOW = frozenset(
    {"compute_only", "code_write", "browser_session", "operator_local", "standard"}
)


class ProtocolVersionError(ValueError):
    """Worker protocol version outside the supported range."""


class DurableWorkerService:
    """Control-plane worker enrollment, heartbeat, dispatch, drain, and result path."""

    def __init__(
        self,
        session: Session,
        *,
        granted_capability_allowlist: set[str] | None = None,
        heartbeat_interval_seconds: int = 30,
    ) -> None:
        self.session = session
        self.lifecycle = LeaseLifecycleService(session)
        self.workers = WorkerRegistrationRepository(session)
        self.granted_capability_allowlist = granted_capability_allowlist
        self.heartbeat_interval_seconds = heartbeat_interval_seconds

    def enroll(self, request: EnrollmentRequest) -> EnrollmentResponse:
        self._require_protocol(request.protocol_version)
        self._reject_secret_bearing_nonce(request)
        granted_caps = self._grant_capabilities(request.capabilities)
        if request.trust_class in _DEFAULT_TRUST_ALLOW:
            trust = request.trust_class
        else:
            trust = "compute_only"
        scopes = list(request.scopes_requested)
        # Never silently broaden: scopes must include the project scope form when present.
        project_scope = f"project:{request.project_id}"
        if project_scope not in scopes:
            scopes = [project_scope, *scopes]
        membership_token = new_id("wt_")
        worker_id = request.worker_id or new_id("wrk_")
        existing = self.workers.get(worker_id)
        generation = 1
        if existing is not None:
            # Re-enrollment under same id bumps generation and replaces credentials.
            generation = int(existing.lease_generation) + 1
        row, token_id = self.workers.upsert_registration(
            worker_id=worker_id,
            project_id=request.project_id,
            node_identity=request.host_alias,
            architecture=request.architecture,
            runtime_version=request.runtime_version,
            capacity_units=float(request.capacity_units),
            membership_token=membership_token,
            status="online",
            generation=generation,
            trust_class=trust,
            labels=list(request.labels),
            capabilities=granted_caps,
            privacy_classes=list(request.privacy_classes),
            resource_payload={
                "resources": request.resources.model_dump(mode="json"),
                "artifact_transport": request.artifact_transport.model_dump(mode="json"),
                "worker_nonce": request.worker_nonce,
            },
            policy_version=request.policy_version,
            software_version=request.software.swarm_version,
            build_sha=request.software.worker_build_sha,
        )
        return EnrollmentResponse(
            worker_id=row.worker_id,
            generation=int(row.lease_generation),
            membership_token=membership_token,
            token_id=token_id,
            scopes_granted=scopes,
            capabilities_granted=granted_caps,
            trust_class=trust,
            heartbeat_interval_seconds=self.heartbeat_interval_seconds,
            policy_version=request.policy_version,
            project_id=request.project_id,
        )

    def heartbeat(self, request: WorkerHeartbeatRequest) -> WorkerHeartbeatResponse:
        self._require_protocol(request.protocol_version)
        # Capability expansion via heartbeat is forbidden — ignore capability_changes
        # that expand; voluntary reductions go through advertise().
        if request.capability_changes:
            raise WorkerNotEligibleError("capability_changes_require_advertise_or_reenroll")
        row = self.workers.record_heartbeat(
            worker_id=request.worker_id,
            membership_token=request.membership_token,
            generation=request.generation,
            worker_state=request.worker_state,
            active_lease_ids=request.active_lease_ids,
            available=request.available,
            health=request.health,
            observed_at=request.observed_at,
        )
        active = self.lifecycle.list_active_leases_for_worker(request.worker_id)
        cancel_notices = [
            lease.lease_id
            for lease in active
            if self._lease_cancellation_stale(lease)
        ]
        return WorkerHeartbeatResponse(
            worker_id=row.worker_id,
            generation=int(row.lease_generation),
            status=row.status,
            server_received_at=utc_now(),
            active_lease_ids=[lease.lease_id for lease in active],
            cancel_notices=cancel_notices,
        )

    def advertise(self, request: CapabilityAdvertisement) -> WorkerLeaseRow:
        self._require_protocol(request.protocol_version)
        return self.workers.advertise_capabilities(
            worker_id=request.worker_id,
            membership_token=request.membership_token,
            generation=request.generation,
            capabilities=request.capabilities,
            capacity_units=request.capacity_units,
            privacy_classes=request.privacy_classes,
        )

    def claim(self, request: ClaimDispatchRequest) -> ClaimDispatchResponse:
        self._require_protocol(request.protocol_version)
        worker = self.workers.get(request.worker_id)
        if worker is None:
            raise WorkerNotEligibleError("worker_not_found")
        if int(worker.lease_generation) != int(request.generation):
            raise WorkerNotEligibleError("worker_generation_mismatch")
        claimed = self.lifecycle.claim_eligible_attempt(
            worker_id=request.worker_id,
            membership_token=request.membership_token,
            agent_profile_id=request.agent_profile_id,
        )
        if claimed is None:
            return ClaimDispatchResponse(claimed=False)
        return ClaimDispatchResponse(
            claimed=True,
            lease_id=claimed.lease_id,
            attempt_id=claimed.attempt_id,
            task_id=claimed.task_id,
            mission_id=claimed.mission_id,
            project_id=claimed.project_id,
            worker_generation=claimed.worker_generation,
            task_revision=claimed.task_revision,
            expires_at=claimed.expires_at,
            state=claimed.state,
        )

    def renew(self, request: RenewLeaseRequest) -> RenewLeaseResponse:
        self._require_protocol(request.protocol_version)
        lease = self.lifecycle.renew_lease(
            lease_id=request.lease_id,
            worker_id=request.worker_id,
            worker_generation=request.generation,
            membership_token=request.membership_token,
            extend_seconds=request.extend_seconds,
        )
        # Persist progress class on lease-adjacent worker payload for audit.
        worker = self.workers.get(request.worker_id)
        if worker is not None:
            payload = dict(worker.resource_payload or {})
            progress = dict(payload.get("lease_progress") or {})
            progress[request.lease_id] = {
                "progress_class": request.progress_class,
                "updated_at": utc_now().isoformat(),
            }
            payload["lease_progress"] = progress
            worker.resource_payload = payload
            worker.updated_at = utc_now()
            self.session.flush()
        return RenewLeaseResponse(
            lease_id=lease.lease_id,
            state=lease.state,
            expires_at=lease.expires_at,
            renewable_until=lease.renewable_until,
        )

    def submit_result(self, request: ResultSubmitRequest) -> ResultSubmitResponse:
        """Worker result path — durable submit only; never self-accepts."""
        self._require_protocol(request.protocol_version)
        if request.generation < 0:
            raise WorkerNotEligibleError("invalid_generation")
        artifact = dict(request.artifact_manifest)
        if request.summary:
            artifact.setdefault("summary", request.summary[:400])
        row = self.lifecycle.submit_result(
            lease_id=request.lease_id,
            worker_id=request.worker_id,
            membership_token=request.membership_token,
            worker_generation=request.generation,
            result_status=request.status,
            artifact_manifest=artifact,
            checks=request.checks,
            usage=request.usage,
            effect_receipts=request.effect_receipts,
            result_id=request.result_id,
        )
        return ResultSubmitResponse(
            result_id=row.result_id,
            acceptance_state=row.acceptance_state,
            attempt_id=row.attempt_id,
            lease_id=row.lease_id,
            submitted_at=row.submitted_at,
        )

    def revoke_mission_work(
        self, *, mission_id: str, reason: str = "revoked", notify_leases: bool = True
    ) -> MissionCancellation:
        """Control-plane durable cancellation bump (fences in-flight leases/results)."""
        return self.lifecycle.revoke_mission_work(
            mission_id=mission_id, reason=reason, notify_leases=notify_leases
        )

    def cancel_mission(self, *, mission_id: str, reason: str = "cancelled") -> MissionCancellation:
        """Control-plane terminal mission cancellation."""
        return self.lifecycle.cancel_mission(mission_id=mission_id, reason=reason)

    def accept_result(self, *, result_id: str, now: datetime | None = None) -> AcceptedResult:
        """Control-plane acceptance only (workers must not call this)."""
        return self.lifecycle.accept_result(result_id=result_id, now=now)

    def drain(self, request: DrainRequest) -> DrainResponse:
        self._require_protocol(request.protocol_version)
        if not self.workers.verify_membership(
            worker_id=request.worker_id, membership_token=request.membership_token
        ):
            raise WorkerNotEligibleError("invalid_membership_token")
        row = self.workers.get(request.worker_id)
        if row is None:
            raise WorkerNotEligibleError("worker_not_found")
        if int(row.lease_generation) != int(request.generation):
            raise WorkerNotEligibleError("worker_generation_mismatch")
        drained = self.workers.request_drain(worker_id=request.worker_id)
        active = self.lifecycle.list_active_leases_for_worker(request.worker_id)
        if not active and drained.status == "draining":
            drained.status = "offline"
            drained.updated_at = utc_now()
            self.session.flush()
        return DrainResponse(
            worker_id=drained.worker_id,
            status=drained.status,
            active_lease_ids=[lease.lease_id for lease in active],
            drain_requested_at=drained.drain_requested_at,
        )

    def cancel_lease(self, request: CancelLeaseRequest) -> CancelLeaseResponse:
        self._require_protocol(request.protocol_version)
        lease = self.lifecycle.cancel_active_lease(
            lease_id=request.lease_id, reason=request.reason
        )
        return CancelLeaseResponse(lease_id=lease.lease_id, state=lease.state)

    def reconnect(self, request: ReconnectRequest) -> ReconnectResponse:
        """Restart recovery: ownership comes from durable rows, not process memory."""
        self._require_protocol(request.protocol_version)
        if not self.workers.verify_membership(
            worker_id=request.worker_id, membership_token=request.membership_token
        ):
            raise WorkerNotEligibleError("invalid_membership_token")
        row = self.workers.get(request.worker_id)
        if row is None:
            raise WorkerNotEligibleError("worker_not_found")
        if int(row.lease_generation) != int(request.generation):
            raise WorkerNotEligibleError("worker_generation_mismatch")
        # Touch heartbeat to prove reconnect liveness without claiming success.
        self.workers.record_heartbeat(
            worker_id=request.worker_id,
            membership_token=request.membership_token,
            generation=request.generation,
            worker_state="active" if row.status == "online" else row.status,
        )
        active = self.lifecycle.list_active_leases_for_worker(request.worker_id)
        return ReconnectResponse(
            worker_id=row.worker_id,
            generation=int(row.lease_generation),
            status=row.status,
            active_leases=[
                {
                    "lease_id": lease.lease_id,
                    "attempt_id": lease.attempt_id,
                    "task_id": lease.task_id,
                    "mission_id": lease.mission_id,
                    "state": lease.state,
                    "expires_at": lease.expires_at.isoformat(),
                    "worker_generation": lease.worker_generation,
                    "task_revision": lease.task_revision,
                    "cancellation_generation": lease.cancellation_generation,
                }
                for lease in active
            ],
        )

    def get_result(self, result_id: str) -> WorkerResultRow | None:
        return self.lifecycle.get_result(result_id)
    @staticmethod
    def _require_protocol(version: str) -> None:
        low, high = SUPPORTED_PROTOCOL_RANGE
        if version < low or version > high:
            raise ProtocolVersionError(f"unsupported_protocol:{version}")

    @staticmethod
    def _reject_secret_bearing_nonce(request: EnrollmentRequest) -> None:
        blob = " ".join(
            [
                request.worker_nonce,
                request.host_alias,
                " ".join(request.capabilities),
                str(request.resources.model_dump()),
            ]
        ).lower()
        for needle in ("sk-", "api_key", "secret=", "password", "cookie="):
            if needle in blob:
                raise WorkerNotEligibleError("provider_secret_forbidden_on_enrollment")

    def _grant_capabilities(self, requested: list[str]) -> list[str]:
        if self.granted_capability_allowlist is None:
            return sorted(set(requested))
        return sorted(set(requested) & self.granted_capability_allowlist)

    def _lease_cancellation_stale(self, lease: TaskLeaseRow) -> bool:
        from swarm.db.models import MissionRow

        mission = self.session.get(MissionRow, lease.mission_id)
        if mission is None:
            return True
        return int(lease.cancellation_generation) != int(mission.cancellation_generation)
