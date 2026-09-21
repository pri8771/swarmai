"""Repo inspection and structured mission task-graph planning."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id
from swarm.contracts.enums import GraphOperation, RiskLevel
from swarm.contracts.mission import GraphProposal, Mission, SizeFeatures, TaskSpec


@dataclass
class RepoInspection:
    root: Path
    git_head: str | None
    has_pyproject: bool
    has_tests: bool
    top_entries: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "git_head": self.git_head,
            "has_pyproject": self.has_pyproject,
            "has_tests": self.has_tests,
            "top_entries": self.top_entries,
            "notes": self.notes,
        }


def inspect_repo(repo: Path) -> RepoInspection:
    root = repo.resolve()
    head: str | None = None
    try:
        import subprocess

        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            head = proc.stdout.strip()
    except OSError:
        head = None
    entries = sorted(p.name for p in root.iterdir() if not p.name.startswith("."))[:40]
    notes: list[str] = []
    if (root / "sandbox" / "selfdev_issue" / "parser_helper.py").exists():
        notes.append("selfdev_off_by_one_sample_present")
    if (root / "src" / "swarm").exists():
        notes.append("swarm_package_present")
    return RepoInspection(
        root=root,
        git_head=head,
        has_pyproject=(root / "pyproject.toml").exists(),
        has_tests=(root / "tests").is_dir(),
        top_entries=entries,
        notes=notes,
    )


def build_software_mission(
    *,
    goal: str,
    project_id: str = "proj_local",
    max_retries: int = 2,
) -> Mission:
    return Mission(
        project_id=project_id,
        objective=goal,
        acceptance_criteria=[
            "Structured task graph executed with dependency order",
            "Workers ran in isolated git worktrees",
            "Verification commands executed against real files",
            "Mission report persisted with cost accounting",
        ],
        allowed_capabilities=["repo_read", "repo_edit", "local_command", "local_inference"],
        data_scope_ids=["scope_repo"],
        resource_policy_id="rp_v0_1_local",
        max_wall_time_seconds=1800,
        max_graph_nodes=16,
        max_active_sessions=4,
        max_model_calls=24,
        total_token_envelope=200_000,
    )


def plan_task_graph(
    mission: Mission,
    inspection: RepoInspection,
    *,
    author_session_id: str = "as_planner",
) -> GraphProposal:
    """Produce a dependency-aware structured task graph (not prose-only)."""
    mid = mission.id
    inspect_id = new_id("tsk_")
    implement_id = new_id("tsk_")
    verify_id = new_id("tsk_")
    review_id = new_id("tsk_")

    size = SizeFeatures(
        file_count=len(inspection.top_entries),
        dependency_depth=3,
        tool_steps_estimate=8,
        risk_level=RiskLevel.MEDIUM,
        language="python",
        source_complexity="repo_mission",
    )
    tasks = [
        TaskSpec(
            id=inspect_id,
            project_id=mission.project_id,
            mission_id=mid,
            objective="Inspect repository layout and identify files to change for the goal",
            task_family="inspect",
            size_features=size,
            inputs={"goal": mission.objective, "inspection": inspection.to_dict()},
            output_schema_id="schema_inspect_findings",
            acceptance_check_ids=["findings_nonempty"],
            dependency_ids=[],
            role_hint="inspector",
            required_capabilities=["repo_read"],
            scopes=["scope_repo"],
            quality_policy_id="qp_default",
            attempt_limit=2,
            priority=10,
        ),
        TaskSpec(
            id=implement_id,
            project_id=mission.project_id,
            mission_id=mid,
            objective="Implement the required change in an isolated worktree",
            task_family="implement",
            size_features=size,
            inputs={"goal": mission.objective},
            output_schema_id="schema_patch",
            acceptance_check_ids=["diff_nonempty"],
            dependency_ids=[inspect_id],
            role_hint="implementer",
            required_capabilities=["repo_read", "repo_edit", "local_inference"],
            scopes=["scope_repo"],
            quality_policy_id="qp_default",
            attempt_limit=3,
            priority=20,
        ),
        TaskSpec(
            id=verify_id,
            project_id=mission.project_id,
            mission_id=mid,
            objective="Run configured verification (tests/lint) in the worker worktree",
            task_family="verify",
            size_features=size,
            inputs={"goal": mission.objective},
            output_schema_id="schema_verify",
            acceptance_check_ids=["commands_recorded"],
            dependency_ids=[implement_id],
            role_hint="verifier",
            required_capabilities=["local_command"],
            scopes=["scope_repo"],
            quality_policy_id="qp_default",
            attempt_limit=3,
            priority=30,
        ),
        TaskSpec(
            id=review_id,
            project_id=mission.project_id,
            mission_id=mid,
            objective="Review diff, synthesize outcome, and accept or request repair",
            task_family="review",
            size_features=size,
            inputs={"goal": mission.objective},
            output_schema_id="schema_review",
            acceptance_check_ids=["decision_recorded"],
            dependency_ids=[verify_id],
            role_hint="reviewer",
            required_capabilities=["repo_read"],
            scopes=["scope_repo"],
            quality_policy_id="qp_default",
            attempt_limit=2,
            priority=40,
        ),
    ]
    return GraphProposal(
        project_id=mission.project_id,
        mission_id=mid,
        based_on_revision=mission.revision,
        author_session_id=author_session_id,
        operation=GraphOperation.SPAWN,
        task_specs=tasks,
        rationale_summary=(
            "V0.1 structured software mission: inspect → implement → verify → review"
        ),
        projected_resource_envelope={
            "max_model_calls": mission.max_model_calls,
            "workers": 2,
            "inspection": inspection.to_dict(),
        },
        evidence_refs=["local_repo_inspection"],
    )


def serialize_plan(proposal: GraphProposal) -> str:
    return json.dumps(proposal.model_dump(mode="json"), indent=2, default=str)
