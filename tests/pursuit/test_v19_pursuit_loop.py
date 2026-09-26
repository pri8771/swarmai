"""V1.9 autonomous pursuit loop — deterministic, zero-spend tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.goals.models import Goal, GoalStatus, GoalStore
from swarm.pursuit import (
    ContributionKind,
    ExecutionOutcome,
    PursuitEngine,
    PursuitLearningError,
    PursuitLesson,
    PursuitLessonStore,
    PursuitScheduler,
    RecordingExecutor,
    admit_proposal,
    detect_stagnation,
)
from swarm.pursuit.models import MissionProposalDraft
from swarm.pursuit.policy import PursuitPolicyError
from swarm.pursuit.durable_accounting import InMemoryHoldStore

HEADERS = {"Authorization": "Bearer review-only-token"}


@pytest.fixture(autouse=True)
def _clear_swarm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("SWARM_"):
            monkeypatch.delenv(key, raising=False)


def _goal(tmp_path: Path, **kwargs: object) -> tuple[GoalStore, Goal]:
    store = GoalStore(tmp_path / "goals")
    defaults: dict[str, object] = {
        "project_id": "proj_pursuit",
        "desired_outcome": "Ship verified extract pipeline",
        "verification_criteria": ["contacts_extracted", "report_published"],
        "resource_envelope": {"spend_usd_ceiling": 0.0},
        "authority_envelope": {"tools": ["workspace.read"], "providers": ["fake"]},
        "strategy": "assume:single-pass-extract",
    }
    defaults.update(kwargs)
    goal = store.create(Goal(**defaults))  # type: ignore[arg-type]
    return store, goal


def _client(path: Path) -> TestClient:
    app = create_app(
        repo_root=path,
        seed_loopback_token="review-only-token",
        install_project_id="proj_pursuit",
        # None = no PG configured → file-backed pursuit durability allowed (PC-02).
        db_reachable=None,
    )
    return TestClient(app)


def test_full_loop_achieves_goal(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path)
    clock = {"t": 0.0}

    def now() -> float:
        return clock["t"]

    engine = PursuitEngine(
        goals,
        executor=RecordingExecutor(default_success=True),
        scheduler=PursuitScheduler(clock=now),
        clock=now,
    )
    c1 = engine.tick(goal.id, force=True)
    assert c1.decided_kind == ContributionKind.ACT
    assert c1.proposal is not None and c1.proposal.state == "admitted"
    assert c1.outcome is not None and c1.outcome.success
    assert c1.verification is not None and "contacts_extracted" in c1.verification.newly_met
    assert goal.id in {goals.get(goal.id).id}
    assert "msn_" in goals.get(goal.id).mission_ids[0]

    clock["t"] += 10.0
    c2 = engine.tick(goal.id, force=True)
    assert c2.decided_kind == ContributionKind.ACT
    refreshed = goals.get(goal.id)
    assert refreshed.status == GoalStatus.ACHIEVED
    assert len(refreshed.mission_ids) == 2
    assert refreshed.evidence_refs


def test_anti_duplicate_mission(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path, verification_criteria=["only_one"])
    executor = RecordingExecutor(
        default_success=True,
    )

    # Override execute to never satisfy criteria so the same ACT would recur.
    def _no_progress(proposal: MissionProposalDraft) -> ExecutionOutcome:
        executor.calls.append(proposal)
        return ExecutionOutcome(
            mission_id=proposal.mission_id or "msn_x",
            success=True,
            evidence_refs=[],
            satisfied_criteria=[],
            cost_usd=0.0,
        )

    executor.execute = _no_progress  # type: ignore[method-assign]
    clock = {"t": 0.0}
    engine = PursuitEngine(
        goals,
        executor=executor,
        scheduler=PursuitScheduler(clock=lambda: clock["t"]),
    )
    first = engine.tick(goal.id, force=True)
    assert first.proposal is not None and first.proposal.state == "admitted"
    clock["t"] += 100.0
    # Same unmet criterion + same approach title → duplicate.
    second = engine.tick(goal.id, force=True)
    assert second.proposal is not None
    assert second.proposal.state == "duplicate"
    assert second.notes == "duplicate_mission"


def test_rejects_budget_and_authority_expansion(tmp_path: Path) -> None:
    goals, goal = _goal(
        tmp_path,
        resource_envelope={"spend_usd_ceiling": 0.0},
        authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
    )
    draft = MissionProposalDraft(
        goal_id=goal.id,
        title="paid call",
        objective="x",
        kind=ContributionKind.ACT,
        dedupe_key="k1",
        requested_budget_usd=1.0,
        requested_tools=["workspace.read"],
        requested_providers=["fake"],
    )
    rejected = admit_proposal(goal, draft)
    assert rejected.state == "rejected"
    assert rejected.rejection_reason == "budget_exceeds_envelope"

    draft2 = MissionProposalDraft(
        goal_id=goal.id,
        title="shell escape",
        objective="x",
        kind=ContributionKind.ACT,
        dedupe_key="k2",
        requested_budget_usd=0.0,
        requested_tools=["shell.exec"],
        requested_providers=["fake"],
    )
    rejected2 = admit_proposal(goal, draft2)
    assert rejected2.state == "rejected"
    assert rejected2.rejection_reason == "tools_outside_authority"


def test_schedule_backoff_not_endless_polling(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path, verification_criteria=["c1"])
    clock = {"t": 0.0}
    executor = RecordingExecutor(default_success=False)
    engine = PursuitEngine(
        goals,
        executor=executor,
        scheduler=PursuitScheduler(clock=lambda: clock["t"]),
    )
    first = engine.tick(goal.id, force=True)
    assert first.outcome is not None and not first.outcome.success
    # Immediately again without force → not due (backoff).
    blocked = engine.tick(goal.id, force=False)
    assert blocked.notes == "not_due"
    assert blocked.phase.value == "stopped"
    # Advance past backoff.
    clock["t"] += engine.scheduler.get(goal.id).backoff_seconds + 0.1
    again = engine.tick(goal.id, force=False)
    assert again.notes != "not_due"


def test_stagnation_moves_goal_to_waiting(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path, verification_criteria=["c1"])
    clock = {"t": 0.0}
    # Fail with empty satisfied; mark approaches failed so engine experiments,
    # but force identical failure_class via custom executor for stagnation history.
    outcomes: dict[str, ExecutionOutcome] = {}
    executor = RecordingExecutor(outcomes=outcomes, default_success=False)
    engine = PursuitEngine(
        goals,
        executor=executor,
        scheduler=PursuitScheduler(clock=lambda: clock["t"]),
    )
    for i in range(3):
        clock["t"] = float(i * 10_000)
        engine.scheduler.force_due(goal.id)
        # Clear dedupe so identical act can be re-proposed after we forget failures path.
        engine._dedupe.clear()  # noqa: SLF001 — test harness
        engine._failed_approaches.get(goal.id, set()).clear()  # noqa: SLF001
        engine.tick(goal.id, force=True)

    # Seed stagnation by synthesizing repeated identical failure cycles.
    report = detect_stagnation(engine.history(goal.id), max_repeated_failures=3)
    assert report.stagnant is True

    clock["t"] += 10_000
    engine.scheduler.force_due(goal.id)
    # Make detect_stagnation trip on next tick via history already stagnant.
    cycle = engine.tick(goal.id, force=True)
    assert "stagnation" in cycle.notes
    assert goals.get(goal.id).status == GoalStatus.WAITING


def test_blockers_request_human(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path, blockers=["need dataset access"])
    engine = PursuitEngine(goals, executor=RecordingExecutor())
    cycle = engine.tick(goal.id, force=True)
    assert cycle.decided_kind == ContributionKind.REQUEST_HUMAN
    assert goals.get(goal.id).status == GoalStatus.BLOCKED


def test_learning_adopt_changes_strategy_and_rollback(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path, strategy="base")
    lessons = PursuitLessonStore()
    lesson = lessons.propose(
        PursuitLesson(
            goal_id=goal.id,
            summary="Prefer multi-pass extract",
            scope=["contacts_extracted"],
            strategy_delta="prefer:multi-pass",
            evidence_refs=["ev:1"],
        )
    )
    with pytest.raises(PursuitLearningError, match="holdout_plaintext"):
        lessons.evaluate(lesson.lesson_id, holdout_check_id="answer=42", holdout_passed=True)
    evaluated = lessons.evaluate(
        lesson.lesson_id, holdout_check_id="seal:holdout/v1#digest", holdout_passed=True
    )
    assert evaluated.state.value == "evaluated"
    adopted = lessons.adopt(lesson.lesson_id, current_strategy="base")
    assert adopted.state.value == "adopted"
    assert lessons.applied_strategy(goal.id, "base") == "base | prefer:multi-pass"

    engine = PursuitEngine(goals, lessons=lessons, executor=RecordingExecutor())
    # Adopted lesson boosts score for contacts_extracted act.
    cycle = engine.tick(goal.id, force=True)
    assert cycle.frontier
    top = cycle.frontier[0]
    assert "contacts_extracted" in top.addresses_criteria

    rolled = lessons.rollback(lesson.lesson_id)
    assert rolled.state.value == "rolled_back"
    assert lessons.applied_strategy(goal.id, "base") == "base"


def test_failed_approach_switches_to_experiment(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path, verification_criteria=["c1"])
    clock = {"t": 0.0}
    engine = PursuitEngine(
        goals,
        executor=RecordingExecutor(default_success=False),
        scheduler=PursuitScheduler(clock=lambda: clock["t"]),
    )
    first = engine.tick(goal.id, force=True)
    assert first.decided_kind == ContributionKind.ACT
    clock["t"] += 10_000
    engine.scheduler.force_due(goal.id)
    engine._dedupe.clear()  # noqa: SLF001 — allow new proposal after failure class change
    second = engine.tick(goal.id, force=True)
    assert second.decided_kind in {ContributionKind.EXPERIMENT, ContributionKind.ASK}


def test_pending_unknown_usage_hold_survives_terminal_reconciliation(tmp_path: Path) -> None:
    goals, goal = _goal(
        tmp_path,
        verification_criteria=["c1"],
        resource_envelope={"spend_usd_ceiling": 0.0, "max_model_calls": 1},
    )

    class PendingUnknownExecutor:
        def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome:
            assert proposal.mission_id is not None
            return ExecutionOutcome(
                mission_id=proposal.mission_id,
                success=False,
                failure_class="submitted_pending",
                model_calls=1,
                runtime="native",
                usage_unknown=True,
            )

        def reconcile(self, mission_id: str) -> ExecutionOutcome:
            return ExecutionOutcome(
                mission_id=mission_id,
                success=False,
                failure_class="mission_failed",
                runtime="native",
            )

    engine = PursuitEngine(
        goals,
        executor=PendingUnknownExecutor(),
        scheduler=PursuitScheduler(clock=lambda: 0.0),
        hold_store=InMemoryHoldStore(),
    )
    first = engine.tick(goal.id, force=True)
    assert first.outcome is not None and first.outcome.usage_unknown
    [hold] = engine.resource_ledger(goal.id).holds.values()
    assert hold.state == "unknown"

    engine.tick(goal.id, force=True)
    assert engine.resource_ledger(goal.id).holds[hold.hold_id].state == "unknown"


def test_pursuit_api_tick_and_lesson(tmp_path: Path) -> None:
    client = _client(tmp_path / "server")
    created = client.post(
        "/v1/goals",
        headers=HEADERS,
        json={
            "project_id": "proj_pursuit",
            "desired_outcome": "Finish pursuit demo",
            "verification_criteria": ["step_a"],
            "resource_envelope": {"spend_usd_ceiling": 0.0},
            "authority_envelope": {"tools": ["workspace.read"], "providers": ["fake"]},
        },
    )
    assert created.status_code == 200, created.text
    goal_id = created.json()["goal"]["id"]
    tick = client.post(
        f"/v1/goals/{goal_id}/pursuit/tick",
        headers=HEADERS,
        json={"force": True},
    )
    assert tick.status_code == 200, tick.text
    body = tick.json()
    assert body["cycle"]["decided_kind"] == "act"
    # R20-01: operational API must not achieve via RecordingExecutor.
    assert body["goal"]["status"] != "achieved"
    outcome = body["cycle"].get("outcome") or {}
    assert outcome.get("success") is False
    assert outcome.get("failure_class") == "submitted_pending"
    assert outcome.get("runtime") == "native"

    status = client.get(f"/v1/goals/{goal_id}/pursuit", headers=HEADERS)
    assert status.status_code == 200
    assert len(status.json()["history"]) >= 1

    lesson = client.post(
        f"/v1/goals/{goal_id}/pursuit/lessons",
        headers=HEADERS,
        json={
            "summary": "reuse fake provider",
            "scope": ["step_a"],
            "strategy_delta": "prefer:fake",
            "evidence_refs": ["ev:api"],
        },
    )
    assert lesson.status_code == 200
    lesson_id = lesson.json()["lesson"]["lesson_id"]
    evaluated = client.post(
        f"/v1/goals/{goal_id}/pursuit/lessons/{lesson_id}/evaluate",
        headers=HEADERS,
        json={"holdout_check_id": "seal:h1", "holdout_passed": True},
    )
    assert evaluated.status_code == 200
    adopted = client.post(
        f"/v1/goals/{goal_id}/pursuit/lessons/{lesson_id}/adopt",
        headers=HEADERS,
    )
    assert adopted.status_code == 200
    assert "prefer:fake" in adopted.json()["strategy"]
    rolled = client.post(
        f"/v1/goals/{goal_id}/pursuit/lessons/{lesson_id}/rollback",
        headers=HEADERS,
    )
    assert rolled.status_code == 200
    assert rolled.json()["lesson"]["state"] == "rolled_back"


def test_ongoing_goal_never_auto_achieved(tmp_path: Path) -> None:
    from swarm.goals.models import GoalKind

    goals, goal = _goal(
        tmp_path,
        kind=GoalKind.ONGOING,
        verification_criteria=["c1"],
    )
    engine = PursuitEngine(goals, executor=RecordingExecutor(default_success=True))
    cycle = engine.tick(goal.id, force=True)
    assert cycle.outcome is not None and cycle.outcome.success
    refreshed = goals.get(goal.id)
    assert refreshed.status == GoalStatus.ACTIVE
    assert refreshed.mission_outcomes
    assert refreshed.mission_outcomes[0]["outcome"] == "succeeded"


def test_negative_budget_raises() -> None:
    goal = Goal(
        project_id="p",
        desired_outcome="x",
        resource_envelope={"spend_usd_ceiling": 0.0},
        authority_envelope={},
    )
    draft = MissionProposalDraft(
        goal_id=goal.id,
        title="t",
        objective="o",
        kind=ContributionKind.ACT,
        dedupe_key="d",
        requested_budget_usd=-1.0,
    )
    with pytest.raises(PursuitPolicyError, match="negative_budget"):
        admit_proposal(goal, draft)
