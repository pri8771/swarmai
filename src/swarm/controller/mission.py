"""MissionController — planning, validation, verification, completion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import new_id
from swarm.contracts.enums import GraphOperation, MissionStatus, TaskStatus
from swarm.contracts.mission import GraphProposal, Mission, TaskAttempt, TaskSpec
from swarm.controller.graph import validate_proposal
from swarm.controller.scheduler import AdaptiveScheduler
from swarm.evals.profiles import ProfileStore


@dataclass
class MissionController:
    profiles: ProfileStore = field(default_factory=ProfileStore)
    scheduler: AdaptiveScheduler | None = None
    missions: dict[str, Mission] = field(default_factory=dict)
    tasks: dict[str, dict[str, TaskSpec]] = field(default_factory=dict)
    proposals: dict[str, GraphProposal] = field(default_factory=dict)
    attempts: dict[str, TaskAttempt] = field(default_factory=dict)
    verifications: dict[str, str] = field(default_factory=dict)
    graph_explanations: list[dict[str, Any]] = field(default_factory=list)
    inference_slots: int = 4
    worker_slots: int = 4

    def __post_init__(self) -> None:
        if self.scheduler is None:
            self.scheduler = AdaptiveScheduler(self.profiles)

    async def submit_mission(self, mission: Mission) -> Mission:
        mission = mission.model_copy(update={"status": MissionStatus.PLANNING})
        self.missions[mission.id] = mission
        self.tasks.setdefault(mission.id, {})
        return mission

    async def propose_graph_change(self, proposal: GraphProposal) -> GraphProposal:
        self.proposals[proposal.proposal_id] = proposal
        return proposal

    async def commit_validated_revision(self, proposal_id: str) -> int:
        proposal = self.proposals[proposal_id]
        mission = self.missions[proposal.mission_id]
        task_map = self.tasks.setdefault(mission.id, {})
        result = validate_proposal(
            proposal,
            tasks=task_map,
            mission_revision=mission.revision,
            mission_scopes=set(mission.data_scope_ids),
            max_graph_nodes=mission.max_graph_nodes,
        )
        explanation = {
            "proposal_id": proposal_id,
            "operation": proposal.operation.value,
            "accepted": result.accepted,
            "reason": result.reason,
            "merged_into": result.merged_into,
        }
        self.graph_explanations.append(explanation)
        if not result.accepted:
            if result.merged_into:
                return mission.revision
            raise ValueError(result.reason)

        if proposal.operation in {GraphOperation.SPAWN, GraphOperation.SPLIT}:
            for spec in proposal.task_specs:
                ready = spec.model_copy(update={"status": TaskStatus.READY})
                task_map[ready.id] = ready
        elif proposal.operation == GraphOperation.MERGE and result.merged_into:
            pass
        elif proposal.operation == GraphOperation.STOP:
            mission = mission.model_copy(update={"status": MissionStatus.CANCELLED})
            self.missions[mission.id] = mission
            return mission.revision

        mission = mission.model_copy(
            update={
                "revision": mission.revision + 1,
                "status": MissionStatus.RUNNING,
            }
        )
        self.missions[mission.id] = mission
        return mission.revision

    async def choose_ready_work(self, mission_id: str) -> list[TaskSpec]:
        assert self.scheduler is not None
        mission = self.missions[mission_id]
        tasks = list(self.tasks.get(mission_id, {}).values())
        # Resolve dependency readiness.
        ready_tasks: list[TaskSpec] = []
        for t in tasks:
            if t.status != TaskStatus.READY:
                # Also promote PROPOSED with satisfied deps.
                if t.status != TaskStatus.PROPOSED:
                    continue
            deps_ok = True
            for dep in t.dependency_ids:
                parent = self.tasks[mission_id].get(dep)
                if parent is None or parent.status not in {
                    TaskStatus.ACCEPTED,
                    TaskStatus.VERIFYING,
                }:
                    # Allow missing dep as not ready.
                    if parent is None or parent.status not in {
                        TaskStatus.ACCEPTED,
                    }:
                        deps_ok = False
                        break
            if deps_ok:
                if t.status == TaskStatus.PROPOSED:
                    t = t.model_copy(update={"status": TaskStatus.READY})
                    self.tasks[mission_id][t.id] = t
                ready_tasks.append(t)

        selected, explanation = self.scheduler.choose_ready(
            mission,
            ready_tasks,
            inference_slots=self.inference_slots,
            worker_slots=self.worker_slots,
            privacy_ok=True,
        )
        self.graph_explanations.append({"type": "schedule", **explanation})
        return selected

    async def record_verification(self, attempt_id: str, receipt_id: str) -> None:
        self.verifications[attempt_id] = receipt_id
        attempt = self.attempts.get(attempt_id)
        if attempt is None:
            return
        attempt = attempt.model_copy(update={"verification_receipt_id": receipt_id})
        self.attempts[attempt_id] = attempt
        # Mark task accepted only with verification.
        for mission_tasks in self.tasks.values():
            if attempt.task_id in mission_tasks:
                task = mission_tasks[attempt.task_id]
                mission_tasks[attempt.task_id] = task.model_copy(
                    update={"status": TaskStatus.ACCEPTED}
                )

    async def reconcile_leases(self, mission_id: str) -> None:
        # Placeholder for worker lease reconciliation hook (P12).
        _ = mission_id
        return None

    def register_attempt(self, attempt: TaskAttempt) -> None:
        self.attempts[attempt.attempt_id] = attempt

    def try_complete(self, mission_id: str) -> Mission:
        mission = self.missions[mission_id]
        tasks = list(self.tasks.get(mission_id, {}).values())
        if not tasks:
            return mission
        # Failing verification prevents completion.
        for t in tasks:
            if t.status in {TaskStatus.FAILED, TaskStatus.REJECTED}:
                return mission.model_copy(update={"status": MissionStatus.FAILED})
            if t.status not in {
                TaskStatus.ACCEPTED,
                TaskStatus.CANCELLED,
                TaskStatus.SUPERSEDED,
            }:
                return mission
            # Accepted tasks must have verification on some attempt.
            verified = any(
                a.task_id == t.id and a.verification_receipt_id
                for a in self.attempts.values()
            )
            if t.status == TaskStatus.ACCEPTED and not verified:
                return mission
        completed = mission.model_copy(
            update={"status": MissionStatus.COMPLETED, "acceptance_receipt_id": new_id("ar_")}
        )
        self.missions[mission_id] = completed
        return completed

    def expand_capacity(self, inference: int, workers: int) -> None:
        self.inference_slots = inference
        self.worker_slots = workers

    def note_inference_exhaustion(self) -> None:
        assert self.scheduler is not None
        self.scheduler.note_overload()


def spawn_proposal(
    mission: Mission,
    *,
    author_session_id: str,
    parent: TaskSpec | None,
    children: list[TaskSpec],
) -> GraphProposal:
    return GraphProposal(
        project_id=mission.project_id,
        mission_id=mission.id,
        based_on_revision=mission.revision,
        author_session_id=author_session_id,
        operation=GraphOperation.SPAWN,
        rationale_summary="spawn subproblems",
        task_specs=children,
    )
