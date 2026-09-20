"""Fake worker registry."""

from __future__ import annotations

from swarm.contracts.enums import WorkerStatus
from swarm.contracts.mission import TaskSpec
from swarm.contracts.workspace import WorkerLease
from swarm.fakes.clock import FakeClock


class FakeWorkerRegistry:
    def __init__(self, clock: FakeClock | None = None) -> None:
        self.clock = clock or FakeClock()
        self.workers: dict[str, WorkerLease] = {}
        self._queue: list[TaskSpec] = []

    async def register(self, lease: WorkerLease) -> WorkerLease:
        lease.heartbeat_at = self.clock.now()
        self.workers[lease.worker_id] = lease
        return lease

    async def heartbeat(self, worker_id: str, generation: int) -> WorkerLease:
        worker = self.workers[worker_id]
        if generation < worker.lease_generation:
            raise PermissionError("stale worker generation")
        worker.heartbeat_at = self.clock.now()
        return worker

    async def claim_dispatch(self, worker_id: str) -> TaskSpec | None:
        if worker_id not in self.workers:
            raise KeyError(worker_id)
        if not self._queue:
            return None
        return self._queue.pop(0)

    async def drain(self, worker_id: str) -> WorkerLease:
        worker = self.workers[worker_id]
        worker.status = WorkerStatus.DRAINING
        return worker

    async def revoke_generation(self, worker_id: str) -> int:
        worker = self.workers[worker_id]
        worker.lease_generation += 1
        worker.status = WorkerStatus.QUARANTINED
        return worker.lease_generation

    def enqueue(self, task: TaskSpec) -> None:
        self._queue.append(task)
