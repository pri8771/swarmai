"""V0.1 mission runtime orchestrator."""

from __future__ import annotations

import asyncio
import os
import threading
from pathlib import Path
from typing import Any

from swarm.broker.broker import SharedInferenceBroker
from swarm.contracts.common import utc_now
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.controller.mission import MissionController
from swarm.cost.ledger import CostEntry, CostLedger
from swarm.db.engine import create_db_engine, make_session_factory
from swarm.mission.action_boundary import local_worktree_gateway
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
from swarm.tools.effects import DurableEffectRepository, InMemoryEffectStore
from swarm.tools.fences import ActorContext, FenceProvider, RevocableFenceProvider
from swarm.tools.v17_gateway import ConsequentialToolGateway


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
        if os.environ.get("SWARM_DATABASE_URL"):
            self._effect_store: InMemoryEffectStore | DurableEffectRepository = (
                DurableEffectRepository(make_session_factory(create_db_engine()))
            )
        else:
            self._effect_store = InMemoryEffectStore()

    def _action_gateway_for(
        self, worktree: Path, *, fences: FenceProvider | None = None
    ) -> ConsequentialToolGateway:
        """Create the worker boundary for one isolated worktree handle."""
        return local_worktree_gateway(worktree, store=self._effect_store, fences=fences)

    @staticmethod
    async def _drain_worker_turn(turn: asyncio.Task[Any]) -> Any:
        """Wait for a shielded sync-worker thread even under repeated cancellation.

        ``asyncio.to_thread`` cannot terminate the underlying worker.  The
        runtime must therefore wait for it to quiesce before removing a
        worktree or returning cancellation to the caller.
        """
        while True:
            try:
                return await asyncio.shield(turn)
            except asyncio.CancelledError:
                if turn.cancelled():
                    raise
                continue

    def _mission_broker(self, *, models: list[str] | None = None) -> SharedInferenceBroker:
        if self._broker is None:
            # None => defaults + local Ollama inventory. Explicit list is an
            # allow-list that must include every model the worker will request.
            self._broker = build_local_mission_broker(
                repo_root=self.repo,
                models=models,
            )
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

        # One shared revocable fence reaches the initial gateway and every
        # per-worktree gateway.  Workers snapshot it at task start; a runtime
        # cancellation advances the generation and makes that snapshot stale.
        cancellation_event = threading.Event()
        revocable_fences = RevocableFenceProvider()

        def action_gateway_for(worktree: Path) -> ConsequentialToolGateway:
            return self._action_gateway_for(worktree, fences=revocable_fences)

        # Pass None so broker loads defaults + discovered local Ollama tags,
        # ensuring route coverage for evidence-router and --model selections.
        worker = RepoWorker(
            self.repo,
            model=default_model,
            model_by_family=model_by_family,
            broker=self._mission_broker(models=None),
            project_id=mission.project_id,
            action_gateway=action_gateway_for(self.repo),
            actor_context=ActorContext(
                actor="mission_runtime", project_id=mission.project_id
            ),
            action_gateway_factory=action_gateway_for,
            cancellation_event=cancellation_event,
            parser_dogfood_fixture=self.parser_dogfood_fixture,
            require_broker=True,
        )
        prior: dict[str, WorkerResult] = {}
        shared_wt: WorktreeHandle | None = None
        ledger = CostLedger(spend_policy="zero", allow_paid=False)
        accepted = False
        summary = "incomplete"
        worker_turn: asyncio.Task[Any] | None = None
        cancelled_turn_result: tuple[WorkerResult, WorktreeHandle | None] | None = None
        cancelled_turn_error: BaseException | None = None
        cancellation_requested = False
        terminal_error: Exception | None = None
        current_task_id: str | None = None

        def request_cancellation() -> None:
            nonlocal cancellation_requested
            if cancellation_requested:
                return
            cancellation_requested = True
            # Invalidate the task-frozen generation before making the worker
            # observe cancellation.  A worker already past its event check
            # then still presents a stale envelope at gateway admission.
            revocable_fences.cancel()
            cancellation_event.set()
            request_worker_cancellation = getattr(worker, "request_cancellation", None)
            if callable(request_worker_cancellation):
                request_worker_cancellation()
            self.store.append_timeline(
                record,
                "mission_cancellation_requested",
                {"task_id": current_task_id},
            )

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
                    # RepoWorker is deliberately synchronous because its local
                    # action gateway owns a synchronous entrypoint.  The
                    # mission orchestrator is async, so execute the serial
                    # worker turn off this loop rather than weakening the
                    # gateway's fail-closed running-loop guard.  Shielding
                    # prevents cancellation from abandoning the live thread;
                    # the cancellation handler drains it before cleanup.
                    current_task_id = task.id
                    worker_turn = asyncio.create_task(
                        asyncio.to_thread(
                            worker.run_task,
                            task,
                            mission_id=mission.id,
                            prior=prior,
                            shared_worktree=shared_wt,
                        )
                    )
                    try:
                        result, shared_wt = await asyncio.shield(worker_turn)
                    except asyncio.CancelledError:
                        request_cancellation()
                        try:
                            cancelled_turn_result = await self._drain_worker_turn(worker_turn)
                        except BaseException as exc:  # worker interruption is recorded below
                            cancelled_turn_error = exc
                        raise
                    finally:
                        if worker_turn is not None and worker_turn.done():
                            worker_turn = None
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
                            "action_receipt_ids": list(result.action_receipt_ids),
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
                "action_receipt_ids": sorted(
                    {
                        receipt_id
                        for worker_result in prior.values()
                        for receipt_id in worker_result.action_receipt_ids
                    }
                ),
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
            # G11: never auto-promote accepted worktree files into the primary
            # checkout. Return isolated worktree diff/artifacts; apply requires
            # an explicit reviewed action outside this path.
            if accepted and shared_wt is not None:
                record.artifacts["pending_apply"] = {
                    "status": "pending_explicit_apply",
                    "changed_files": changed,
                    "worktree": shared_wt.to_dict(),
                    "note": (
                        "accepted worktree changes are isolated; "
                        "automatic primary-checkout promotion is disabled"
                    ),
                }
                self.store.append_timeline(
                    record,
                    "apply_pending",
                    {"changed_files": changed, "auto_promote": False},
                )
            report_dir = self.repo / "var" / "reports" / "missions" / mission.id
            paths = write_reports(record, report_dir)
            record.artifacts["reports"] = paths
            self.store.append_timeline(record, "mission_finished", {"accepted": accepted})
            self.store.save(record)
            return record
        except asyncio.CancelledError:
            request_cancellation()
            raise
        except Exception as exc:
            terminal_error = exc
            raise
        finally:
            # A worker can create and bind a worktree before a gateway effect
            # raises. In that case run_task never returns its tuple, so retain
            # the worker's bound handle solely to remove the disposable tree.
            if cancelled_turn_result is not None:
                _, returned_worktree = cancelled_turn_result
                if returned_worktree is not None:
                    shared_wt = returned_worktree
            cleanup_wt = shared_wt or getattr(worker, "active_worktree", None)
            cleanup: dict[str, Any] = {
                "attempted": False,
                "completed": cleanup_wt is None,
                "deferred_worker_still_running": bool(
                    worker_turn is not None and not worker_turn.done()
                ),
                "error_type": None,
            }
            if cleanup_wt is not None and not cleanup["deferred_worker_still_running"]:
                cleanup["attempted"] = True
                try:
                    remove_worktree(self.repo, cleanup_wt, force=True)
                    cleanup["completed"] = not cleanup_wt.path.exists()
                except Exception as exc:  # noqa: BLE001 - terminal record is still required
                    cleanup["error_type"] = type(exc).__name__

            if cancellation_requested or terminal_error is not None:
                receipt_ids = {
                    receipt_id
                    for worker_result in prior.values()
                    for receipt_id in worker_result.action_receipt_ids
                }
                if cancelled_turn_result is not None:
                    receipt_ids.update(cancelled_turn_result[0].action_receipt_ids)
                active_receipts = getattr(worker, "active_action_receipt_ids", [])
                receipt_ids.update(str(receipt_id) for receipt_id in active_receipts)

                interrupted = cancellation_requested
                if interrupted:
                    for row in record.tasks:
                        if row["id"] == current_task_id or row.get("status") in {
                            TaskStatus.READY.value,
                            TaskStatus.RUNNING.value,
                            TaskStatus.WAITING_CAPACITY.value,
                            TaskStatus.WAITING_APPROVAL.value,
                        }:
                            row["status"] = TaskStatus.CANCELLED.value
                            row["ok"] = False
                            row["summary"] = "runtime_cancelled"
                    self.store.append_timeline(
                        record,
                        "mission_worker_quiesced",
                        {
                            "task_id": current_task_id,
                            "turn_result_available": cancelled_turn_result is not None,
                            "turn_error_type": (
                                type(cancelled_turn_error).__name__
                                if cancelled_turn_error is not None
                                else None
                            ),
                        },
                    )

                record.status = (
                    MissionStatus.CANCELLED.value if interrupted else MissionStatus.FAILED.value
                )
                record.validation = {
                    "accepted": False,
                    "interrupted": interrupted,
                    "error_type": (
                        type(cancelled_turn_error).__name__
                        if interrupted and cancelled_turn_error is not None
                        else type(terminal_error).__name__ if terminal_error is not None else None
                    ),
                }
                record.result = {
                    "accepted": False,
                    "summary": "mission_cancelled" if interrupted else "mission_exception",
                    "worktree": cleanup_wt.to_dict() if cleanup_wt else None,
                    "action_receipt_ids": sorted(receipt_ids),
                    "current_task_id": current_task_id,
                    "cleanup": cleanup,
                    "cost_accounting": "partial_or_unknown" if interrupted else "failed",
                }
                record.cost = {**ledger.to_dict(), "requests": len(ledger.entries)}
                record.artifacts = {
                    "worker_results": {k: v.to_dict() for k, v in prior.items()},
                }
                if cancelled_turn_result is not None:
                    record.artifacts["interrupted_worker_result"] = (
                        cancelled_turn_result[0].to_dict()
                    )
                self.store.append_timeline(
                    record,
                    "mission_cleanup_finished",
                    dict(cleanup),
                )
                self.store.save(record)

    def apply_worktree_changes(
        self,
        handle: WorktreeHandle,
        changed_files: list[str],
        *,
        approved: bool,
    ) -> list[str]:
        """Explicit reviewed apply into the primary checkout — never automatic."""
        if not approved:
            raise PermissionError("explicit_apply_requires_approved_true")
        applied: list[str] = []
        for rel in changed_files:
            src = handle.path / rel
            dst = self.repo / rel
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                applied.append(rel)
        return applied

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
