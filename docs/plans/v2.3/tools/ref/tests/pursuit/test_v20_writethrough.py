"""SW-W1-S9 / V20-E03: DB-first write-through and fail-closed mirror (offline fakes)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from swarm.goals.models import Goal, GoalStore
from swarm.pursuit import PursuitEngine, PursuitScheduler, RecordingExecutor
from swarm.pursuit.pg_mirror import PursuitMirrorError, dedupe_db_key
from swarm.pursuit.state_store import DurablePursuitStateStore


class FakeMirror:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.fail = False

    def write_snapshot(self, goal_id: str, snapshot: dict[str, Any]) -> None:
        if self.fail:
            raise PursuitMirrorError("pursuit_mirror_write_failed:Fake")
        self.rows[goal_id] = snapshot

    def load_snapshot(self, goal_id: str) -> dict[str, Any] | None:
        if self.fail:
            raise PursuitMirrorError("pursuit_mirror_read_failed:Fake")
        return self.rows.get(goal_id)


def _goal(root: Path) -> tuple[GoalStore, Goal]:
    goals = GoalStore(root / "goals")
    goal = goals.create(
        Goal(
            project_id="proj_wt",
            desired_outcome="write through",
            verification_criteria=["one", "two"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )
    return goals, goal


def _engine(goals: GoalStore, store: DurablePursuitStateStore) -> PursuitEngine:
    return PursuitEngine(
        goals,
        executor=RecordingExecutor(default_success=True),
        scheduler=PursuitScheduler(clock=lambda: 50.0),
        state_store=store,
    )


def test_db_snapshot_is_authoritative_on_reopen(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path)
    mirror = FakeMirror()
    engine = _engine(goals, DurablePursuitStateStore(tmp_path / "ps", mirror=mirror))
    engine.tick(goal.id, force=True)
    assert goal.id in mirror.rows
    # The local file volume is lost; the DB snapshot alone restores state.
    cold = _engine(goals, DurablePursuitStateStore(tmp_path / "ps_new_volume", mirror=mirror))
    assert len(cold.history(goal.id)) == 1
    assert cold.satisfied_criteria(goal.id) == engine.satisfied_criteria(goal.id)


def test_mirror_write_failure_fails_closed_and_file_not_written(tmp_path: Path) -> None:
    mirror = FakeMirror()
    store = DurablePursuitStateStore(tmp_path / "ps", mirror=mirror)
    mirror.fail = True
    with pytest.raises(PursuitMirrorError):
        store.save(
            "goal_x",
            satisfied=set(),
            history=[],
            dedupe={},
            failed_approaches=set(),
            active_missions=set(),
            commitments=[],
            schedule=None,
        )
    assert not (tmp_path / "ps" / "goal_x.json").exists()


def test_mirror_read_failure_is_not_silently_ignored(tmp_path: Path) -> None:
    mirror = FakeMirror()
    store = DurablePursuitStateStore(tmp_path / "ps", mirror=mirror)
    mirror.fail = True
    with pytest.raises(PursuitMirrorError):
        store.load("goal_x")


def test_file_fallback_when_db_has_no_row(tmp_path: Path) -> None:
    plain = DurablePursuitStateStore(tmp_path / "ps")
    plain.save(
        "goal_old",
        satisfied={"a"},
        history=[],
        dedupe={},
        failed_approaches=set(),
        active_missions=set(),
        commitments=[],
        schedule=None,
    )
    mirrored = DurablePursuitStateStore(tmp_path / "ps", mirror=FakeMirror())
    raw = mirrored.load("goal_old")
    assert raw is not None and raw["satisfied_criteria"] == ["a"]


def test_long_dedupe_keys_are_hashed_to_column_width() -> None:
    assert dedupe_db_key("short") == "short"
    long_key = "k" * 200
    hashed = dedupe_db_key(long_key)
    assert len(hashed) == 64 and hashed == dedupe_db_key(long_key)
