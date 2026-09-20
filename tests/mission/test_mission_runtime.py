"""V0.1 mission runtime unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.cost.ledger import CostEntry, CostLedger, format_cost_show
from swarm.mission.planner import build_software_mission, inspect_repo, plan_task_graph
from swarm.mission.store import MissionRecord, MissionStore
from swarm.mission.worktree import create_worktree, remove_worktree, worktree_diff

ROOT = Path(__file__).resolve().parents[2]


def test_inspect_and_structured_plan() -> None:
    inspection = inspect_repo(ROOT)
    assert inspection.has_pyproject
    mission = build_software_mission(goal="fix off-by-one in parser_helper")
    proposal = plan_task_graph(mission, inspection)
    families = [t.task_family for t in proposal.task_specs]
    assert families == ["inspect", "implement", "verify", "review"]
    # Dependency chain is linear.
    assert proposal.task_specs[1].dependency_ids == [proposal.task_specs[0].id]
    assert proposal.task_specs[2].dependency_ids == [proposal.task_specs[1].id]
    assert proposal.task_specs[3].dependency_ids == [proposal.task_specs[2].id]


def test_mission_store_roundtrip(tmp_path: Path) -> None:
    store = MissionStore(tmp_path / "missions")
    record = MissionRecord(
        mission_id="msn_test",
        goal="demo",
        status="running",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    store.append_timeline(record, "started", {"ok": True})
    path = store.save(record)
    assert path.exists()
    loaded = store.load("msn_test")
    assert loaded.goal == "demo"
    assert loaded.timeline[0]["event"] == "started"
    assert store.list_missions()[0]["mission_id"] == "msn_test"


def test_cost_ledger_zero_spend() -> None:
    ledger = CostLedger()
    ledger.add(
        CostEntry(
            source="t1",
            route_id="rt_ollama_gemma3:4b",
            model="gemma3:4b",
            requests=1,
            cost_usd=0.0,
        )
    )
    view = format_cost_show(ledger)
    assert view["total_usd"] == 0.0
    with pytest.raises(PermissionError):
        ledger.add(
            CostEntry(
                source="paid",
                route_id="rt_paid",
                model="x",
                requests=1,
                cost_usd=0.01,
            )
        )


def test_real_git_worktree_isolation() -> None:
    handle = create_worktree(
        ROOT,
        mission_id="msn_unit",
        task_id="tsk_unit",
        worker_id="wrk_unit",
        base_dir=ROOT / "var" / "mission-worktrees" / "unit-test",
    )
    try:
        assert handle.path.exists()
        marker = handle.path / "sandbox" / "selfdev_issue" / "parser_helper.py"
        assert marker.exists()
        original = marker.read_text()
        marker.write_text(original + "\n# mission-worktree-marker\n")
        diff = worktree_diff(handle)
        assert "mission-worktree-marker" in diff
        # Parent checkout must remain unchanged.
        parent = ROOT / "sandbox" / "selfdev_issue" / "parser_helper.py"
        assert "# mission-worktree-marker" not in parent.read_text()
    finally:
        remove_worktree(ROOT, handle, force=True)
