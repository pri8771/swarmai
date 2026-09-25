"""V1.8 durable Goal lifecycle campaign — protected regressions.

Covers: fields, finite vs ongoing, transition rules, pause/resume/cancel/restart,
duplicate-trigger handling, mission≠achievement, retained decision history across
cold reopen.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.goals.models import (
    Goal,
    GoalError,
    GoalKind,
    GoalStatus,
    GoalStore,
    allowed_transitions,
)

HEADERS = {"Authorization": "Bearer review-only-token"}


@pytest.fixture(autouse=True)
def _clear_swarm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("SWARM_"):
            monkeypatch.delenv(key, raising=False)


def _client(path: Path) -> TestClient:
    app = create_app(
        repo_root=path,
        seed_loopback_token="review-only-token",
        install_project_id="proj_review",
        # None = no PG configured → file-backed goal durability allowed (PC-02).
        db_reachable=None,
    )
    return TestClient(app)


def test_goal_fields_and_transition_matrix() -> None:
    assert GoalStatus.ACHIEVED in allowed_transitions(GoalStatus.ACTIVE)
    assert GoalStatus.ACTIVE not in allowed_transitions(GoalStatus.CANCELLED)
    assert GoalStatus.ACTIVE in allowed_transitions(GoalStatus.PAUSED)
    assert not allowed_transitions(GoalStatus.EXPIRED)
    goal = Goal(
        project_id="proj_review",
        desired_outcome="Ship durable goals",
        verification_criteria=["lifecycle campaign green"],
        kind=GoalKind.FINITE,
        scope={"repos": ["pri8771/swarmai"]},
        constraints={"no_main_merge": True},
        resource_envelope={"max_missions": 3},
        authority_envelope={"tools": ["sandbox.fs"]},
        owner="operator",
        permitted_agents=["planner", "worker"],
        strategy="mission_chain",
        dependencies=["dep_infra"],
        stop_conditions=["budget_exhausted"],
        review_cadence="daily",
        expires_at=(datetime.now(UTC) + timedelta(days=7)).isoformat(),
        open_questions=["host gate?"],
        blockers=[],
    )
    dumped = goal.model_dump(mode="json")
    for key in (
        "desired_outcome",
        "verification_criteria",
        "kind",
        "scope",
        "constraints",
        "resource_envelope",
        "authority_envelope",
        "owner",
        "permitted_agents",
        "strategy",
        "dependencies",
        "stop_conditions",
        "review_cadence",
        "expires_at",
        "progress",
        "decision_history",
        "mission_outcomes",
        "trigger_receipts",
    ):
        assert key in dumped


def test_finite_vs_ongoing_and_mission_not_achievement(tmp_path: Path) -> None:
    store = GoalStore(tmp_path / "goals")
    finite = store.create(
        Goal(
            project_id="proj_review",
            desired_outcome="Finite extract complete",
            verification_criteria=["artifact verified"],
            kind=GoalKind.FINITE,
        )
    )
    ongoing = store.create(
        Goal(
            project_id="proj_review",
            desired_outcome="Keep parser green",
            verification_criteria=["no regressions"],
            kind=GoalKind.ONGOING,
        )
    )
    store.record_mission_outcome(
        finite.id,
        mission_id="msn_done",
        outcome="completed",
        actor="op",
        notes="mission accepted",
        evidence_refs=["art_1"],
    )
    after = store.get(finite.id)
    assert after.status == GoalStatus.ACTIVE
    assert after.mission_outcomes[-1]["outcome"] == "completed"
    assert "msn_done" in after.mission_ids
    assert "art_1" in after.evidence_refs

    achieved = store.transition(
        finite.id, GoalStatus.ACHIEVED, reason="criteria met", actor="op"
    )
    assert achieved.status == GoalStatus.ACHIEVED

    with pytest.raises(GoalError, match="ongoing_goal_cannot_achieve"):
        store.transition(
            ongoing.id, GoalStatus.ACHIEVED, reason="should fail", actor="op"
        )
    store.record_progress(
        ongoing.id, summary="cycle-1 ok", actor="op", metrics={"missions": 1}
    )
    assert store.get(ongoing.id).status == GoalStatus.ACTIVE
    assert len(store.get(ongoing.id).progress) == 1


def test_pause_resume_cancel_restart_retains_history(tmp_path: Path) -> None:
    store = GoalStore(tmp_path / "goals")
    goal = store.create(
        Goal(
            project_id="proj_review",
            desired_outcome="Recoverable goal",
            verification_criteria=["history retained"],
            kind=GoalKind.FINITE,
            blockers=["waiting_host"],
        )
    )
    paused = store.pause(goal.id, reason="operator pause", actor="op")
    assert paused.status == GoalStatus.PAUSED
    resumed = store.resume(goal.id, reason="resume", actor="op")
    assert resumed.status == GoalStatus.ACTIVE
    cancelled = store.cancel(goal.id, reason="abort", actor="op")
    assert cancelled.status == GoalStatus.CANCELLED
    with pytest.raises(GoalError, match="illegal_goal_transition"):
        store.transition(goal.id, GoalStatus.ACTIVE, reason="sneak", actor="op")
    restarted = store.restart(goal.id, reason="restart recovery", actor="op")
    assert restarted.status == GoalStatus.ACTIVE
    assert restarted.restart_count == 1
    assert restarted.blockers == []
    actions = [e.get("action") for e in restarted.decision_history]
    assert "create" in actions
    assert "pause" in actions
    assert "resume" in actions
    assert "cancel" in actions
    assert "restart" in actions
    history_len = len(restarted.decision_history)

    cold = GoalStore(tmp_path / "goals")
    recovered = cold.get(goal.id)
    assert recovered.status == GoalStatus.ACTIVE
    assert recovered.restart_count == 1
    assert len(recovered.decision_history) == history_len
    assert recovered.decision_history[-1]["action"] == "restart"


def test_duplicate_trigger_handling(tmp_path: Path) -> None:
    store = GoalStore(tmp_path / "goals")
    goal = store.create(
        Goal(
            project_id="proj_review",
            desired_outcome="Trigger dedupe",
            verification_criteria=["one receipt"],
            kind=GoalKind.ONGOING,
        )
    )
    g1, r1 = store.accept_trigger(
        goal.id,
        dedupe_key="sched:2026-09-25T00:00:00Z",
        trigger_kind="schedule",
        actor="scheduler",
        payload={"occurrence": 1},
    )
    assert r1["duplicate"] is False
    assert len(g1.trigger_receipts) == 1
    g2, r2 = store.accept_trigger(
        goal.id,
        dedupe_key="sched:2026-09-25T00:00:00Z",
        trigger_kind="schedule",
        actor="scheduler",
        payload={"occurrence": 1},
    )
    assert r2["duplicate"] is True
    assert r2["receipt_id"] == r1["receipt_id"]
    assert len(g2.trigger_receipts) == 1

    store.pause(goal.id, reason="hold", actor="op")
    with pytest.raises(GoalError, match="trigger_not_allowed"):
        store.accept_trigger(
            goal.id,
            dedupe_key="other",
            trigger_kind="manual",
            actor="op",
        )


def test_expiry_transition(tmp_path: Path) -> None:
    store = GoalStore(tmp_path / "goals")
    past = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    goal = store.create(
        Goal(
            project_id="proj_review",
            desired_outcome="Expiring goal",
            verification_criteria=["expires"],
            expires_at=past,
        )
    )
    expired = store.evaluate_expiry(goal.id, actor="system")
    assert expired.status == GoalStatus.EXPIRED
    with pytest.raises(GoalError, match="trigger_not_allowed"):
        store.accept_trigger(
            goal.id, dedupe_key="late", trigger_kind="manual", actor="op"
        )
    revived = store.restart(goal.id, reason="extend", actor="op")
    assert revived.status == GoalStatus.ACTIVE


def test_goal_api_lifecycle_campaign(tmp_path: Path) -> None:
    client = _client(tmp_path / "server")
    created = client.post(
        "/v1/goals",
        headers=HEADERS,
        json={
            "project_id": "proj_review",
            "desired_outcome": "V1.8 lifecycle campaign",
            "verification_criteria": ["pause resume cancel restart", "dedupe"],
            "kind": "finite",
            "dependencies": ["dep_pg"],
            "resource_envelope": {"max_usd": 0},
            "authority_envelope": {"spawn": False},
            "stop_conditions": ["operator_cancel"],
            "review_cadence": "on_mission",
            "idempotency_key": "goal-create-1",
        },
    )
    assert created.status_code == 200, created.text
    goal = created.json()["goal"]
    goal_id = goal["id"]
    assert goal["kind"] == "finite"
    assert goal["dependencies"] == ["dep_pg"]
    assert len(goal["decision_history"]) >= 1

    # Idempotent create
    again = client.post(
        "/v1/goals",
        headers={**HEADERS, "Idempotency-Key": "goal-create-1"},
        json={
            "project_id": "proj_review",
            "desired_outcome": "V1.8 lifecycle campaign",
            "verification_criteria": ["pause resume cancel restart", "dedupe"],
            "kind": "finite",
            "dependencies": ["dep_pg"],
            "resource_envelope": {"max_usd": 0},
            "authority_envelope": {"spawn": False},
            "stop_conditions": ["operator_cancel"],
            "review_cadence": "on_mission",
            "idempotency_key": "goal-create-1",
        },
    )
    assert again.status_code == 200
    assert again.json()["goal"]["id"] == goal_id

    paused = client.post(
        f"/v1/goals/{goal_id}/pause",
        headers=HEADERS,
        json={"reason": "hold"},
    )
    assert paused.status_code == 200
    assert paused.json()["goal"]["status"] == "paused"

    resumed = client.post(
        f"/v1/goals/{goal_id}/resume",
        headers=HEADERS,
        json={"reason": "continue"},
    )
    assert resumed.status_code == 200
    assert resumed.json()["goal"]["status"] == "active"

    trig = client.post(
        f"/v1/goals/{goal_id}/triggers",
        headers=HEADERS,
        json={"dedupe_key": "evt-1", "trigger_kind": "manual"},
    )
    assert trig.status_code == 200
    assert trig.json()["receipt"]["duplicate"] is False
    trig2 = client.post(
        f"/v1/goals/{goal_id}/triggers",
        headers=HEADERS,
        json={"dedupe_key": "evt-1", "trigger_kind": "manual"},
    )
    assert trig2.status_code == 200
    assert trig2.json()["receipt"]["duplicate"] is True

    outcome = client.post(
        f"/v1/goals/{goal_id}/mission-outcomes",
        headers=HEADERS,
        json={
            "mission_id": "msn_api_1",
            "outcome": "completed",
            "notes": "mission done",
            "evidence_refs": ["art_x"],
        },
    )
    assert outcome.status_code == 200
    body = outcome.json()
    assert body["mission_completion_implies_goal_achievement"] is False
    assert body["goal"]["status"] == "active"
    assert body["goal"]["mission_outcomes"][-1]["mission_id"] == "msn_api_1"

    prog = client.post(
        f"/v1/goals/{goal_id}/progress",
        headers=HEADERS,
        json={"summary": "halfway", "metrics": {"pct": 50}},
    )
    assert prog.status_code == 200
    assert prog.json()["goal"]["progress"][-1]["summary"] == "halfway"

    cancelled = client.post(
        f"/v1/goals/{goal_id}/cancel",
        headers=HEADERS,
        json={"reason": "operator cancel"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["goal"]["status"] == "cancelled"

    bad = client.post(
        f"/v1/goals/{goal_id}/transition",
        headers=HEADERS,
        json={"status": "active", "reason": "illegal"},
    )
    assert bad.status_code == 409

    restarted = client.post(
        f"/v1/goals/{goal_id}/restart",
        headers=HEADERS,
        json={"reason": "restart recovery"},
    )
    assert restarted.status_code == 200
    assert restarted.json()["goal"]["status"] == "active"
    assert restarted.json()["goal"]["restart_count"] == 1
    history = restarted.json()["goal"]["decision_history"]
    assert any(e.get("action") == "restart" for e in history)

    # Cold reopen via new app instance on same repo root
    cold = _client(tmp_path / "server")
    got = cold.get(f"/v1/goals/{goal_id}", headers=HEADERS)
    assert got.status_code == 200
    recovered = got.json()["goal"]
    assert recovered["status"] == "active"
    assert recovered["restart_count"] == 1
    assert len(recovered["decision_history"]) == len(history)
    assert recovered["mission_outcomes"][-1]["outcome"] == "completed"

    # Persistence file schema
    path = tmp_path / "server" / "var" / "goals" / "goals.json"
    assert path.is_file()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["schema_version"] == "1.8"
    assert any(g["id"] == goal_id for g in raw["goals"])


def test_ongoing_api_rejects_achieve(tmp_path: Path) -> None:
    client = _client(tmp_path / "server")
    created = client.post(
        "/v1/goals",
        headers=HEADERS,
        json={
            "project_id": "proj_review",
            "desired_outcome": "Ongoing watch",
            "verification_criteria": ["cycles continue"],
            "kind": "ongoing",
        },
    )
    assert created.status_code == 200
    goal_id = created.json()["goal"]["id"]
    denied = client.post(
        f"/v1/goals/{goal_id}/transition",
        headers=HEADERS,
        json={"status": "achieved", "reason": "nope"},
    )
    assert denied.status_code == 409
    assert "ongoing_goal_cannot_achieve" in denied.text
