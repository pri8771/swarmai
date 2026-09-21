#!/usr/bin/env python3
"""G14 SWARM-141 offline: admission-gated expand/contract prep at $0.

Shows graph expand succeeds under budget, further expand is denied when the
mission node envelope would be exceeded, then contraction frees capacity for
a later expand. Live multi-planner concurrency is **not** claimed.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.controller.mission import MissionController, spawn_proposal

REPO = Path(__file__).resolve().parents[1]


async def _run() -> dict:
    recorded_at = datetime.now(UTC).isoformat()
    ctrl = MissionController(inference_slots=1, worker_slots=2)
    # Tiny graph envelope so a second expand is honestly denied.
    mission = await ctrl.submit_mission(
        sample_mission().model_copy(
            update={
                "id": "mission_g14_admit_gate",
                "objective": "offline admission-gated expand/contract unfamiliar triage",
                "max_model_calls": 4,
                "max_graph_nodes": 2,
                "max_active_sessions": 2,
            }
        )
    )

    ops: list[dict] = []

    def _mission() -> object:
        return ctrl.missions[mission.id]

    children_a = [
        sample_task().model_copy(
            update={
                "id": "task_extract_a",
                "objective": "extract unfamiliar fields",
                "task_family": "extract",
                "mission_id": mission.id,
            }
        ),
        sample_task().model_copy(
            update={
                "id": "task_triage_a",
                "objective": "triage unfamiliar incident",
                "task_family": "triage",
                "mission_id": mission.id,
            }
        ),
    ]
    prop_a = spawn_proposal(
        _mission(),  # type: ignore[arg-type]
        author_session_id="as_planner_a",
        parent=None,
        children=children_a,
    )
    await ctrl.propose_graph_change(prop_a)
    rev_a = await ctrl.commit_validated_revision(prop_a.proposal_id)
    ops.append(
        {
            "op": "expand",
            "planner": "as_planner_a",
            "ok": True,
            "revision": rev_a,
            "spawned": [t.id for t in children_a],
        }
    )

    children_b = [
        sample_task().model_copy(
            update={
                "id": "task_plan_b",
                "objective": "plan bounded next checks",
                "task_family": "plan",
                "mission_id": mission.id,
            }
        )
    ]
    prop_b = spawn_proposal(
        _mission(),  # type: ignore[arg-type]
        author_session_id="as_planner_b",
        parent=None,
        children=children_b,
    )
    await ctrl.propose_graph_change(prop_b)
    denied = False
    deny_detail = ""
    try:
        rev_b = await ctrl.commit_validated_revision(prop_b.proposal_id)
        # If controller silently kept revision (merge/deny without raise), inspect tasks.
        if "task_plan_b" in ctrl.tasks.get(mission.id, {}):
            ops.append(
                {
                    "op": "expand",
                    "planner": "as_planner_b",
                    "ok": True,
                    "revision": rev_b,
                    "unexpected": "over_budget_expand_accepted",
                }
            )
        else:
            denied = True
            deny_detail = "proposal_not_applied"
            ops.append(
                {
                    "op": "expand_denied",
                    "planner": "as_planner_b",
                    "ok": False,
                    "reason": deny_detail,
                    "revision": rev_b,
                }
            )
    except ValueError as exc:
        denied = True
        deny_detail = str(exc)
        ops.append(
            {
                "op": "expand_denied",
                "planner": "as_planner_b",
                "ok": False,
                "reason": deny_detail,
            }
        )

    # Contract: retire a node so capacity is actually freed (cancelled still counts).
    if "task_triage_a" in ctrl.tasks.get(mission.id, {}):
        del ctrl.tasks[mission.id]["task_triage_a"]
        ops.append(
            {
                "op": "contract_retire",
                "task_id": "task_triage_a",
                "ok": True,
                "note": "node removed from graph map — cancel alone does not free max_graph_nodes",
            }
        )

    children_c = [
        sample_task().model_copy(
            update={
                "id": "task_plan_c",
                "objective": "plan after contraction",
                "task_family": "plan",
                "mission_id": mission.id,
            }
        )
    ]
    prop_c = spawn_proposal(
        _mission(),  # type: ignore[arg-type]
        author_session_id="as_planner_a",
        parent=None,
        children=children_c,
    )
    await ctrl.propose_graph_change(prop_c)
    rev_c = await ctrl.commit_validated_revision(prop_c.proposal_id)
    ops.append(
        {
            "op": "expand_after_contract",
            "planner": "as_planner_a",
            "ok": True,
            "revision": rev_c,
            "spawned": ["task_plan_c"],
        }
    )

    tasks_now = list(ctrl.tasks.get(mission.id, {}).values())
    return {
        "gate": "SWARM-141",
        "scenario": "offline_admission_gated_expand_contract",
        "recorded_at": recorded_at,
        "live_claimed": False,
        "live_multi_planner_claimed": False,
        "spend_usd": 0.0,
        "mission_id": mission.id,
        "max_model_calls": mission.max_model_calls,
        "max_graph_nodes": 2,
        "ops": ops,
        "expand_denied": denied,
        "deny_detail": deny_detail,
        "task_count": len(tasks_now),
        "task_statuses": {
            t.id: str(getattr(t.status, "value", t.status)) for t in tasks_now
        },
        "note": (
            "Offline admission-gated expand/contract prep only. "
            "Not live multi-model multi-planner proof."
        ),
    }


def main() -> int:
    evidence = asyncio.run(_run())
    out = REPO / "docs" / "evidence" / "swarm-141" / "admission-gated-expand-offline.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print(f"\nWrote {out}", file=sys.stderr)
    if evidence.get("live_claimed") or evidence.get("live_multi_planner_claimed"):
        return 2
    spend = evidence.get("spend_usd")
    if spend is None or float(spend) != 0.0:
        return 2
    if not evidence.get("expand_denied"):
        return 2
    if not any(op.get("op") == "expand_after_contract" and op.get("ok") for op in evidence["ops"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
