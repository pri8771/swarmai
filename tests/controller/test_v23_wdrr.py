"""SW-W1-S1: weighted deficit round-robin selector (offline, deterministic)."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from swarm.contracts.v23 import (
    MissionQueueLifecycle,
    MissionQueueState,
    PriorityClass,
    ProjectQueueState,
    ReasonCode,
    SchedulableTask,
    SchedulerDecision,
)
from swarm.scheduling.wdrr import (
    WdrrConfig,
    apply_selection,
    clamp_restart_credit,
    select_next,
)

NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)
REPO = Path(__file__).resolve().parents[2]


def _project(pid: str, weight: float = 1.0, **kw: object) -> ProjectQueueState:
    return ProjectQueueState(project_id=pid, weight=weight, max_concurrency=10_000, **kw)


def _mission(mid: str, pid: str, **kw: object) -> MissionQueueState:
    kw.setdefault("max_parallelism", 10_000)
    return MissionQueueState(mission_id=mid, project_id=pid, enqueued_at=NOW, **kw)


def _task(tid: str, mid: str, pid: str, **kw: object) -> SchedulableTask:
    kw.setdefault("enqueued_at", NOW)
    return SchedulableTask(task_id=tid, mission_id=mid, project_id=pid, **kw)


def _simulate(
    projects: list[ProjectQueueState],
    missions: list[MissionQueueState],
    tasks: list[SchedulableTask],
    rounds: int,
) -> Counter[str]:
    """Each admitted task completes immediately and is replaced (infinite backlog)."""
    served: Counter[str] = Counter()
    for seq in range(1, rounds + 1):
        sel = select_next(projects, missions, tasks, now=NOW)
        assert sel.decision == SchedulerDecision.ADMIT
        assert sel.project_id is not None
        served[sel.project_id] += 1
        projects, missions = apply_selection(projects, missions, sel, sequence=seq)
        projects = [p.model_copy(update={"running": 0}) for p in projects]
        missions = [m.model_copy(update={"running": 0}) for m in missions]
    return served


def test_policy_file_loads() -> None:
    cfg = WdrrConfig.from_policy_file(REPO / "config" / "v23" / "scheduler_policy.v1.json")
    assert cfg.policy_version == "v23-wdrr-1"
    assert cfg.base_quantum == 1.0


def test_long_run_share_proportional_to_weight() -> None:
    weights = {"proj_a": 1.0, "proj_b": 2.0, "proj_c": 3.0}
    projects = [_project(p, w) for p, w in weights.items()]
    missions = [_mission(f"msn_{p}", p) for p in weights]
    tasks = [_task(f"tsk_{p}", f"msn_{p}", p) for p in weights]
    served = _simulate(projects, missions, tasks, rounds=600)
    total_w = sum(weights.values())
    for pid, w in weights.items():
        expected = 600 * w / total_w
        assert abs(served[pid] - expected) <= 0.15 * expected, (pid, served)


def test_more_missions_do_not_amplify_project_share() -> None:
    projects = [_project("proj_many"), _project("proj_one")]
    missions = [_mission(f"msn_many_{i}", "proj_many") for i in range(10)]
    missions.append(_mission("msn_one", "proj_one"))
    tasks = [_task(f"tsk_many_{i}", f"msn_many_{i}", "proj_many") for i in range(10)]
    tasks.append(_task("tsk_one", "msn_one", "proj_one"))
    served = _simulate(projects, missions, tasks, rounds=400)
    assert abs(served["proj_many"] - 200) <= 30
    assert abs(served["proj_one"] - 200) <= 30


def test_low_weight_project_is_not_starved() -> None:
    projects = [_project("proj_small", 0.1), _project("proj_big", 10.0)]
    missions = [_mission("msn_s", "proj_small"), _mission("msn_b", "proj_big")]
    tasks = [_task("tsk_s", "msn_s", "proj_small"), _task("tsk_b", "msn_b", "proj_big")]
    served = _simulate(projects, missions, tasks, rounds=1000)
    assert served["proj_small"] >= 5


def test_blocked_work_does_not_accrue_credit() -> None:
    projects = [_project("proj_a"), _project("proj_blocked")]
    missions = [_mission("msn_a", "proj_a"), _mission("msn_x", "proj_blocked")]
    tasks = [
        _task("tsk_a", "msn_a", "proj_a"),
        _task("tsk_x", "msn_x", "proj_blocked", dependencies_ready=False),
    ]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.project_id == "proj_a"
    assert sel.credits_after["proj_blocked"] == 0.0


def test_stale_cancellation_generation_is_never_selected() -> None:
    projects = [_project("proj_a")]
    missions = [_mission("msn_a", "proj_a", cancellation_generation=2)]
    tasks = [_task("tsk_old", "msn_a", "proj_a", cancellation_generation=1)]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.decision == SchedulerDecision.IDLE
    assert sel.blocked["tsk_old"] == ReasonCode.CANCELLED_GENERATION.value


def test_paused_project_and_caps_are_excluded() -> None:
    projects = [
        _project("proj_paused", paused=True),
        ProjectQueueState(project_id="proj_full", max_concurrency=1, running=1),
    ]
    missions = [_mission("msn_p", "proj_paused"), _mission("msn_f", "proj_full")]
    tasks = [_task("tsk_p", "msn_p", "proj_paused"), _task("tsk_f", "msn_f", "proj_full")]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.decision == SchedulerDecision.DEFER
    assert sel.reason_code == ReasonCode.PROJECT_CONCURRENCY_CAP
    assert sel.blocked["proj_paused"] == ReasonCode.DRAINING.value


def test_draining_mission_is_not_selected() -> None:
    projects = [_project("proj_a")]
    missions = [_mission("msn_a", "proj_a", lifecycle=MissionQueueLifecycle.DRAINING)]
    tasks = [_task("tsk_a", "msn_a", "proj_a")]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.decision == SchedulerDecision.IDLE
    assert sel.blocked["tsk_a"] == ReasonCode.DRAINING.value


def test_resource_unavailable_defers() -> None:
    projects = [_project("proj_a")]
    missions = [_mission("msn_a", "proj_a")]
    tasks = [_task("tsk_a", "msn_a", "proj_a")]
    sel = select_next(projects, missions, tasks, now=NOW, resource_available=lambda t: False)
    assert sel.decision == SchedulerDecision.DEFER
    assert sel.reason_code == ReasonCode.DEFERRED_RESOURCE_UNAVAILABLE


def test_idle_when_no_work() -> None:
    sel = select_next([_project("proj_a")], [], [], now=NOW)
    assert sel.decision == SchedulerDecision.IDLE
    assert sel.reason_code == ReasonCode.NO_ELIGIBLE_WORK


def test_deterministic_and_inputs_not_mutated() -> None:
    projects = [_project("proj_a"), _project("proj_b")]
    missions = [_mission("msn_a", "proj_a"), _mission("msn_b", "proj_b")]
    tasks = [_task("tsk_a", "msn_a", "proj_a"), _task("tsk_b", "msn_b", "proj_b")]
    before = [x.model_dump() for x in [*projects, *missions, *tasks]]
    first = select_next(projects, missions, tasks, now=NOW)
    second = select_next(list(reversed(projects)), missions, list(reversed(tasks)), now=NOW)
    assert first.project_id == second.project_id == "proj_a"
    assert first.candidate_set_hash == second.candidate_set_hash
    assert [x.model_dump() for x in [*projects, *missions, *tasks]] == before


def test_urgent_bonus_is_bounded() -> None:
    projects = [_project("proj_urgent"), _project("proj_normal")]
    missions = [
        _mission("msn_u", "proj_urgent", priority=PriorityClass.URGENT),
        _mission("msn_n", "proj_normal"),
    ]
    tasks = [_task("tsk_u", "msn_u", "proj_urgent"), _task("tsk_n", "msn_n", "proj_normal")]
    served = _simulate(projects, missions, tasks, rounds=400)
    assert served["proj_normal"] >= 150
    assert served["proj_urgent"] <= 250


def test_near_deadline_mission_wins_tie() -> None:
    projects = [_project("proj_a")]
    missions = [
        _mission("msn_late", "proj_a", deadline_at=NOW + timedelta(hours=5)),
        _mission("msn_soon", "proj_a", deadline_at=NOW + timedelta(minutes=1)),
    ]
    tasks = [_task("tsk_l", "msn_late", "proj_a"), _task("tsk_s", "msn_soon", "proj_a")]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.mission_id == "msn_soon"


def test_task_order_within_mission() -> None:
    projects = [_project("proj_a")]
    missions = [_mission("msn_a", "proj_a")]
    tasks = [
        _task("tsk_2", "msn_a", "proj_a", priority=1, enqueued_at=NOW),
        _task("tsk_1", "msn_a", "proj_a", priority=5, enqueued_at=NOW + timedelta(seconds=9)),
    ]
    sel = select_next(projects, missions, tasks, now=NOW + timedelta(seconds=10))
    assert sel.task is not None and sel.task.task_id == "tsk_1"


def test_restart_clamps_positive_credit_only() -> None:
    projects = [_project("proj_rich", credit=500.0), _project("proj_debt", credit=-50.0)]
    clamped = {p.project_id: p.credit for p in clamp_restart_credit(projects)}
    assert clamped["proj_rich"] == 10.0
    assert clamped["proj_debt"] == -50.0
