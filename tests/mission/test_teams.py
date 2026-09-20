"""P32 dynamic team formation tests."""

from __future__ import annotations

from pathlib import Path

from swarm.mission.planner import build_software_mission, inspect_repo
from swarm.mission.teams import estimate_complexity, form_dynamic_team, plan_dynamic_task_graph


def test_complexity_increases_with_scale_goal(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n")
    (tmp_path / "tests").mkdir()
    inspection = inspect_repo(tmp_path)
    low, _ = estimate_complexity("fix typo", inspection)
    high, signals = estimate_complexity(
        "scale parallel swarm refactor across a.py b.py c.py with tests",
        inspection,
    )
    assert high > low
    assert signals.get("scale_keywords")


def test_form_dynamic_team_scales_workers() -> None:
    mission = build_software_mission(
        goal="scale parallel swarm mission with review and multi file a.py b.py"
    )
    # Minimal fake inspection
    from swarm.mission.planner import RepoInspection

    inspection = RepoInspection(
        root=Path("."),
        git_head=None,
        has_pyproject=True,
        has_tests=True,
        top_entries=["a", "b", "c"],
        notes=[],
    )
    team = form_dynamic_team(mission, inspection, max_agents=16)
    assert team.agent_count() >= 4
    assert any(r.role == "worker" and r.count >= 2 for r in team.roles)
    assert team.agent_count() <= 16


def test_plan_dynamic_task_graph_dependencies() -> None:
    mission = build_software_mission(goal="fix off-by-one with tests and review")
    from swarm.mission.planner import RepoInspection

    inspection = RepoInspection(
        root=Path("."),
        git_head="abc",
        has_pyproject=True,
        has_tests=True,
        top_entries=["src"],
        notes=["swarm_package_present"],
    )
    proposal, team = plan_dynamic_task_graph(mission, inspection, max_agents=12)
    assert proposal.rationale_summary == team.rationale
    families = {t.task_family for t in proposal.task_specs}
    assert "inspect" in families
    assert "implement" in families
    assert "review" in families
    assert "verify" in families
    # Workers depend on inspect.
    workers = [t for t in proposal.task_specs if t.task_family == "implement"]
    assert workers
    for w in workers:
        assert any(d.startswith("tsk_") for d in w.dependency_ids)
