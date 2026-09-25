"""Worker enrollment, leases, drain, revocation, and recovery fencing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import WorkerStatus
from swarm.contracts.mission import TaskSpec
from swarm.contracts.workspace import WorkerLease


class WorkerAuthError(PermissionError):
    pass


class StaleGenerationError(PermissionError):
    pass


class LeaseStateError(RuntimeError):
    pass


@dataclass
class DispatchLease:
    """Server-owned work lease — workers submit results; they never self-accept."""

    lease_id: str
    task: TaskSpec
    worker_id: str
    worker_generation: int
    expires_at: datetime
    state: str = "claimed"  # claimed | renewed | cancelled | submitted | expired
    cancel_requested: bool = False
    cancel_reason: str | None = None
    result_id: str | None = None
    result_payload: dict[str, Any] | None = None
    submitted_at: datetime | None = None
    acceptance_state: str = "pending"  # pending | accepted | rejected — control-plane only


@dataclass
class ClaimedDispatch:
    claimed: bool
    lease: DispatchLease | None = None
    cancel_notices: list[str] = field(default_factory=list)


@dataclass
class WorkerRecord:
    lease: WorkerLease
    token: str
    project_id: str | None = None
    revoked: bool = False
    privacy_classes: set[str] = field(default_factory=lambda: {"local"})
    named_inference_urls: list[str] = field(default_factory=list)
    measured_capacity: float = 1.0
    claimed_task_id: str | None = None
    active_lease_ids: list[str] = field(default_factory=list)
    last_heartbeat: Any = field(default_factory=utc_now)


class WorkerRegistryService:
    """Trusted control-plane registry — no raw provider secrets on workers."""

    def __init__(
        self,
        *,
        heartbeat_ttl_seconds: int = 30,
        lease_ttl_seconds: int = 60,
    ) -> None:
        self.heartbeat_ttl = timedelta(seconds=heartbeat_ttl_seconds)
        self.lease_ttl = timedelta(seconds=lease_ttl_seconds)
        self._workers: dict[str, WorkerRecord] = {}
        self._tokens: dict[str, str] = {}
        self._quarantine: set[str] = set()
        self._dispatch_queue: list[TaskSpec] = []
        self._leases: dict[str, DispatchLease] = {}
        self._results: dict[str, dict[str, Any]] = {}

    async def register(
        self,
        lease: WorkerLease,
        *,
        token: str | None = None,
        project_id: str | None = None,
    ) -> WorkerLease:
        token = token or new_id("wt_")
        # Never store provider secrets — token is membership only.
        if any(k in token.lower() for k in ("sk-", "api_key", "secret=")):
            raise WorkerAuthError("provider_secret_forbidden_on_worker_token")
        lease = lease.model_copy(update={"status": WorkerStatus.ONLINE})
        rec = WorkerRecord(
            lease=lease,
            token=token,
            project_id=project_id,
            measured_capacity=lease.capacity_units,
        )
        self._workers[lease.worker_id] = rec
        self._tokens[token] = lease.worker_id
        return lease

    def _require(self, worker_id: str, token: str) -> WorkerRecord:
        wid = self._tokens.get(token)
        if wid != worker_id:
            raise WorkerAuthError("invalid_token")
        rec = self._workers[worker_id]
        if rec.revoked:
            raise WorkerAuthError("revoked")
        return rec

    async def heartbeat(self, worker_id: str, generation: int, *, token: str) -> WorkerLease:
        rec = self._require(worker_id, token)
        if generation != rec.lease.lease_generation:
            raise StaleGenerationError("heartbeat_generation_mismatch")
        rec.last_heartbeat = utc_now()
        rec.lease = rec.lease.model_copy(update={"heartbeat_at": rec.last_heartbeat})
        return rec.lease

    def cancel_notices_for(self, worker_id: str) -> list[str]:
        notices: list[str] = []
        now = utc_now()
        for lease in self._leases.values():
            if lease.worker_id != worker_id:
                continue
            if lease.cancel_requested and lease.state not in {"cancelled", "submitted"}:
                notices.append(lease.lease_id)
            elif lease.state in {"claimed", "renewed"} and lease.expires_at <= now:
                lease.state = "expired"
                notices.append(lease.lease_id)
        return notices

    def enqueue(self, task: TaskSpec) -> None:
        self._dispatch_queue.append(task)

    def _task_matches_worker(self, task: TaskSpec, rec: WorkerRecord) -> bool:
        needed = set(task.required_capabilities)
        have = set(rec.lease.capabilities)
        if needed and not needed.issubset(have):
            return False
        if "local_only" in task.scopes and "local" not in rec.privacy_classes:
            return False
        if "mac_local" in task.scopes and "mac_local" not in rec.privacy_classes:
            return False
        return True

    async def claim_dispatch(self, worker_id: str, *, token: str) -> TaskSpec | None:
        """Backward-compatible claim — returns TaskSpec or None."""
        claimed = await self.claim_work(worker_id, token=token)
        return claimed.lease.task if claimed.claimed and claimed.lease else None

    async def claim_work(self, worker_id: str, *, token: str) -> ClaimedDispatch:
        rec = self._require(worker_id, token)
        notices = self.cancel_notices_for(worker_id)
        if rec.lease.status == WorkerStatus.DRAINING:
            return ClaimedDispatch(claimed=False, cancel_notices=notices)
        if worker_id in self._quarantine:
            return ClaimedDispatch(claimed=False, cancel_notices=notices)
        if rec.claimed_task_id is not None:
            # One active claim per worker for this registry path.
            return ClaimedDispatch(claimed=False, cancel_notices=notices)

        pending: list[TaskSpec] = []
        matched: TaskSpec | None = None
        while self._dispatch_queue:
            task = self._dispatch_queue.pop(0)
            if self._task_matches_worker(task, rec):
                matched = task
                break
            pending.append(task)
        # Restore unmatched tasks in original relative order.
        self._dispatch_queue = pending + self._dispatch_queue
        if matched is None:
            return ClaimedDispatch(claimed=False, cancel_notices=notices)

        lease = DispatchLease(
            lease_id=new_id("lease_"),
            task=matched,
            worker_id=worker_id,
            worker_generation=rec.lease.lease_generation,
            expires_at=utc_now() + self.lease_ttl,
            state="claimed",
        )
        self._leases[lease.lease_id] = lease
        rec.claimed_task_id = matched.id
        rec.active_lease_ids.append(lease.lease_id)
        return ClaimedDispatch(claimed=True, lease=lease, cancel_notices=notices)

    def renew_lease(
        self,
        *,
        lease_id: str,
        worker_id: str,
        generation: int,
        token: str,
        extend_seconds: int | None = None,
    ) -> DispatchLease:
        rec = self._require(worker_id, token)
        if generation != rec.lease.lease_generation:
            raise StaleGenerationError("renew_generation_mismatch")
        lease = self._leases.get(lease_id)
        if lease is None:
            raise LeaseStateError("lease_not_found")
        if lease.worker_id != worker_id:
            raise LeaseStateError("lease_worker_mismatch")
        if lease.cancel_requested or lease.state == "cancelled":
            raise LeaseStateError("lease_cancelled")
        if lease.state == "submitted":
            raise LeaseStateError("lease_already_submitted")
        if lease.expires_at <= utc_now():
            lease.state = "expired"
            raise LeaseStateError("lease_expired")
        ttl = timedelta(seconds=extend_seconds) if extend_seconds else self.lease_ttl
        lease.expires_at = utc_now() + ttl
        lease.state = "renewed"
        return lease

    def submit_result(
        self,
        *,
        lease_id: str,
        worker_id: str,
        generation: int,
        token: str,
        status: str,
        checks: dict[str, Any] | None = None,
        artifact_manifest: dict[str, Any] | None = None,
        usage: dict[str, Any] | None = None,
        summary: str | None = None,
        result_id: str | None = None,
    ) -> dict[str, Any]:
        """Durable submit only — never accepts. Control plane accepts separately."""
        rec = self._require(worker_id, token)
        if generation != rec.lease.lease_generation:
            raise StaleGenerationError("submit_generation_mismatch")
        lease = self._leases.get(lease_id)
        if lease is None:
            raise LeaseStateError("lease_not_found")
        if lease.worker_id != worker_id:
            raise LeaseStateError("lease_worker_mismatch")
        if lease.cancel_requested or lease.state == "cancelled":
            raise LeaseStateError("lease_cancelled")
        if lease.state == "expired" or lease.expires_at <= utc_now():
            lease.state = "expired"
            raise LeaseStateError("lease_expired")
        if lease.state == "submitted" and lease.result_id:
            # Idempotent replay of same result_id.
            existing = self._results.get(lease.result_id)
            if existing is not None:
                return existing

        rid = result_id or new_id("res_")
        payload = {
            "result_id": rid,
            "lease_id": lease_id,
            "attempt_id": new_id("att_"),
            "task_id": lease.task.id,
            "mission_id": lease.task.mission_id,
            "worker_id": worker_id,
            "status": status,
            "checks": dict(checks or {}),
            "artifact_manifest": dict(artifact_manifest or {}),
            "usage": dict(usage or {}),
            "summary": (summary or "")[:400],
            "acceptance_state": "pending",
            "submitted_at": utc_now().isoformat(),
        }
        self._results[rid] = payload
        lease.state = "submitted"
        lease.result_id = rid
        lease.result_payload = payload
        lease.submitted_at = utc_now()
        lease.acceptance_state = "pending"
        rec.claimed_task_id = None
        if lease_id in rec.active_lease_ids:
            rec.active_lease_ids = [x for x in rec.active_lease_ids if x != lease_id]
        return payload

    def control_plane_accept_result(self, result_id: str, *, accepted: bool) -> dict[str, Any]:
        """Control-plane only — workers must not call this."""
        row = self._results.get(result_id)
        if row is None:
            raise LeaseStateError("result_not_found")
        row = dict(row)
        row["acceptance_state"] = "accepted" if accepted else "rejected"
        row["accepted_at"] = utc_now().isoformat()
        self._results[result_id] = row
        lease = self._leases.get(str(row.get("lease_id") or ""))
        if lease is not None:
            lease.acceptance_state = row["acceptance_state"]
        return row

    def cancel_lease(self, *, lease_id: str, reason: str = "cancelled") -> DispatchLease:
        lease = self._leases.get(lease_id)
        if lease is None:
            raise LeaseStateError("lease_not_found")
        if lease.state == "submitted":
            raise LeaseStateError("cannot_cancel_submitted")
        lease.cancel_requested = True
        lease.cancel_reason = reason
        lease.state = "cancelled"
        rec = self._workers.get(lease.worker_id)
        if rec is not None:
            if rec.claimed_task_id == lease.task.id:
                rec.claimed_task_id = None
            if lease_id in rec.active_lease_ids:
                rec.active_lease_ids = [x for x in rec.active_lease_ids if x != lease_id]
        return lease

    def reconnect(self, worker_id: str, *, generation: int, token: str) -> dict[str, Any]:
        rec = self._require(worker_id, token)
        if generation != rec.lease.lease_generation:
            raise StaleGenerationError("reconnect_generation_mismatch")
        rec.last_heartbeat = utc_now()
        active = [
            {
                "lease_id": lease.lease_id,
                "task_id": lease.task.id,
                "mission_id": lease.task.mission_id,
                "state": lease.state,
                "expires_at": lease.expires_at.isoformat(),
                "cancel_requested": lease.cancel_requested,
                "worker_generation": lease.worker_generation,
            }
            for lease in self._leases.values()
            if lease.worker_id == worker_id and lease.state in {"claimed", "renewed"}
        ]
        return {
            "worker_id": worker_id,
            "generation": generation,
            "status": rec.lease.status.value,
            "active_leases": active,
            "cancel_notices": self.cancel_notices_for(worker_id),
        }

    async def drain(self, worker_id: str, *, token: str) -> WorkerLease:
        rec = self._require(worker_id, token)
        rec.lease = rec.lease.model_copy(update={"status": WorkerStatus.DRAINING})
        # Complete current claim then exit — clear claim when done.
        if rec.claimed_task_id is None:
            rec.lease = rec.lease.model_copy(update={"status": WorkerStatus.OFFLINE})
        return rec.lease

    def complete_current(self, worker_id: str) -> None:
        rec = self._workers[worker_id]
        rec.claimed_task_id = None
        if rec.lease.status == WorkerStatus.DRAINING:
            rec.lease = rec.lease.model_copy(update={"status": WorkerStatus.OFFLINE})

    async def revoke_generation(self, worker_id: str) -> int:
        rec = self._workers[worker_id]
        rec.revoked = True
        new_gen = rec.lease.lease_generation + 1
        rec.lease = rec.lease.model_copy(
            update={"lease_generation": new_gen, "status": WorkerStatus.QUARANTINED}
        )
        self._quarantine.add(worker_id)
        # Fence old generation — token invalidated.
        for tok, wid in list(self._tokens.items()):
            if wid == worker_id:
                del self._tokens[tok]
        return new_gen

    def accept_result(
        self,
        worker_id: str,
        *,
        lease_generation: int,
        task_id: str,
    ) -> None:
        rec = self._workers[worker_id]
        if lease_generation != rec.lease.lease_generation:
            raise StaleGenerationError("stale_result_rejected")
        if worker_id in self._quarantine:
            raise StaleGenerationError("quarantined")
        if rec.claimed_task_id != task_id:
            raise StaleGenerationError("task_claim_mismatch")

    def suspect_lost_heartbeat(self, worker_id: str) -> str:
        """Lost heartbeat is suspicion, not permission for duplicate external action."""
        rec = self._workers[worker_id]
        age = utc_now() - rec.last_heartbeat
        if age > self.heartbeat_ttl:
            self._quarantine.add(worker_id)
            return "suspect_quarantine_unresolved_side_effects"
        return "healthy"

    def total_capacity(self) -> float:
        return sum(
            r.measured_capacity
            for r in self._workers.values()
            if r.lease.status == WorkerStatus.ONLINE and not r.revoked
        )

    def inspect(self, *, project_id: str | None = None) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for r in self._workers.values():
            if project_id is not None and r.project_id != project_id:
                continue
            rows.append(
                {
                    "worker_id": r.lease.worker_id,
                    "project_id": r.project_id,
                    "status": r.lease.status.value,
                    "generation": r.lease.lease_generation,
                    "capacity": float(r.measured_capacity),
                    "privacy": sorted(r.privacy_classes),
                    "claimed": r.claimed_task_id,
                    "active_leases": list(r.active_lease_ids),
                    "revoked": r.revoked,
                }
            )
        online = [
            row
            for row in rows
            if row["status"] == WorkerStatus.ONLINE.value and not row["revoked"]
        ]
        return {
            "workers": rows,
            "total_capacity": sum(float(row["capacity"]) for row in online),
            "quarantine": sorted(
                wid
                for wid in self._quarantine
                if project_id is None
                or (self._workers.get(wid) and self._workers[wid].project_id == project_id)
            ),
            "dispatch_queue_depth": len(self._dispatch_queue),
            "active_lease_count": sum(
                1 for lease in self._leases.values() if lease.state in {"claimed", "renewed"}
            ),
        }


def worker_self_test(*, mode: str = "mock") -> dict[str, Any]:
    if mode != "mock":
        return {"ok": False, "error": "live_worker_test_not_enabled"}
    # Synchronous smoke using asyncio.run at CLI layer — keep pure here.
    import asyncio

    async def _run() -> dict[str, Any]:
        reg = WorkerRegistryService()
        lease = WorkerLease(
            node_identity="local-dev",
            architecture="arm64",
            runtime_version="0.1.0",
            capacity_units=2.0,
            capabilities=["chat", "tools", "code.read"],
            labels=["local"],
        )
        token = new_id("wt_")
        lease = await reg.register(lease, token=token)
        await reg.heartbeat(lease.worker_id, lease.lease_generation, token=token)
        return {
            "ok": True,
            "mode": "mock",
            "mock_vs_live": "membership_only_no_provider_secrets",
            "worker_id": lease.worker_id,
            "capacity": reg.total_capacity(),
            "inspect": reg.inspect(),
        }

    return asyncio.run(_run())
