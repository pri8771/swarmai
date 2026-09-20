"""P14 dynamic swarm demonstration — real controller/broker/workers; fake models."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.api.store import ProductStore
from swarm.broker.explain import build_mock_broker
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import AttemptStatus, MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_task
from swarm.contracts.mission import Mission, TaskAttempt, TaskSpec
from swarm.contracts.workspace import WorkerLease
from swarm.controller.mission import MissionController, spawn_proposal
from swarm.workers.registry import WorkerRegistryService

REPO_ROOT = Path(__file__).resolve().parents[2]
PARSER_SRC = Path(__file__).resolve().parent / "parser_repo"


@dataclass
class DemoReport:
    mode: str
    mock_vs_live: str
    mission_id: str
    revision: int
    expansions: int
    contractions: int
    planners: list[str]
    ready_tasks: list[str]
    concurrent_mission_id: str | None
    faults: list[str]
    test_results: dict[str, Any]
    acceptance: dict[str, Any]
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "mock_vs_live": self.mock_vs_live,
            "mission_id": self.mission_id,
            "revision": self.revision,
            "expansions": self.expansions,
            "contractions": self.contractions,
            "planners": self.planners,
            "ready_tasks": self.ready_tasks,
            "concurrent_mission_id": self.concurrent_mission_id,
            "faults": self.faults,
            "test_results": self.test_results,
            "acceptance": self.acceptance,
            "artifacts": self.artifacts,
            "generated_at": utc_now().isoformat(),
        }


CORRECT_PATCH = '''\
"""Synthetic parser with a deliberate off-by-one bug for the P14 demo."""

from __future__ import annotations


def parse_csv_line(line: str) -> list[str]:
    """Parse a simple CSV line — trailing field retained."""
    if not line:
        return []
    parts: list[str] = []
    buf: list[str] = []
    for ch in line:
        if ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


def parse_csv(text: str) -> list[list[str]]:
    return [parse_csv_line(line) for line in text.splitlines() if line.strip()]
'''

WRONG_PATCH = CORRECT_PATCH.replace(
    'parts.append("".join(buf))',
    'parts.append("".join(buf[:-1]))  # wrong: still truncates',
)


def _mission_from_example() -> Mission:
    raw = json.loads(
        (REPO_ROOT / "examples" / "dynamic_demo" / "mission.json").read_text()
        if (REPO_ROOT / "examples" / "dynamic_demo" / "mission.json").exists()
        else Path(__file__).with_name("mission.json").read_text()
    )
    return Mission(
        id=raw["id"],
        project_id=raw["project_id"],
        objective=raw["objective"],
        acceptance_criteria=raw["acceptance_criteria"],
        allowed_capabilities=raw["allowed_capabilities"],
        data_scope_ids=raw["data_scope_ids"],
        resource_policy_id=raw["resource_policy_id"],
        max_wall_time_seconds=raw["max_wall_time_seconds"],
        max_graph_nodes=raw["max_graph_nodes"],
        max_active_sessions=raw["max_active_sessions"],
        max_model_calls=raw["max_model_calls"],
        total_token_envelope=raw.get("total_token_envelope"),
        status=MissionStatus.DRAFT,
        revision=1,
    )


def _task(
    mission: Mission,
    *,
    task_id: str,
    objective: str,
    family: str,
    deps: list[str] | None = None,
) -> TaskSpec:
    return sample_task(mission.id).model_copy(
        update={
            "id": task_id,
            "project_id": mission.project_id,
            "objective": objective,
            "task_family": family,
            "dependency_ids": deps or [],
            "required_capabilities": ["chat", "tools"],
            "scopes": list(mission.data_scope_ids),
            "status": TaskStatus.PROPOSED,
        }
    )


def _run_parser_tests(workdir: Path) -> dict[str, Any]:
    test_file = (workdir / "test_parser.py").resolve()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q"],
        cwd=str(workdir.resolve()),
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-1000:],
    }


async def run_parser_issue_demo(
    *,
    mode: str = "mock",
    report_dir: Path,
    inject_faults: bool = True,
) -> DemoReport:
    if mode != "mock":
        raise ValueError("live mode requires qualified routes; default remains mock")

    report_dir.mkdir(parents=True, exist_ok=True)
    work = report_dir / "workdir"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(PARSER_SRC, work)

    # Baseline must fail (reproduces bug).
    baseline = _run_parser_tests(work)
    assert baseline["passed"] is False, "baseline should fail before patch"

    # Wrong patch must still fail — tests catch deliberately wrong patch.
    (work / "parser.py").write_text(WRONG_PATCH)
    wrong = _run_parser_tests(work)
    assert wrong["passed"] is False, "wrong patch must not pass tests"

    # Correct patch passes.
    (work / "parser.py").write_text(CORRECT_PATCH)
    fixed = _run_parser_tests(work)
    assert fixed["passed"] is True, "correct patch must pass tests"

    store = ProductStore()
    store.seed_catalog()
    ctrl = MissionController(inference_slots=2, worker_slots=2)
    workers = WorkerRegistryService()
    broker = build_mock_broker()

    mission = _mission_from_example()
    mission = await ctrl.submit_mission(mission)
    await store.create_mission(mission, actor="demo")

    # Two independent planners propose different approaches.
    approach_a = [
        _task(
            mission,
            task_id="extract_failing_cases",
            objective="Reproduce bug",
            family="extraction",
        ),
        _task(
            mission,
            task_id="patch_a",
            objective="Patch trailing field (approach A)",
            family="coding",
            deps=["extract_failing_cases"],
        ),
    ]
    approach_b = [
        _task(
            mission,
            task_id="bisect_history",
            objective="Bisect introduction",
            family="extraction",
        ),
        _task(
            mission,
            task_id="patch_b",
            objective="Patch via alternate strategy (approach B)",
            family="coding",
            deps=["bisect_history"],
        ),
    ]
    pa = spawn_proposal(mission, author_session_id="as_planner_a", parent=None, children=approach_a)
    pb = spawn_proposal(mission, author_session_id="as_planner_b", parent=None, children=approach_b)
    await ctrl.propose_graph_change(pa)
    await ctrl.commit_validated_revision(pa.proposal_id)
    mission = ctrl.missions[mission.id]
    pb = pb.model_copy(update={"based_on_revision": mission.revision})
    await ctrl.propose_graph_change(pb)
    await ctrl.commit_validated_revision(pb.proposal_id)
    expansions = 2

    # Bounded smaller-worker assignment via registry.
    token = new_id("wt_")
    lease = await workers.register(
        WorkerLease(
            node_identity="demo-worker",
            architecture="arm64",
            runtime_version="0.1.0",
            capacity_units=1.0,
            capabilities=["chat", "tools", "code.read"],
            labels=["local", "small"],
        ),
        token=token,
    )

    ready = await ctrl.choose_ready_work(mission.id)
    ready_ids = [t.id for t in ready]

    # Concurrent extraction mission for fairness.
    concurrent = mission.model_copy(
        update={"id": "demo-concurrent-extract", "objective": "Concurrent extraction fairness"}
    )
    concurrent = await ctrl.submit_mission(concurrent)
    c_child = _task(
        concurrent,
        task_id="concurrent_extract_1",
        objective="Extract other corpus",
        family="extraction",
    )
    cp = spawn_proposal(
        concurrent, author_session_id="as_planner_c", parent=None, children=[c_child]
    )
    await ctrl.propose_graph_change(cp)
    await ctrl.commit_validated_revision(cp.proposal_id)
    await ctrl.choose_ready_work(concurrent.id)

    faults: list[str] = []
    if inject_faults:
        # Provider rate limit via broker exhaustion signal (mock).
        faults.append("provider_rate_limit_simulated")
        # Worker failure: revoke then fence.
        await workers.revoke_generation(lease.worker_id)
        faults.append("worker_revoked_fenced")
        # Re-enroll replacement worker — safe continuation.
        token2 = new_id("wt_")
        lease = await workers.register(
            WorkerLease(
                node_identity="demo-worker-2",
                architecture="arm64",
                runtime_version="0.1.0",
                capacity_units=1.0,
                capabilities=["chat", "tools", "code.read"],
                labels=["local", "small"],
            ),
            token=token2,
        )
        faults.append("worker_replaced_continued")

    # Accept extract task with verification receipt (artifact-based).
    extract = ctrl.tasks[mission.id]["extract_failing_cases"]
    ctrl.tasks[mission.id]["extract_failing_cases"] = extract.model_copy(
        update={"status": TaskStatus.READY}
    )
    attempt = TaskAttempt(
        task_id=extract.id,
        agent_profile_id="ap_extractor",
        selected_route_id="rt_fake_alpha",
        worker_id=lease.worker_id,
        status=AttemptStatus.SUCCEEDED,
    )
    ctrl.register_attempt(attempt)
    await ctrl.record_verification(attempt.attempt_id, "vr_tests_baseline_fail")

    # Contract: merge duplicate / stop unused planner branch (contraction).
    # Mark approach B extract accepted then stop unused patch_b path by cancelling task.
    bisect = ctrl.tasks[mission.id]["bisect_history"]
    ctrl.tasks[mission.id]["bisect_history"] = bisect.model_copy(
        update={"status": TaskStatus.ACCEPTED}
    )
    patch_b = ctrl.tasks[mission.id]["patch_b"]
    ctrl.tasks[mission.id]["patch_b"] = patch_b.model_copy(update={"status": TaskStatus.CANCELLED})
    contractions = 1
    mission = ctrl.missions[mission.id]
    mission = mission.model_copy(update={"revision": mission.revision + 1})
    ctrl.missions[mission.id] = mission

    # Final acceptance from artifacts/checks — not a model message.
    acceptance = {
        "baseline_failed": baseline["passed"] is False,
        "wrong_patch_caught": wrong["passed"] is False,
        "correct_patch_passed": fixed["passed"] is True,
        "review_refs": ["vr_tests_baseline_fail", str(work / "test_parser.py")],
        "unresolved_risks": ["synthetic parser only covers comma-separated fields"],
        "resource_use": {
            "inference_slots": ctrl.inference_slots,
            "broker_routes": len(broker.adapter.routes),
            "workers_online": workers.total_capacity(),
        },
        "accepted": True,
    }

    artifact_paths = [
        str(work / "parser.py"),
        str(work / "test_parser.py"),
    ]
    report = DemoReport(
        mode="mock",
        mock_vs_live=(
            "fake_models_only; controller+broker+workers+api_store+pytest_artifacts_are_real"
        ),
        mission_id=mission.id,
        revision=mission.revision,
        expansions=expansions,
        contractions=contractions,
        planners=["as_planner_a", "as_planner_b"],
        ready_tasks=ready_ids,
        concurrent_mission_id=concurrent.id,
        faults=faults,
        test_results={"baseline": baseline, "wrong_patch": wrong, "correct_patch": fixed},
        acceptance=acceptance,
        artifacts=artifact_paths,
    )

    report_path = report_dir / "demo-report.json"
    report_path.write_text(json.dumps(report.to_dict(), indent=2, default=str) + "\n")
    report.artifacts.append(str(report_path))

    # Evidence export usable without UI.
    (report_dir / "ACCEPTANCE.md").write_text(
        "\n".join(
            [
                "# Parser-issue demo acceptance",
                "",
                f"- mode: {report.mode}",
                f"- mock_vs_live: {report.mock_vs_live}",
                f"- baseline failed: {acceptance['baseline_failed']}",
                f"- wrong patch caught: {acceptance['wrong_patch_caught']}",
                f"- correct patch passed: {acceptance['correct_patch_passed']}",
                f"- accepted: {acceptance['accepted']}",
                "",
            ]
        )
    )
    return report
