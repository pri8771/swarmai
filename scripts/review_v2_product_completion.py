"""Read-only source review, using generated temporary data only; no model calls."""

# ruff: noqa: E402

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "src"))
for key in list(os.environ):
    if key.startswith("SWARM_"):
        del os.environ[key]

from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.api.store import ProductStore
from swarm.goals.models import Goal
from swarm.pursuit import ExecutionOutcome, PursuitEngine
from swarm.workers.continuous_connector import (
    PermittedRuntime,
    execute_mac_local_extract_operational,
)

result = {
    "source_sha": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip(),
    "probes": {},
}
with tempfile.TemporaryDirectory(prefix="swarm-review-") as tmp:
    base = Path(tmp)
    app = create_app(
        repo_root=base / "api",
        seed_loopback_token="review-only-token",
        install_project_id="proj_review",
        db_reachable=False,
    )
    store = app.state.store
    goal = store.goal_store().create(
        Goal(
            project_id="proj_review",
            desired_outcome="Produce a verified report",
            verification_criteria=["report exists"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )
    client = TestClient(app)
    response = client.post(
        f"/v1/goals/{goal.id}/pursuit/tick",
        json={"force": True},
        headers={"Authorization": "Bearer review-only-token"},
    )
    data = response.json()
    result["probes"]["operational_api_simulates_achievement"] = {
        "http_status": response.status_code,
        "execution_mode": store.execution_mode,
        "fixture_mode": store.fixture_mode,
        "executor": type(store.pursuit_engine().executor).__name__,
        "goal_status": data.get("goal", {}).get("status"),
        "evidence_refs": data.get("goal", {}).get("evidence_refs"),
        "mission_record_count": len(list((base / "api" / "var" / "missions").glob("*.json"))),
    }
    old = store.pursuit_engine()
    reopened = ProductStore(repo_root=base / "api").pursuit_engine()
    result["probes"]["pursuit_restart"] = {
        "before_history": len(old.history(goal.id)),
        "after_history": len(reopened.history(goal.id)),
        "scheduler_now": old.scheduler.now(),
        "next_due_at": old.scheduler.get(goal.id).next_due_at,
    }
    runtime = PermittedRuntime(
        "extract", frozenset({"extract"}), frozenset({"workspace.read"}), lambda c, p: {}
    )
    result["probes"]["runtime_authorization_match"] = {
        "missing_required_capability_admitted": runtime.matches(
            {"required_capabilities": ["extract", "admin"], "scopes": ["workspace.read"]}
        ),
        "forbidden_scope_admitted": runtime.matches(
            {"required_capabilities": ["extract"], "scopes": ["secrets.read"]}
        ),
    }
    workspace = base / "workspace"
    workspace.mkdir()
    outside = base / "outside.txt"
    outside.write_text("Generated probe: test@example.test\n")
    work = execute_mac_local_extract_operational(
        {"task": {"id": "generated-probe", "input_path": str(outside)}}, workspace
    )
    result["probes"]["outside_workspace_input"] = {
        "input_is_outside_supplied_workspace": not outside.is_relative_to(workspace),
        "status": work["status"],
        "artifact_created": bool(work.get("artifact_manifest")),
    }
    granted, _ = asyncio.run(
        store.enroll_worker(
            capabilities=["code.write"],
            capacity_units=1,
            privacy_classes=["local"],
            project_id="proj_review",
            actor="review",
            platform="unsupported_os",
            architecture="unsupported_arch",
        )
    )
    result["probes"]["unenforced_enrollment_qualification"] = {
        "platform": granted.platform,
        "capabilities": granted.capabilities,
        "capabilities_verified": granted.capabilities_verified,
        "explicit_project_policy": "proj_review" in store.capability_authority.project_grants,
    }
    failed_goal = store.goal_store().create(
        Goal(
            project_id="proj_review",
            desired_outcome="Failed work must not achieve",
            verification_criteria=["valid artifact"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )

    class FailedExecutor:
        def execute(self, proposal):
            return ExecutionOutcome(
                mission_id=proposal.mission_id,
                success=False,
                satisfied_criteria=["valid artifact"],
                evidence_refs=[],
            )

    engine = PursuitEngine(store.goal_store(), executor=FailedExecutor())
    cycle = engine.tick(failed_goal.id, force=True)
    result["probes"]["failed_claim_achieves"] = {
        "verification_passed": cycle.verification.passed,
        "goal_status": store.goal_store().get(failed_goal.id).status.value,
    }
print(json.dumps(result, indent=2))
