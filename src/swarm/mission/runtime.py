"""V0.1 mission runtime orchestrator."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from swarm.broker.broker import SharedInferenceBroker
from swarm.contracts.common import utc_now
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.controller.mission import MissionController
from swarm.cost.ledger import CostEntry, CostLedger
from swarm.mission.brokered_inference import build_local_mission_broker
from swarm.mission.planner import (
    build_software_mission,
    inspect_repo,
    plan_task_graph,
)
from swarm.mission.report import live_state_view, write_reports
from swarm.mission.store import MissionRecord, MissionStore
from swarm.mission.worker import RepoWorker, WorkerResult
from swarm.mission.worktree import WorktreeHandle, remove_worktree


class MissionRuntime:
    def __init__(
        self,
        repo: Path,
        *,
        store_dir: Path | None = None,
        model: str = "gemma3:4b",
        max_repair_rounds: int = 2,
        use_evidence_router: bool = True,
        parser_dogfood_fixture: bool = False,
    ) -> None:
        self.repo = repo.resolve()
        self.store = MissionStore(store_dir or (self.repo / "var" / "missions"))
        self.model = model
        self.max_repair_rounds = max_repair_rounds
        self.use_evidence_router = use_evidence_router
        self.parser_dogfood_fixture = parser_dogfood_fixture
        self.controller = MissionController(inference_slots=2, worker_slots=2)
        self._broker: SharedInferenceBroker | None = None

    def _mission_broker(self) -> SharedInferenceBroker:
        if self._broker is None:
            self._broker = build_local_mission_broker(repo_root=self.repo)
        return self._broker

    async def run(self, goal: str) -> MissionRecord:
        from swarm.evals.evidence_router import build_mission_route_plan, save_route_plan

        inspection = inspect_repo(self.repo)
        mission = build_software_mission(goal=goal)
        mission = await self.controller.submit_mission(mission)
        proposal = plan_task_graph(mission, inspection)
        await self.controller.propose_graph_change(proposal)
        revision = await self.controller.commit_validated_revision(proposal.proposal_id)

        route_plan = None
        model_by_family: dict[str, str] = {}
        if self.use_evidence_router:
            route_plan = build_mission_route_plan(repo=self.repo)
            save_route_plan(route_plan, repo=self.repo)
            model_by_family = {
                fam: assignment.model
                for fam, assignment in route_plan.assignments.items()
            }
        default_model = (
            model_by_family.get("implement")
            or model_by_family.get("inspect")
            or self.model
        )

        record = MissionRecord(
            mission_id=mission.id,
            goal=goal,
            status=MissionStatus.RUNNING.value,
            created_at=utc_now().isoformat(),
            updated_at=utc_now().isoformat(),
            revision=revision,
            plan={
                "proposal_id": proposal.proposal_id,
                "operation": proposal.operation.value,
                "rationale": proposal.rationale_summary,
                "inspection": inspection.to_dict(),
                "task_ids": [t.id for t in proposal.task_specs],
                "route_plan": route_plan.to_dict() if route_plan else None,
            },
            tasks=[
                {
                    "id": t.id,
                    "task_family": t.task_family,
                    "objective": t.objective,
                    "dependency_ids": t.dependency_ids,
                    "status": TaskStatus.READY.value,
                    "ok": None,
                    "assigned_model": model_by_family.get(t.task_family, default_model),
                }
                for t in proposal.task_specs
            ],
            cost={"spend_policy": "zero", "allow_paid": False, "total_usd": 0.0, "requests": 0},
        )
        self.store.append_timeline(
            record,
            "mission_started",
            {
                "revision": revision,
                "model": default_model,
                "route_plan": route_plan.to_dict() if route_plan else None,
            },
        )
        self.store.save(record)

        worker = RepoWorker(
            self.repo,
            model=default_model,
            model_by_family=model_by_family,
            broker=self._mission_broker(),
            project_id=mission.project_id,
            parser_dogfood_fixture=self.parser_dogfood_fixture,
        )
        prior: dict[str, WorkerResult] = {}
        shared_wt: WorktreeHandle | None = None
        ledger = CostLedger(spend_policy="zero", allow_paid=False)
        accepted = False
        summary = "incomplete"

        try:
            for round_idx in range(self.max_repair_rounds + 1):
                self.store.append_timeline(
                    record, "execution_round", {"round": round_idx}
                )
                # Dependency order from planner: inspect → implement → verify → review
                ordered = sorted(
                    self.controller.tasks[mission.id].values(),
                    key=lambda t: t.priority,
                )
                round_ok = True
                for task in ordered:
                    # Skip already-accepted inspect on repair rounds; re-run implement+.
                    if round_idx > 0 and task.task_family == "inspect":
                        continue
                    if round_idx > 0 and task.task_family == "implement":
                        # Force re-implement after failed verify/review.
                        pass
                    result, shared_wt = worker.run_task(
                        task,
                        mission_id=mission.id,
                        prior=prior,
                        shared_worktree=shared_wt,
                    )
                    prior[task.id] = result
                    self.store.append_timeline(
                        record,
                        "task_finished",
                        {
                            "task_id": task.id,
                            "family": task.task_family,
                            "ok": result.ok,
                            "summary": result.summary,
                            "worker_id": result.worker_id,
                        },
                    )
                    record.agents.append(
                        {
                            "worker_id": result.worker_id,
                            "task_id": task.id,
                            "family": task.task_family,
                        }
                    )
                    if result.inference:
                        record.model_assignments.append(
                            {
                                "task_id": task.id,
                                "route_id": result.inference.get("route_id"),
                                "model": result.inference.get("model"),
                            }
                        )
                        ledger.add(
                            CostEntry(
                                source=task.id,
                                route_id=result.inference.get("route_id"),
                                model=result.inference.get("model"),
                                requests=1,
                                prompt_tokens=result.inference.get("prompt_tokens"),
                                completion_tokens=result.inference.get(
                                    "completion_tokens"
                                ),
                                cost_usd=float(result.inference.get("cost_usd") or 0.0),
                            )
                        )
                    for row in record.tasks:
                        if row["id"] == task.id:
                            row["status"] = (
                                TaskStatus.ACCEPTED.value
                                if result.ok
                                else TaskStatus.FAILED.value
                            )
                            row["ok"] = result.ok
                            row["summary"] = result.summary
                    if not result.ok:
                        round_ok = False
                        record.retries.append(
                            {
                                "round": round_idx,
                                "task_id": task.id,
                                "family": task.task_family,
                                "reason": result.summary,
                            }
                        )
                        # Continue to collect evidence; repair on next round.
                        if task.task_family in {"verify", "review"}:
                            break
                review = next(
                    (r for r in prior.values() if r.task_family == "review"), None
                )
                if round_ok and review and review.ok:
                    accepted = True
                    summary = "mission_accepted"
                    break
                summary = "repair_required"
                self.store.append_timeline(
                    record, "repair_scheduled", {"round": round_idx + 1}
                )
                # Reset implement/verify/review statuses for next attempt.
                for row in record.tasks:
                    if row.get("task_family") in {"implement", "verify", "review"}:
                        row["status"] = TaskStatus.READY.value
                        row["ok"] = None

            review_task = next((t for t in ordered if t.task_family == "review"), None)
            review_result = prior.get(review_task.id) if review_task else None
            record.validation = {
                "accepted": accepted,
                "review": review_result.to_dict() if review_result else None,
            }
            changed = []
            implement = next(
                (r for r in prior.values() if r.task_family == "implement"), None
            )
            if implement:
                changed = list(implement.artifacts.get("changed_files") or [])
            record.result = {
                "accepted": accepted,
                "summary": summary,
                "changed_files": changed,
                "worktree": shared_wt.to_dict() if shared_wt else None,
            }
            record.status = (
                MissionStatus.COMPLETED.value if accepted else MissionStatus.FAILED.value
            )
            record.cost = {
                **ledger.to_dict(),
                "requests": len(ledger.entries),
            }
            record.artifacts = {
                "worker_results": {k: v.to_dict() for k, v in prior.items()},
            }
            # Promote accepted worktree changes into the primary checkout for dogfood proof.
            if accepted and shared_wt is not None:
                self._promote_changes(shared_wt, changed)
            report_dir = self.repo / "var" / "reports" / "missions" / mission.id
            paths = write_reports(record, report_dir)
            record.artifacts["reports"] = paths
            self.store.append_timeline(record, "mission_finished", {"accepted": accepted})
            self.store.save(record)
            return record
        finally:
            if shared_wt is not None:
                try:
                    remove_worktree(self.repo, shared_wt, force=True)
                except Exception:  # noqa: BLE001
                    pass

    def _promote_changes(self, handle: WorktreeHandle, changed_files: list[str]) -> None:
        for rel in changed_files:
            src = handle.path / rel
            dst = self.repo / rel
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def status(self, mission_id: str) -> dict[str, Any]:
        record = self.store.load(mission_id)
        return live_state_view(record)


def run_mission(
    goal: str,
    *,
    repo: Path,
    model: str = "gemma3:4b",
    store_dir: Path | None = None,
    use_evidence_router: bool = True,
    parser_dogfood_fixture: bool = False,
) -> MissionRecord:
    runtime = MissionRuntime(
        repo,
        store_dir=store_dir,
        model=model,
        use_evidence_router=use_evidence_router,
        parser_dogfood_fixture=parser_dogfood_fixture,
    )
    return asyncio.run(runtime.run(goal))
