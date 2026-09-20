"""V0.3 P32 — dynamic team formation from mission needs.

Planners create subteams (supervisor, specialists, workers, reviewers)
instead of a fixed four-role crew. Team size scales with goal complexity
and repo signals while remaining bounded for zero-spend dogfood.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from swarm.contracts.common import new_id
from swarm.contracts.enums import GraphOperation, RiskLevel
from swarm.contracts.mission import GraphProposal, Mission, SizeFeatures, TaskSpec
from swarm.mission.planner import RepoInspection


ROLE_CAPS: dict[str, list[str]] = {
    "supervisor": ["repo_read", "local_inference"],
    "specialist": ["repo_read", "local_inference"],
    "worker": ["repo_read", "repo_edit", "local_inference", "local_command"],
    "reviewer": ["repo_read", "local_inference"],
}


@dataclass
class TeamRole:
    role: str
    count: int
    task_family: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DynamicTeamPlan:
    mission_id: str
    complexity_score: int
    roles: list[TeamRole]
    max_agents: int
    rationale: str
    signals: dict[str, Any] = field(default_factory=dict)

    def agent_count(self) -> int:
        return sum(r.count for r in self.roles)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "complexity_score": self.complexity_score,
            "max_agents": self.max_agents,
            "agent_count": self.agent_count(),
            "roles": [r.to_dict() for r in self.roles],
            "rationale": self.rationale,
            "signals": self.signals,
        }


def estimate_complexity(goal: str, inspection: RepoInspection) -> tuple[int, dict[str, Any]]:
    """Heuristic complexity in 1–10 from goal text + repo signals."""
    score = 2
    signals: dict[str, Any] = {"goal_len": len(goal), "top_entries": len(inspection.top_entries)}
    g = goal.lower()
    if len(goal) > 120:
        score += 1
    if any(w in g for w in ("refactor", "migrate", "multi", "scale", "parallel", "swarm")):
        score += 2
        signals["scale_keywords"] = True
    if any(w in g for w in ("test", "verify", "review", "audit")):
        score += 1
        signals["quality_keywords"] = True
    if inspection.has_tests:
        score += 1
        signals["has_tests"] = True
    if inspection.has_pyproject:
        score += 1
    # Fan-out hint: N files / modules mentioned.
    file_hits = re.findall(r"[\w./-]+\.py", goal)
    if file_hits:
        score += min(3, len(set(file_hits)))
        signals["named_files"] = sorted(set(file_hits))[:12]
    if "selfdev_issue" in g or "off-by-one" in g:
        score = max(score, 3)
        signals["dogfood_target"] = True
    score = max(1, min(10, score))
    return score, signals


def form_dynamic_team(
    mission: Mission,
    inspection: RepoInspection,
    *,
    max_agents: int = 32,
    min_workers: int = 1,
) -> DynamicTeamPlan:
    """Allocate supervisor / specialists / workers / reviewers from needs."""
    complexity, signals = estimate_complexity(mission.objective, inspection)
    # Workers scale with complexity; specialists appear for multi-file / scale goals.
    workers = min(max(min_workers, complexity // 2), max(1, max_agents // 2))
    specialists = 1 if complexity >= 5 else 0
    if signals.get("named_files"):
        specialists = min(2, max(specialists, len(signals["named_files"]) // 3 or 1))
    reviewers = 1 if complexity >= 3 else 1
    supervisors = 1
    # Fit under max_agents.
    total = supervisors + specialists + workers + reviewers
    while total > max_agents and workers > 1:
        workers -= 1
        total -= 1
    while total > max_agents and specialists > 0:
        specialists -= 1
        total -= 1

    roles = [
        TeamRole(
            role="supervisor",
            count=supervisors,
            task_family="supervise",
            rationale="coordinate subteams and accept/reject branches",
        ),
    ]
    if specialists:
        roles.append(
            TeamRole(
                role="specialist",
                count=specialists,
                task_family="specialize",
                rationale="domain analysis before worker fan-out",
            )
        )
    roles.append(
        TeamRole(
            role="worker",
            count=workers,
            task_family="implement",
            rationale=f"{workers} parallel/sequential workers for complexity={complexity}",
        )
    )
    roles.append(
        TeamRole(
            role="reviewer",
            count=reviewers,
            task_family="review",
            rationale="independent review / consensus vote",
        )
    )
    rationale = (
        f"Dynamic team for complexity={complexity}: "
        + ", ".join(f"{r.count}×{r.role}" for r in roles)
        + f" (cap={max_agents})"
    )
    return DynamicTeamPlan(
        mission_id=mission.id,
        complexity_score=complexity,
        roles=roles,
        max_agents=max_agents,
        rationale=rationale,
        signals=signals,
    )


def plan_dynamic_task_graph(
    mission: Mission,
    inspection: RepoInspection,
    *,
    author_session_id: str = "as_dynamic_planner",
    max_agents: int = 32,
) -> tuple[GraphProposal, DynamicTeamPlan]:
    """Build a dependency-aware graph from a dynamic team plan."""
    team = form_dynamic_team(mission, inspection, max_agents=max_agents)
    mid = mission.id
    size = SizeFeatures(
        file_count=len(inspection.top_entries),
        dependency_depth=4,
        tool_steps_estimate=max(8, team.agent_count() * 2),
        risk_level=RiskLevel.MEDIUM if team.complexity_score < 7 else RiskLevel.HIGH,
        language="python",
        source_complexity="dynamic_team",
    )

    tasks: list[TaskSpec] = []
    supervise_ids: list[str] = []
    specialist_ids: list[str] = []
    worker_ids: list[str] = []
    review_ids: list[str] = []

    # Inspect once (shared context).
    inspect_id = new_id("tsk_")
    tasks.append(
        TaskSpec(
            id=inspect_id,
            project_id=mission.project_id,
            mission_id=mid,
            objective="Inspect repository and publish shared findings for subteams",
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
            priority=5,
        )
    )

    for role in team.roles:
        for i in range(role.count):
            tid = new_id("tsk_")
            if role.role == "supervisor":
                supervise_ids.append(tid)
                deps = [inspect_id]
                family = "supervise"
                obj = "Supervise team progress and record coordination notes"
                caps = ROLE_CAPS["supervisor"]
                priority = 15
            elif role.role == "specialist":
                specialist_ids.append(tid)
                deps = [inspect_id]
                family = "specialize"
                obj = f"Specialize analysis lane {i + 1} for the mission goal"
                caps = ROLE_CAPS["specialist"]
                priority = 18
            elif role.role == "worker":
                worker_ids.append(tid)
                deps = [inspect_id] + specialist_ids
                family = "implement"
                obj = f"Worker lane {i + 1}: implement or validate assigned slice"
                caps = ROLE_CAPS["worker"]
                priority = 20 + i
            else:
                review_ids.append(tid)
                deps = list(worker_ids) if worker_ids else [inspect_id]
                family = "review"
                obj = f"Reviewer {i + 1}: critique worker outputs and vote accept/reject"
                caps = ROLE_CAPS["reviewer"]
                priority = 40 + i
            tasks.append(
                TaskSpec(
                    id=tid,
                    project_id=mission.project_id,
                    mission_id=mid,
                    objective=obj,
                    task_family=family,
                    size_features=size,
                    inputs={
                        "goal": mission.objective,
                        "team_role": role.role,
                        "lane": i + 1,
                        "team_plan": team.to_dict(),
                    },
                    output_schema_id=f"schema_{family}",
                    acceptance_check_ids=["recorded"],
                    dependency_ids=deps,
                    role_hint=role.role,
                    required_capabilities=caps,
                    scopes=["scope_repo"],
                    quality_policy_id="qp_default",
                    attempt_limit=2,
                    priority=priority,
                )
            )

    # Final verify after reviews.
    verify_id = new_id("tsk_")
    tasks.append(
        TaskSpec(
            id=verify_id,
            project_id=mission.project_id,
            mission_id=mid,
            objective="Run verification commands after dynamic team execution",
            task_family="verify",
            size_features=size,
            inputs={},
            output_schema_id="schema_verify",
            acceptance_check_ids=["commands_recorded"],
            dependency_ids=review_ids or worker_ids or [inspect_id],
            role_hint="verifier",
            required_capabilities=["local_command"],
            scopes=["scope_repo"],
            quality_policy_id="qp_default",
            attempt_limit=3,
            priority=50,
        )
    )

    proposal = GraphProposal(
        project_id=mission.project_id,
        mission_id=mid,
        based_on_revision=mission.revision,
        author_session_id=author_session_id,
        operation=GraphOperation.SPAWN,
        task_specs=tasks,
        rationale_summary=team.rationale,
        projected_resource_envelope={
            "max_model_calls": mission.max_model_calls,
            "agents": team.agent_count(),
            "team": team.to_dict(),
        },
        evidence_refs=["dynamic_team_formation", "local_repo_inspection"],
    )
    return proposal, team
