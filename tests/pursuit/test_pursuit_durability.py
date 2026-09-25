"""R20-04 / PC-02: pursuit history and schedules survive ProductStore reopen."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.api.durable_authority import dry_run_import_goals_json
from swarm.api.store import ProductStore
from swarm.goals.models import Goal, GoalStatus, GoalStore
from swarm.pursuit import PursuitEngine, PursuitScheduler, RecordingExecutor

HEADERS = {"Authorization": "Bearer review-only-token"}


def test_pursuit_history_survives_store_reopen(tmp_path: Path) -> None:
    root = tmp_path / "api"
    goals = GoalStore(root / "var" / "goals")
    goal = goals.create(
        Goal(
            project_id="proj_persist",
            desired_outcome="Persist pursuit cycles",
            verification_criteria=["step_one", "step_two"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )
    clock = {"t": 100.0}
    engine = PursuitEngine(
        goals,
        executor=RecordingExecutor(default_success=True),
        scheduler=PursuitScheduler(clock=lambda: clock["t"]),
        state_root=root / "var" / "pursuit",
    )
    cycle = engine.tick(goal.id, force=True)
    assert cycle.phase.value == "update"
    assert len(engine.history(goal.id)) == 1
    satisfied_before = engine.satisfied_criteria(goal.id)
    assert satisfied_before

    # Cold reopen — new ProductStore / PursuitEngine against same volume.
    reopened = ProductStore(repo_root=root, db_reachable=None)
    cold = reopened.pursuit_engine()
    assert len(cold.history(goal.id)) == 1
    assert cold.satisfied_criteria(goal.id) == satisfied_before
    assert cold.scheduler.get(goal.id).next_due_at >= 100.0


def test_synthetic_achievement_flagged_on_disk(tmp_path: Path) -> None:
    goals = GoalStore(tmp_path / "goals")
    goal = goals.create(
        Goal(
            project_id="proj_syn",
            desired_outcome="Mark synthetic",
            verification_criteria=["only"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )
    engine = PursuitEngine(
        goals,
        executor=RecordingExecutor(default_success=True),
        scheduler=PursuitScheduler(clock=lambda: 1.0),
        state_root=tmp_path / "pursuit",
    )
    engine.tick(goal.id, force=True)
    refreshed = goals.get(goal.id)
    assert refreshed.status == GoalStatus.ACHIEVED
    assert refreshed.achievement_authority == "synthetic"


def test_operational_db_down_blocks_pursuit_tick(tmp_path: Path) -> None:
    app = create_app(
        repo_root=tmp_path,
        seed_loopback_token="review-only-token",
        install_project_id="proj_block",
        db_reachable=False,
    )
    assert app.state.store.health_ready()["durable_writes"] == "blocked_db_down"
    client = TestClient(app)
    # Seed goal via GoalStore directly (bypassing blocked API) then tick must 503.
    goal = app.state.store.goal_store().create(
        Goal(
            project_id="proj_block",
            desired_outcome="Must not write",
            verification_criteria=["x"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"]},
        )
    )
    response = client.post(
        f"/v1/goals/{goal.id}/pursuit/tick",
        json={"force": True},
        headers=HEADERS,
    )
    assert response.status_code == 503
    assert response.json()["code"] == "durable_authority_unavailable"


def test_dry_run_import_flags_synthetic(tmp_path: Path) -> None:
    path = tmp_path / "goals.json"
    path.write_text(
        '{"schema_version":"1.8","goals":['
        '{"id":"goal_a","project_id":"p","desired_outcome":"x","status":"achieved"},'
        '{"id":"goal_b","project_id":"p","desired_outcome":"y","status":"active"}'
        "]}\n",
        encoding="utf-8",
    )
    receipt = dry_run_import_goals_json(path)
    assert receipt["schema_ok"] is True
    assert "goal_a" in receipt["synthetic_achievements"]
    assert any(r["goal_id"] == "goal_b" for r in receipt["accepted"])
