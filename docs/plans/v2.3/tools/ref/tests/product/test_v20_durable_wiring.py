"""SW-W3-S2: E03 mirror, E04 holds and E06 singleton ticker are wired into ProductStore."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.api.store import ProductStore
from swarm.goals.models import Goal, GoalStore
from swarm.pursuit import PursuitEngine, PursuitScheduler, RecordingExecutor
from swarm.pursuit.durable_accounting import InMemoryHoldStore
from swarm.scheduling.epoch import InMemorySchedulerEpochService
from swarm.scheduling.singleton import SingletonTicker


def _goals(root: Path, *outcomes: str) -> tuple[GoalStore, list[str]]:
    goals = GoalStore(root / "var" / "goals")
    ids = [
        goals.create(
            Goal(
                project_id="proj_wire",
                desired_outcome=text,
                verification_criteria=["done"],
                resource_envelope={"spend_usd_ceiling": 1.0, "allow_paid": True},
                authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
            )
        ).id
        for text in outcomes
    ]
    return goals, ids


def _engine(goals: GoalStore, root: Path, **kw: object) -> PursuitEngine:
    return PursuitEngine(
        goals,
        executor=RecordingExecutor(default_success=True),
        scheduler=PursuitScheduler(clock=lambda: 1000.0),
        state_root=root / "var" / "pursuit",
        **kw,  # type: ignore[arg-type]
    )


def test_default_store_stays_file_backed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_V23_DURABLE", raising=False)
    store = ProductStore(repo_root=tmp_path, db_reachable=True)
    engine = store.pursuit_engine()
    assert store.pg_session_factory() is None
    assert engine.hold_store is None
    assert engine.state_store.mirror is None


def test_flag_without_reachable_db_stays_file_backed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SWARM_V23_DURABLE", "1")
    store = ProductStore(repo_root=tmp_path, db_reachable=False)
    assert store.pg_session_factory() is None


def test_engine_ledgers_restore_holds_from_store(tmp_path: Path) -> None:
    goals, (gid,) = _goals(tmp_path, "hold budget")
    holds = InMemoryHoldStore()
    first = _engine(goals, tmp_path, hold_store=holds)
    hold = first.resource_ledger(gid).reserve(mission_id="msn_1", spend_usd=0.4)
    cold = _engine(goals, tmp_path, hold_store=holds)
    restored = cold.resource_ledger(gid)
    assert hold.hold_id in restored.holds
    assert restored.remaining().spend_usd == pytest.approx(0.6)


def test_tick_all_due_skips_paused_goals(tmp_path: Path) -> None:
    goals, (active, paused) = _goals(tmp_path, "active goal", "paused goal")
    goals.pause(paused, reason="test", actor="tester")
    records = _engine(goals, tmp_path).tick_all_due()
    assert [r.goal_id for r in records] == [active]


def test_only_one_ticker_runs_per_site(tmp_path: Path) -> None:
    goals, (gid,) = _goals(tmp_path, "singleton")
    epochs = InMemorySchedulerEpochService(site_id="pursuit-ticker")
    engine = _engine(goals, tmp_path)
    first = engine.singleton_tick(SingletonTicker(epochs, holder_id="proc_a"))
    second = engine.singleton_tick(SingletonTicker(epochs, holder_id="proc_b"))
    assert first.ran and first.reason == "ok" and [r.goal_id for r in first.value] == [gid]
    assert not second.ran and second.reason == "epoch_held_by_other"


def test_product_store_run_pursuit_tick(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_V23_DURABLE", raising=False)
    store = ProductStore(repo_root=tmp_path, db_reachable=None)
    store.fixture_mode = True
    result = store.run_pursuit_tick()
    assert result.ran and result.reason == "ok" and result.value == []
