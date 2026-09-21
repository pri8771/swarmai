"""Worker enrollment, leases, drain, revocation, and recovery fencing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import WorkerStatus
from swarm.contracts.mission import TaskSpec
from swarm.contracts.workspace import WorkerLease


class WorkerAuthError(PermissionError):
    pass


class StaleGenerationError(PermissionError):
    pass


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
    last_heartbeat: Any = field(default_factory=utc_now)


class WorkerRegistryService:
    """Trusted control-plane registry — no raw provider secrets on workers."""

    def __init__(self, *, heartbeat_ttl_seconds: int = 30) -> None:
        self.heartbeat_ttl = timedelta(seconds=heartbeat_ttl_seconds)
        self._workers: dict[str, WorkerRecord] = {}
        self._tokens: dict[str, str] = {}
        self._quarantine: set[str] = set()
        self._dispatch_queue: list[TaskSpec] = []

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

    def enqueue(self, task: TaskSpec) -> None:
        self._dispatch_queue.append(task)

    async def claim_dispatch(self, worker_id: str, *, token: str) -> TaskSpec | None:
        rec = self._require(worker_id, token)
        if rec.lease.status == WorkerStatus.DRAINING:
            return None
        if worker_id in self._quarantine:
            return None
        # V2A-H3: scan for first eligible task; leave incompatible heads in place
        # so they do not head-of-line block later compatible work (fairness preserved).
        for index, task in enumerate(self._dispatch_queue):
            needed = set(task.required_capabilities)
            have = set(rec.lease.capabilities)
            if needed and not needed.issubset(have):
                continue
            if "local_only" in task.scopes and "local" not in rec.privacy_classes:
                continue
            self._dispatch_queue.pop(index)
            rec.claimed_task_id = task.id
            return task
        return None

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
