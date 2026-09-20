"""P11 mission controller and scheduler tests."""

from __future__ import annotations

import pytest

from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.contracts.mission import TaskAttempt
from swarm.controller.graph import validate_proposal
from swarm.controller.mission import MissionController, spawn_proposal
from swarm.controller.scheduler import AdaptiveScheduler, SchedulerConfig


@pytest.mark.asyncio
async def test_two_planners_and_spawn() -> None:
    ctrl = MissionController(inference_slots=4, worker_slots=4)
    mission = await ctrl.submit_mission(sample_mission())
    # Planner A and B propose different children.
    child_a = sample_task().model_copy(
        update={"id": "task_child_a", "objective": "extract A", "status": TaskStatus.PROPOSED}
    )
    child_b = sample_task().model_copy(
        update={"id": "task_child_b", "objective": "extract B", "status": TaskStatus.PROPOSED}
    )
    pa = spawn_proposal(mission, author_session_id="as_planner_a", parent=None, children=[child_a])
    pb = spawn_proposal(mission, author_session_id="as_planner_b", parent=None, children=[child_b])
    await ctrl.propose_graph_change(pa)
    await ctrl.propose_graph_change(pb)
    rev = await ctrl.commit_validated_revision(pa.proposal_id)
    assert rev == 2
    # Re-base planner B on current revision (optimistic concurrency).
    mission = ctrl.missions[mission.id]
    pb2 = pb.model_copy(update={"based_on_revision": mission.revision})
    await ctrl.propose_graph_change(pb2)
    await ctrl.commit_validated_revision(pb2.proposal_id)
    ready = await ctrl.choose_ready_work(mission.id)
    assert len(ready) >= 1
    assert {t.id for t in ctrl.tasks[mission.id].values()} >= {"task_child_a", "task_child_b"}


@pytest.mark.asyncio
async def test_cycle_rejected() -> None:
    ctrl = MissionController()
    mission = await ctrl.submit_mission(sample_mission())
    t1 = sample_task().model_copy(update={"id": "t1", "dependency_ids": ["t2"]})
    t2 = sample_task().model_copy(update={"id": "t2", "dependency_ids": ["t1"]})
    prop = spawn_proposal(mission, author_session_id="as_x", parent=None, children=[t1, t2])
    await ctrl.propose_graph_change(prop)
    with pytest.raises(ValueError, match="cycle"):
        await ctrl.commit_validated_revision(prop.proposal_id)


@pytest.mark.asyncio
async def test_duplicate_merged() -> None:
    ctrl = MissionController()
    mission = await ctrl.submit_mission(sample_mission())
    child = sample_task().model_copy(update={"id": "task_dup_1", "objective": "same work"})
    p1 = spawn_proposal(mission, author_session_id="a", parent=None, children=[child])
    await ctrl.propose_graph_change(p1)
    await ctrl.commit_validated_revision(p1.proposal_id)
    # Refresh mission revision for second proposal
    mission = ctrl.missions[mission.id]
    child2 = sample_task().model_copy(
        update={"id": "task_dup_2", "objective": "same work", "task_family": child.task_family}
    )
    p2 = spawn_proposal(mission, author_session_id="b", parent=None, children=[child2])
    await ctrl.propose_graph_change(p2)
    # Duplicate merge returns without raising; revision unchanged path
    result = validate_proposal(
        p2,
        tasks=ctrl.tasks[mission.id],
        mission_revision=mission.revision,
        mission_scopes=set(mission.data_scope_ids),
        max_graph_nodes=mission.max_graph_nodes,
    )
    assert result.accepted is False
    assert result.merged_into == "task_dup_1"


@pytest.mark.asyncio
async def test_insufficient_inference_contracts_concurrency() -> None:
    ctrl = MissionController(inference_slots=1, worker_slots=10)
    ctrl.scheduler = AdaptiveScheduler(config=SchedulerConfig(control_reserve_slots=0, max_concurrency=1))
    mission = await ctrl.submit_mission(sample_mission())
    kids = [
        sample_task().model_copy(update={"id": f"task_k{i}", "objective": f"k{i}"})
        for i in range(5)
    ]
    prop = spawn_proposal(mission, author_session_id="a", parent=None, children=kids)
    await ctrl.propose_graph_change(prop)
    await ctrl.commit_validated_revision(prop.proposal_id)
    ready = await ctrl.choose_ready_work(mission.id)
    assert len(ready) <= 1


@pytest.mark.asyncio
async def test_capacity_increase_expands_work() -> None:
    ctrl = MissionController(inference_slots=1, worker_slots=1)
    ctrl.scheduler = AdaptiveScheduler(config=SchedulerConfig(control_reserve_slots=0, max_concurrency=8))
    mission = await ctrl.submit_mission(sample_mission())
    kids = [
        sample_task().model_copy(update={"id": f"task_e{i}", "objective": f"e{i}"})
        for i in range(4)
    ]
    prop = spawn_proposal(mission, author_session_id="a", parent=None, children=kids)
    await ctrl.propose_graph_change(prop)
    await ctrl.commit_validated_revision(prop.proposal_id)
    first = await ctrl.choose_ready_work(mission.id)
    ctrl.expand_capacity(4, 4)
    second = await ctrl.choose_ready_work(mission.id)
    assert len(second) >= len(first)


@pytest.mark.asyncio
async def test_no_oscillation_on_short_overload() -> None:
    sched = AdaptiveScheduler(config=SchedulerConfig(overload_cooldown_ticks=3, control_reserve_slots=0))
    mission = sample_mission()
    tasks = [
        sample_task().model_copy(update={"id": f"t{i}", "status": TaskStatus.READY, "objective": f"o{i}"})
        for i in range(6)
    ]
    sched.note_overload()
    selected1, exp1 = sched.choose_ready(mission, tasks, inference_slots=6, worker_slots=6)
    selected2, exp2 = sched.choose_ready(mission, tasks, inference_slots=6, worker_slots=6)
    assert exp1["hysteresis_hold"] is True
    assert exp2["hysteresis_hold"] is True
    assert len(selected1) <= 3


@pytest.mark.asyncio
async def test_verification_required_for_completion() -> None:
    ctrl = MissionController()
    mission = await ctrl.submit_mission(sample_mission())
    task = sample_task().model_copy(update={"id": "task_v1", "status": TaskStatus.READY})
    prop = spawn_proposal(mission, author_session_id="a", parent=None, children=[task])
    await ctrl.propose_graph_change(prop)
    await ctrl.commit_validated_revision(prop.proposal_id)
    # Mark accepted without verification — must not complete.
    ctrl.tasks[mission.id]["task_v1"] = task.model_copy(update={"status": TaskStatus.ACCEPTED})
    out = ctrl.try_complete(mission.id)
    assert out.status != MissionStatus.COMPLETED
    attempt = TaskAttempt(task_id="task_v1", agent_profile_id="ap")
    ctrl.register_attempt(attempt)
    await ctrl.record_verification(attempt.attempt_id, "vr_1")
    out2 = ctrl.try_complete(mission.id)
    assert out2.status == MissionStatus.COMPLETED


@pytest.mark.asyncio
async def test_privacy_wait_not_weaken() -> None:
    sched = AdaptiveScheduler(config=SchedulerConfig(control_reserve_slots=0))
    mission = sample_mission()
    tasks = [sample_task().model_copy(update={"status": TaskStatus.READY})]
    selected, exp = sched.choose_ready(
        mission, tasks, inference_slots=4, worker_slots=4, privacy_ok=False
    )
    assert selected == []
    assert exp["reason"] == "waiting_privacy_constraint"
