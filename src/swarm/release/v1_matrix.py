"""V1.0 real-world validation matrix."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.memory.store import run_interrupt_resume_proof
from swarm.observability.reliability import run_reliability_scenarios
from swarm.product.journey import run_product_journey
from swarm.release.contract_freeze import freeze_public_contracts
from swarm.release.demo_suite import run_public_demo_suite
from swarm.release.first_run import run_first_run
from swarm.release.harden import run_security_harden
from swarm.release.install import run_install_check
from swarm.release.verify import verify_release
from swarm.tools.permission_mission import run_permission_mission_sync


def run_v1_validation_matrix(repo: Path) -> dict[str, Any]:
    """Representative V1 matrix: coding UX, routing, recovery, permissions, reliability."""
    repo = repo.resolve()
    cells: list[dict[str, Any]] = []

    def add(name: str, ok: bool, **detail: Any) -> None:
        cells.append({"name": name, "ok": ok, "detail": detail})

    first = run_first_run(repo)
    add("first_run", first.ok, project_id=first.project_id)

    freeze = freeze_public_contracts(repo)
    add("contract_freeze", freeze.ok, hash=freeze.hash)

    inst = run_install_check(repo)
    add("install_check", inst.ok)

    hard = run_security_harden(repo)
    add("security_harden", hard.ok, findings=len(hard.findings))

    ver = verify_release(repo)
    add("release_verify", ver.passed, label=ver.label)

    journey = run_product_journey(repo)
    add(
        "product_journey",
        bool(journey.get("ok")),
        cost_usd=journey.get("cost_usd"),
        mission_id=journey.get("mission_id"),
    )

    perm = run_permission_mission_sync(repo)
    add("permission_gates", bool(perm.get("ok")), cost_usd=perm.get("cost_usd"))

    mem = run_interrupt_resume_proof(repo=repo, goal="Recover V1 validation interrupt")
    add("recovery_interrupt_resume", bool(mem.get("ok")), cost_usd=mem.get("cost_usd") or 0.0)

    rel = run_reliability_scenarios(repo=repo)
    add(
        "provider_failure_reliability",
        bool(rel.get("ok")),
        scenarios=list((rel.get("scenarios") or {}).keys()),
    )

    demo = run_public_demo_suite(repo)
    add("demo_suite", bool(demo.get("ok")), cost_usd=demo.get("cost_usd"))

    # Lightweight coding plan (real planner against repo) without full Ollama loop.
    from swarm.mission.planner import (
        build_software_mission,
        inspect_repo,
        plan_task_graph,
    )

    inspection = inspect_repo(repo)
    mission = build_software_mission(goal="Validate V1 coding plan against sandbox")
    proposal = plan_task_graph(mission, inspection)
    add(
        "coding_mission_plan",
        len(proposal.task_specs) >= 1,
        task_count=len(proposal.task_specs),
        mission_id=mission.id,
    )

    total_cost = 0.0
    for cell in cells:
        total_cost += float((cell.get("detail") or {}).get("cost_usd") or 0.0)

    report = {
        "schema_version": "1.0.0",
        "run_id": new_id("v1matrix_"),
        "generated_at": utc_now().isoformat(),
        "cells": cells,
        "ok": all(c["ok"] for c in cells),
        "cost_usd": total_cost,
        "spend_policy": "zero",
        "mock_vs_live": "v1_validation_matrix_local_zero_spend",
        "public_launch": False,
        "stop_gate": "awaiting_explicit_launch_approval",
    }
    raw = json.dumps({k: v for k, v in report.items() if k != "report_hash"}, sort_keys=True)
    report["report_hash"] = hashlib.sha256(raw.encode()).hexdigest()
    out = repo / "var" / "reports" / "v1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_validation_matrix.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
    )
    return report
