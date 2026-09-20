"""V0.4 memory / recovery tests."""

from __future__ import annotations

from pathlib import Path

from swarm.memory.store import (
    MemoryRecord,
    MemoryStore,
    build_recovery_plan,
    interrupt_mission,
    performance_memory_for_routing,
    resume_mission,
    retrieve_context,
)
from swarm.mission.store import MissionRecord, MissionStore


def test_durable_vs_transient_and_budget(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "mem")
    store.append(
        MemoryRecord(
            memory_id="m1",
            project_id="p",
            mission_id="x",
            kind="durable_fact",
            topic="mission_goal",
            content="fix parser off-by-one",
            provenance="t",
            tokens_estimate=10,
            confidence=1.0,
            tags=["goal"],
        )
    )
    store.append(
        MemoryRecord(
            memory_id="m2",
            project_id="p",
            mission_id="x",
            kind="transient_context",
            topic="noise",
            content="ephemeral detail " * 50,
            provenance="t",
            tokens_estimate=200,
            confidence=0.2,
            tags=["timeline"],
        )
    )
    ctx = retrieve_context(store, query="fix parser", token_budget=50, include_transient=False)
    assert ctx["tokens_used"] <= 50
    assert all(i["kind"] != "transient_context" for i in ctx["items"])
    assert ctx["items"]


def test_interrupt_resume_skips_accepted(tmp_path: Path) -> None:
    ms = MissionStore(tmp_path / "missions")
    rec = MissionRecord(
        mission_id="mid1",
        goal="fix bug",
        status="running",
        created_at="t0",
        updated_at="t0",
        tasks=[
            {"id": "t_inspect", "task_family": "inspect", "status": "accepted", "ok": True, "objective": "inspect"},
            {"id": "t_impl", "task_family": "implement", "status": "running", "ok": None, "objective": "impl"},
            {"id": "t_dup", "task_family": "implement", "status": "ready", "ok": None, "objective": "impl"},
        ],
    )
    ms.save(rec)
    interrupted = interrupt_mission(ms, "mid1")
    assert interrupted.status == "interrupted"
    plan = build_recovery_plan(interrupted)
    assert "t_impl" in plan.resume_from_task_ids or plan.action == "resume"
    resumed, plan2 = resume_mission(ms, "mid1")
    assert resumed.status == "running"
    inspect = next(t for t in resumed.tasks if t["id"] == "t_inspect")
    assert inspect["status"] == "accepted"
    assert plan2.skipped_duplicate_objectives.count("impl") >= 1


def test_routing_memory_does_not_rewrite_safety(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "mem")
    store.append(
        MemoryRecord(
            memory_id="m",
            project_id="p",
            mission_id="x",
            kind="model_obs",
            topic="model_assignment",
            content='{"model":"gemma3:4b","task_id":"t"}',
            provenance="t",
            tokens_estimate=10,
            tags=["routing", "gemma3:4b"],
        )
    )
    perf = performance_memory_for_routing(store, task_family="implement")
    assert perf["safety_policy_unchanged"] is True
    assert perf["preferred_model"] == "gemma3:4b"
