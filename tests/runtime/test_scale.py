"""V0.3 backpressure + scale unit tests."""

from __future__ import annotations

from pathlib import Path

from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.runtime.backpressure import ProviderQuota, make_scale_scheduler
from swarm.runtime.scale import (
    AgentResult,
    LightAgent,
    bounded_consensus,
    detect_duplicate_work,
    isolate_failures,
    run_scale_mission,
)


def test_provider_quota_backpressure() -> None:
    q = ProviderQuota("ollama", max_in_flight=2, max_per_minute=100)
    assert q.try_acquire()
    assert q.try_acquire()
    assert not q.try_acquire()
    q.release()
    assert q.try_acquire()


def test_scheduler_rejects_when_queue_full() -> None:
    sched = make_scale_scheduler(max_concurrency=2)
    sched.max_queue = 2
    mission = sample_mission()
    assert sched.enqueue(sample_task().model_copy(update={"id": "t1"}))
    assert sched.enqueue(sample_task().model_copy(update={"id": "t2"}))
    assert not sched.enqueue(sample_task().model_copy(update={"id": "t3"}))
    assert sched.rejected_backpressure == 1
    assert sched.cancel("t1")
    dispatched, expl = sched.dispatch(mission, inference_slots=2, worker_slots=2)
    assert expl["queue_depth"] >= 0
    assert isinstance(dispatched, list)


def test_dedup_and_consensus() -> None:
    repo = Path(".")
    a = LightAgent("ag1", "worker", 0)
    b = LightAgent("ag2", "worker", 1)
    t1 = sample_task().model_copy(update={"id": "a"})
    t2 = sample_task().model_copy(update={"id": "b"})
    p = repo / "README.md"
    unique, dupes = detect_duplicate_work([(a, t1, p), (b, t2, p)])
    assert dupes == 1
    assert len(unique) == 1
    results = [
        AgentResult("ag1", "a", True, "ok"),
        AgentResult("ag2", "b", True, "ok"),
        AgentResult("ag3", "c", False, "bad", error_class="Boom"),
        AgentResult("ag4", "d", False, "bad", error_class="Boom"),
        AgentResult("ag5", "e", False, "bad", error_class="Boom"),
    ]
    isolated = isolate_failures(results)
    assert sum(1 for r in isolated if r.isolated) == 3
    decision = bounded_consensus(isolated)
    assert decision["decision"] in {"accept", "reject"}


def test_run_scale_mission_dozens(tmp_path: Path) -> None:
    # Minimal repo tree for targets.
    src = tmp_path / "src" / "swarm"
    src.mkdir(parents=True)
    for i in range(20):
        (src / f"m{i}.py").write_text(f"x={i}\n")
    (tmp_path / "sandbox").mkdir()
    report = run_scale_mission(
        repo=tmp_path,
        agent_count=40,
        max_concurrency=8,
        use_supervisor_model=False,
        out_dir=tmp_path / "out",
    )
    assert report.agent_count == 40
    assert report.completed >= 20
    assert report.duplicates_suppressed >= 1
    assert report.total_cost_usd == 0.0
    assert report.consensus["decision"] == "accept"
    assert (tmp_path / "out" / "latest_scale_mission.json").exists()
