"""Operational pursuit executor — durable native mission dispatch (R20-01).

Never synthesizes achievement. Admits a RUNNING mission under ``var/missions/``
and returns a pending outcome until protected verification accepts an artifact.
An optional bounded native loop (V20-E05) may run model/tool turns; its result is
recorded on the mission but never turns the outcome into success.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import MissionStatus
from swarm.contracts.fixtures import sample_task
from swarm.contracts.mission import Mission
from swarm.pursuit.models import ExecutionOutcome, MissionProposalDraft
from swarm.pursuit.native_loop import BoundedNativeLoop, LoopResult, native_loop_from_env
from swarm.pursuit.verification import (
    artifact_digest_for_refs,
    issue_criterion_receipt,
)

if TYPE_CHECKING:
    from swarm.api.store import ProductStore

PROVENANCE = "pursuit_native_dispatch"
SOURCE = "pursuit_native"


class NativeMissionDispatchExecutor:
    """Dispatch real durable missions for operational pursuit.

    ``RecordingExecutor`` remains available only for explicit fixture/mock demos.
    """

    def __init__(
        self,
        store: ProductStore,
        *,
        enqueue_worker_task: bool = True,
        native_loop: BoundedNativeLoop | None = None,
    ) -> None:
        self.store = store
        self.enqueue_worker_task = enqueue_worker_task
        self.native_loop = native_loop
        self.loop_blocker: str | None = None
        if native_loop is None:
            # No LiveGrant is ever invented here, so this reports the honest blocker.
            _, self.loop_blocker = native_loop_from_env({}, grant=None)

    def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome:
        mission_id = proposal.mission_id or new_id("msn_")
        project_id = self._project_id(proposal.goal_id)
        mission = Mission(
            id=mission_id,
            project_id=project_id,
            objective=proposal.objective,
            acceptance_criteria=list(proposal.addresses_criteria),
            allowed_capabilities=list(proposal.admitted_tools) or ["workspace.read"],
            data_scope_ids=[f"scope_{project_id}"],
            resource_policy_id="policy_pursuit_native",
            max_wall_time_seconds=3600,
            max_graph_nodes=50,
            max_active_sessions=4,
            max_model_calls=50,
            status=MissionStatus.RUNNING,
        )
        self.store.controller.missions[mission.id] = mission
        self.store._persist_mission_record(mission, source=SOURCE)
        record = self.store.mission_store().load(mission.id)
        plan = dict(record.plan or {})
        plan.update(
            {
                "project_id": project_id,
                "goal_id": proposal.goal_id,
                "proposal_id": proposal.proposal_id,
                "dedupe_key": proposal.dedupe_key,
                "runtime": "native",
                "addresses_criteria": list(proposal.addresses_criteria),
                "admitted_tools": list(proposal.admitted_tools),
                "admitted_providers": list(proposal.admitted_providers),
                "provenance": PROVENANCE,
                "task_family": "extract",
            }
        )
        record.plan = plan
        record.source = SOURCE
        record.status = MissionStatus.RUNNING.value
        self.store.mission_store().append_timeline(
            record,
            "mission.created",
            {"source": SOURCE, "provenance": PROVENANCE, "goal_id": proposal.goal_id},
        )
        self.store.mission_store().save(record)

        try:
            self.store.goal_store().link_mission(proposal.goal_id, mission.id)
        except KeyError:
            pass

        if self.enqueue_worker_task:
            self._enqueue_task(mission_id=mission.id, project_id=project_id, proposal=proposal)

        loop_result = self._run_native_loop(mission.id, proposal)

        self.store.publish(
            project_id=project_id,
            type="mission.created",
            actor="pursuit",
            mission_id=mission.id,
            payload={"source": SOURCE, "provenance": PROVENANCE, "status": "running"},
            dedupe_key=f"mission.created:{mission.id}",
        )

        routes = [r.route_id for r in loop_result.receipts if r.route_id] if loop_result else []
        return ExecutionOutcome(
            mission_id=mission.id,
            success=False,
            failure_class="submitted_pending",
            notes="native_mission_dispatched_awaiting_worker_and_protected_verify",
            cost_usd=0.0,
            model_calls=loop_result.model_calls if loop_result else 0,
            tool_calls=loop_result.tool_calls if loop_result else 0,
            route_id=routes[0] if routes else None,
            runtime="native",
            usage_unknown=loop_result is not None
            and loop_result.model_calls > 0
            and not loop_result.usage_known,
        )

    def _run_native_loop(
        self, mission_id: str, proposal: MissionProposalDraft
    ) -> LoopResult | None:
        result: LoopResult | None = None
        if self.native_loop is None:
            summary: dict[str, Any] = {"status": "blocked", "reason": self.loop_blocker}
        else:
            result = self.native_loop.run(proposal.objective)
            summary = result.summary()
        record = self.store.mission_store().load(mission_id)
        plan = dict(record.plan or {})
        plan["native_loop"] = summary
        record.plan = plan
        self.store.mission_store().append_timeline(
            record, f"native_loop.{summary['status']}", dict(summary)
        )
        self.store.mission_store().save(record)
        return result

    def reconcile(self, mission_id: str) -> ExecutionOutcome | None:
        """Return terminal outcome when mission completed/failed; else None (still pending)."""
        path = self.store.mission_store()._path(mission_id)
        if not path.exists():
            return ExecutionOutcome(
                mission_id=mission_id,
                success=False,
                failure_class="mission_missing",
                runtime="native",
            )
        record = self.store.mission_store().load(mission_id)
        status = (record.status or "").lower()
        validation = dict(record.validation or {})
        protected = validation.get("protected_verify") or {}
        result = dict(record.result or {})
        usage = self._recorded_loop_usage(record.plan)
        receipt_id = result.get("acceptance_receipt_id")
        if not receipt_id:
            mission = self.store.controller.missions.get(mission_id)
            if mission is not None:
                receipt_id = mission.acceptance_receipt_id

        if status in {"failed", "cancelled"}:
            return ExecutionOutcome(
                mission_id=mission_id,
                success=False,
                failure_class=f"mission_{status}",
                notes=str((record.result or {}).get("summary") or status),
                runtime="native",
                **usage,
            )

        if (
            status == "completed"
            and receipt_id
            and isinstance(protected, dict)
            and protected.get("accepted") is True
        ):
            plan = dict(record.plan or {})
            criteria = list(plan.get("addresses_criteria") or [])
            goal_id = str(plan.get("goal_id") or "")
            content_hash = str(protected.get("content_hash") or "")
            artifact_id = str(protected.get("artifact_id") or "")
            evidence_refs = [f"art:{artifact_id}"] if artifact_id else [f"acr:{receipt_id}"]
            digest = content_hash or artifact_digest_for_refs(
                evidence_refs, mission_id=mission_id
            )
            receipts: list[dict[str, Any]] = []
            for criterion_id in criteria:
                if not goal_id:
                    break
                receipt = issue_criterion_receipt(
                    goal_id=goal_id,
                    criterion_id=criterion_id,
                    mission_id=mission_id,
                    artifact_digest=digest,
                    evidence_ref=evidence_refs[0],
                )
                receipts.append(receipt.model_dump(mode="json"))
            return ExecutionOutcome(
                mission_id=mission_id,
                success=True,
                evidence_refs=evidence_refs,
                satisfied_criteria=list(criteria),
                criterion_receipts=receipts,
                notes=f"protected_verify_accepted:{receipt_id}",
                cost_usd=0.0,
                runtime="native",
                **usage,
            )

        # Still awaiting worker execution / protected verify.
        return None

    @staticmethod
    def _recorded_loop_usage(plan: dict[str, Any] | None) -> dict[str, Any]:
        summary = dict((plan or {}).get("native_loop") or {})
        model_calls = max(0, int(summary.get("model_calls") or 0))
        return {
            "model_calls": model_calls,
            "tool_calls": max(0, int(summary.get("tool_calls") or 0)),
            "prompt_tokens": summary.get("prompt_tokens"),
            "completion_tokens": summary.get("completion_tokens"),
            "usage_unknown": model_calls > 0 and summary.get("usage_known") is not True,
        }

    def _project_id(self, goal_id: str) -> str:
        try:
            return str(self.store.goal_store().get(goal_id).project_id)
        except KeyError:
            return "proj_unknown"

    def _enqueue_task(
        self,
        *,
        mission_id: str,
        project_id: str,
        proposal: MissionProposalDraft,
    ) -> None:
        task = sample_task(mission_id=mission_id).model_copy(
            update={
                "id": new_id("tsk_"),
                "project_id": project_id,
                "objective": proposal.objective,
                "task_family": "extract",
                "required_capabilities": ["extract"],
                "scopes": ["local"],
                "inputs": {
                    "goal_id": proposal.goal_id,
                    "proposal_id": proposal.proposal_id,
                    "addresses_criteria": list(proposal.addresses_criteria),
                    "dispatched_at": utc_now().isoformat(),
                },
            }
        )
        self.store.workers.enqueue(task)
        record = self.store.mission_store().load(mission_id)
        tasks = list(record.tasks or [])
        tasks.append(task.model_dump(mode="json"))
        record.tasks = tasks
        self.store.mission_store().append_timeline(
            record,
            "task.enqueued",
            {"task_id": task.id, "required_capabilities": list(task.required_capabilities)},
        )
        self.store.mission_store().save(record)


class BlockedMissingImplementationExecutor:
    """Honest blocker when no native dispatch is wired (no synthetic success).

    Used as ``PursuitEngine`` default when callers omit an executor. Operational
    ProductStore must prefer ``NativeMissionDispatchExecutor`` instead.
    """

    def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome:
        mission_id = proposal.mission_id or new_id("msn_")
        return ExecutionOutcome(
            mission_id=mission_id,
            success=False,
            failure_class="blocked_missing_implementation",
            notes="operational_pursuit_requires_native_dispatch",
            evidence_refs=[],
            satisfied_criteria=[],
            criterion_receipts=[],
            cost_usd=0.0,
            model_calls=0,
            tool_calls=0,
            runtime="blocked",
        )
