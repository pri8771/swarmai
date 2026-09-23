"""V2A-005 / ART-V15-RECOVERY-EVIDENCE — multi-worker recovery harness.

Exercises host enrollment, dispatch, kill, lease expiry/reassignment,
stale-result rejection, drain, and restart/recovery against the durable
worker service + accept fence.

This harness is **single-process / simulated multi-worker**. It does not
claim live multi-host (Mac+Windows) proof. Live multi-host remains UNKNOWN
until ART-V15-MULTIHOST-EVIDENCE has real second-host receipts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.db.lease_fencing import ResultAcceptanceError, WorkerNotEligibleError
from swarm.db.models import TaskRow
from swarm.db.repositories import MissionRepository
from swarm.workers.client import WorkerClient
from swarm.workers.envelopes import EnrollmentRequest
from swarm.workers.service import DurableWorkerService
from swarm.workers.transport import InProcessWorkerTransport


@dataclass
class HarnessScenarioResult:
    name: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class RecoveryHarnessReport:
    """Honest evidence envelope for B3."""

    artifact_id: str = "ART-V15-RECOVERY-EVIDENCE"
    packet_id: str = "V2A-005"
    mode: str = "simulated_multi_worker_single_process"
    live_multi_host_evidence: str = "UNKNOWN_pending_second_physical_host"
    scenarios: list[HarnessScenarioResult] = field(default_factory=list)
    spend_usd: float = 0.0

    @property
    def all_passed(self) -> bool:
        return bool(self.scenarios) and all(s.passed for s in self.scenarios)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "packet_id": self.packet_id,
            "mode": self.mode,
            "live_multi_host_evidence": self.live_multi_host_evidence,
            "all_passed": self.all_passed,
            "spend_usd": self.spend_usd,
            "scenarios": [
                {
                    "name": s.name,
                    "passed": s.passed,
                    "details": s.details,
                    "error": s.error,
                }
                for s in self.scenarios
            ],
        }


class MultiWorkerRecoveryHarness:
    """Deterministic failure-mode suite over one DB session / one process."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.service = DurableWorkerService(session)
        self.transport = InProcessWorkerTransport(self.service)

    def run_all(self, *, now: datetime | None = None) -> RecoveryHarnessReport:
        clock = now or utc_now()
        report = RecoveryHarnessReport()
        for runner in (
            self.scenario_host_enrollment,
            self.scenario_dispatch_race,
            self.scenario_worker_kill_expire_reassign,
            self.scenario_stale_result_rejected,
            self.scenario_drain,
            self.scenario_restart_recovery,
        ):
            report.scenarios.append(runner(clock=clock))
        return report

    def _seed_mission_with_tasks(
        self, *, n_tasks: int = 1, caps: list[str] | None = None
    ) -> tuple[Any, list[TaskRow]]:
        mission = sample_mission().model_copy(
            update={"id": new_id("msn_"), "status": MissionStatus.RUNNING}
        )
        MissionRepository(self.session).insert(mission)
        self.session.flush()
        tasks: list[TaskRow] = []
        for i in range(n_tasks):
            tid = new_id("tsk_")
            task = sample_task(mission_id=mission.id).model_copy(
                update={
                    "id": tid,
                    "project_id": mission.project_id,
                    "required_capabilities": list(caps or ["code.read"]),
                    "scopes": ["scope_repo_demo"],
                    "status": TaskStatus.READY,
                    "priority": 10 + i,
                    "graph_revision": mission.revision,
                }
            )
            row = TaskRow(
                id=tid,
                project_id=mission.project_id,
                mission_id=mission.id,
                objective=task.objective,
                task_family=task.task_family,
                status="ready",
                graph_revision=mission.revision,
                priority=10 + i,
                scopes=list(task.scopes),
                dependency_ids=[],
                payload=task.model_dump(mode="json"),
            )
            self.session.add(row)
            tasks.append(row)
        self.session.flush()
        return mission, tasks

    def _enroll(self, *, project_id: str, host_alias: str) -> WorkerClient:
        client = WorkerClient(transport=self.transport)
        client.enroll(
            EnrollmentRequest(
                host_alias=host_alias,
                project_id=project_id,
                capabilities=["code.read", "chat"],
                trust_class="compute_only",
            )
        )
        return client

    def scenario_host_enrollment(self, *, clock: datetime) -> HarnessScenarioResult:
        name = "host_enrollment"
        try:
            mission, _ = self._seed_mission_with_tasks(n_tasks=0)
            a = self._enroll(project_id=mission.project_id, host_alias="host-a")
            b = self._enroll(project_id=mission.project_id, host_alias="host-b")
            assert a.worker_id and b.worker_id and a.worker_id != b.worker_id
            assert a.generation == 1 and b.generation == 1
            hb_a = a.heartbeat(health={"executor": "ready"})
            hb_b = b.heartbeat(health={"executor": "ready"})
            return HarnessScenarioResult(
                name=name,
                passed=True,
                details={
                    "workers": [a.worker_id, b.worker_id],
                    "statuses": [hb_a.status, hb_b.status],
                },
            )
        except Exception as exc:  # noqa: BLE001
            return HarnessScenarioResult(name=name, passed=False, error=str(exc))

    def scenario_dispatch_race(self, *, clock: datetime) -> HarnessScenarioResult:
        name = "dispatch_exactly_one_lease"
        try:
            mission, _ = self._seed_mission_with_tasks(n_tasks=1)
            a = self._enroll(project_id=mission.project_id, host_alias="race-a")
            b = self._enroll(project_id=mission.project_id, host_alias="race-b")
            ca = a.claim()
            cb = b.claim()
            winners = [c for c in (ca, cb) if c.claimed]
            losers = [c for c in (ca, cb) if not c.claimed]
            ok = len(winners) == 1 and len(losers) == 1
            return HarnessScenarioResult(
                name=name,
                passed=ok,
                details={
                    "winner_lease": winners[0].lease_id if winners else None,
                    "loser_claimed": False if losers else None,
                },
                error=None if ok else "expected_exactly_one_winner",
            )
        except Exception as exc:  # noqa: BLE001
            return HarnessScenarioResult(name=name, passed=False, error=str(exc))

    def scenario_worker_kill_expire_reassign(
        self, *, clock: datetime
    ) -> HarnessScenarioResult:
        name = "worker_kill_lease_expiry_reassignment"
        try:
            mission, _ = self._seed_mission_with_tasks(n_tasks=1)
            victim = self._enroll(project_id=mission.project_id, host_alias="victim")
            survivor = self._enroll(project_id=mission.project_id, host_alias="survivor")
            claimed = victim.claim()
            assert claimed.claimed and claimed.lease_id
            # Simulate kill: abandon client; do not renew. Server expires lease.
            expired = self.service.lifecycle.expire_leases(
                now=clock + timedelta(seconds=120)
            )
            assert claimed.lease_id in expired
            # Task returns to ready → survivor can claim new attempt/lease.
            reclaimed = survivor.claim()
            ok = (
                reclaimed.claimed
                and reclaimed.lease_id != claimed.lease_id
                and reclaimed.attempt_id != claimed.attempt_id
            )
            return HarnessScenarioResult(
                name=name,
                passed=ok,
                details={
                    "expired_lease": claimed.lease_id,
                    "new_lease": reclaimed.lease_id,
                    "new_attempt": reclaimed.attempt_id,
                },
                error=None if ok else "reassignment_failed",
            )
        except Exception as exc:  # noqa: BLE001
            return HarnessScenarioResult(name=name, passed=False, error=str(exc))

    def scenario_stale_result_rejected(self, *, clock: datetime) -> HarnessScenarioResult:
        name = "stale_result_after_reassignment_rejected"
        try:
            mission, _ = self._seed_mission_with_tasks(n_tasks=1)
            stale = self._enroll(project_id=mission.project_id, host_alias="stale-w")
            fresh = self._enroll(project_id=mission.project_id, host_alias="fresh-w")
            old = stale.claim()
            assert old.claimed and old.lease_id
            self.service.lifecycle.expire_leases(now=clock + timedelta(seconds=120))
            new = fresh.claim()
            assert new.claimed
            # Late result from killed worker — durable submit ok, accept must fail.
            submitted = stale.submit_result(
                lease_id=old.lease_id,
                status="succeeded",
                checks={"review_passed": True},
                summary="late",
            )
            rejected = False
            reason = None
            try:
                self.service.accept_result(
                    result_id=submitted.result_id, now=clock + timedelta(seconds=130)
                )
            except ResultAcceptanceError as exc:
                rejected = True
                reason = str(exc)
            ok = rejected and submitted.acceptance_state == "submitted"
            return HarnessScenarioResult(
                name=name,
                passed=ok,
                details={
                    "result_id": submitted.result_id,
                    "reject_reason": reason,
                    "fresh_lease": new.lease_id,
                },
                error=None if ok else "stale_result_was_accepted",
            )
        except Exception as exc:  # noqa: BLE001
            return HarnessScenarioResult(name=name, passed=False, error=str(exc))

    def scenario_drain(self, *, clock: datetime) -> HarnessScenarioResult:
        name = "drain_blocks_new_leases"
        try:
            mission, _ = self._seed_mission_with_tasks(n_tasks=2)
            worker = self._enroll(project_id=mission.project_id, host_alias="drain-w")
            first = worker.claim()
            assert first.claimed
            drained = worker.drain()
            blocked = False
            try:
                worker.claim()
            except WorkerNotEligibleError as exc:
                blocked = "draining" in str(exc) or "offline" in str(exc)
            ok = blocked and drained.status in {"draining", "offline"}
            return HarnessScenarioResult(
                name=name,
                passed=ok,
                details={
                    "drain_status": drained.status,
                    "active_leases": drained.active_lease_ids,
                },
                error=None if ok else "drain_did_not_block_claim",
            )
        except Exception as exc:  # noqa: BLE001
            return HarnessScenarioResult(name=name, passed=False, error=str(exc))

    def scenario_restart_recovery(self, *, clock: datetime) -> HarnessScenarioResult:
        name = "restart_reconnect_recovers_leases"
        try:
            mission, _ = self._seed_mission_with_tasks(n_tasks=1)
            worker = self._enroll(project_id=mission.project_id, host_alias="restart-w")
            assert worker.worker_id and worker.membership_token and worker.generation is not None
            claimed = worker.claim()
            assert claimed.claimed and claimed.lease_id
            # New process memory: credentials only.
            restarted = WorkerClient(
                transport=self.transport,
                worker_id=worker.worker_id,
                generation=worker.generation,
                membership_token=worker.membership_token,
                project_id=worker.project_id,
            )
            recovered = restarted.reconnect()
            ok = any(row["lease_id"] == claimed.lease_id for row in recovered.active_leases)
            return HarnessScenarioResult(
                name=name,
                passed=ok,
                details={
                    "recovered_leases": [r["lease_id"] for r in recovered.active_leases],
                    "expected": claimed.lease_id,
                },
                error=None if ok else "lease_not_reconstructed",
            )
        except Exception as exc:  # noqa: BLE001
            return HarnessScenarioResult(name=name, passed=False, error=str(exc))
