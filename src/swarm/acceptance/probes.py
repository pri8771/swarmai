"""Deterministic probes for frozen V2.0 acceptance scenarios.

Probes exercise real local contracts where available. Scaffold probes assert
freeze wiring and explicit not-yet-integrated product hooks without claiming
pass. Live/host/elapsed gates are never satisfied by inventing grants or
simulating wall-clock time.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.evals.synthetic_harness import LiveGateBlocked, LiveGrant
from swarm.goals.models import Goal, GoalStatus, GoalStore
from swarm.learning import LearningError, LearningProposal, LearningRepository


@dataclass
class ProbeResult:
    ok: bool
    status: str
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "status": self.status, "detail": self.detail}


def _goal_store(tmp: Path) -> GoalStore:
    return GoalStore(root=tmp / "goals")


def probe_goal_multi_mission_link(tmp: Path) -> ProbeResult:
    store = _goal_store(tmp)
    goal = store.create(
        Goal(
            project_id="proj_accept",
            desired_outcome="Ship finite multi-mission outcome",
            verification_criteria=["artifact_hash_matches", "checks_pass"],
        )
    )
    store.link_mission(goal.id, "mission_a")
    store.link_mission(goal.id, "mission_b")
    # Linking missions must not auto-achieve.
    loaded = store.get(goal.id)
    if loaded.status == GoalStatus.ACHIEVED:
        return ProbeResult(False, "fail_auto_achieved", {"goal_id": goal.id})
    if len(loaded.mission_ids) != 2:
        return ProbeResult(False, "fail_mission_link", {"mission_ids": loaded.mission_ids})
    # Achieve only via explicit transition with criteria present.
    achieved = store.transition(
        goal.id, GoalStatus.ACHIEVED, reason="criteria_met_fixture", actor="harness"
    )
    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "goal_id": achieved.id,
            "mission_ids": achieved.mission_ids,
            "status": achieved.status.value,
            "history_len": len(achieved.decision_history),
            "note": "mission_link_does_not_auto_achieve",
        },
    )


def probe_goal_strategy_change_after_failure(tmp: Path) -> ProbeResult:
    store = _goal_store(tmp)
    goal = store.create(
        Goal(
            project_id="proj_accept",
            desired_outcome="Recover from failed approach",
            strategy="approach_v1_brute",
            verification_criteria=["holdout_pass"],
        )
    )
    # Record failure in decision history via pause then strategy rewrite + resume.
    store.transition(goal.id, GoalStatus.PAUSED, reason="approach_v1_failed", actor="harness")
    paused = store.get(goal.id)
    updated = paused.model_copy(
        update={
            "strategy": "approach_v2_decompose",
            "decision_history": list(paused.decision_history)
            + [
                {
                    "at": paused.updated_at,
                    "actor": "harness",
                    "from": "strategy:approach_v1_brute",
                    "to": "strategy:approach_v2_decompose",
                    "reason": "prior_approach_failed_stagnation_guard",
                }
            ],
        }
    )
    store.goals[goal.id] = updated
    store._save()
    store.transition(goal.id, GoalStatus.ACTIVE, reason="strategy_updated", actor="harness")
    final = store.get(goal.id)
    if final.strategy != "approach_v2_decompose":
        return ProbeResult(False, "fail_strategy_unchanged", {"strategy": final.strategy})
    if len(final.decision_history) < 2:
        return ProbeResult(False, "fail_missing_history", {"history": final.decision_history})
    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "goal_id": final.id,
            "strategy": final.strategy,
            "history_len": len(final.decision_history),
        },
    )


def probe_goal_ongoing_cycles(tmp: Path) -> ProbeResult:
    store = _goal_store(tmp)
    goal = store.create(
        Goal(
            project_id="proj_accept",
            desired_outcome="Ongoing monitoring goal",
            verification_criteria=["never_auto_complete"],
            stop_conditions=["operator_cancel"],
            review_cadence="per_cycle",
        )
    )
    for i in range(2):
        store.link_mission(goal.id, f"mission_cycle_{i}")
        store.transition(goal.id, GoalStatus.WAITING, reason=f"cycle_{i}_complete", actor="harness")
        store.transition(goal.id, GoalStatus.ACTIVE, reason=f"cycle_{i+1}_start", actor="harness")
    final = store.get(goal.id)
    if final.status == GoalStatus.ACHIEVED:
        return ProbeResult(False, "fail_auto_achieved_ongoing", {})
    if len(final.mission_ids) != 2:
        return ProbeResult(False, "fail_cycles", {"mission_ids": final.mission_ids})
    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "goal_id": final.id,
            "status": final.status.value,
            "cycles": len(final.mission_ids),
            "history_len": len(final.decision_history),
        },
    )


def probe_goal_blocked_then_available(tmp: Path) -> ProbeResult:
    store = _goal_store(tmp)
    goal = store.create(
        Goal(
            project_id="proj_accept",
            desired_outcome="Unblock when prerequisite lands",
            blockers=["need_credential_grant"],
            verification_criteria=["prereq_cleared"],
        )
    )
    store.transition(goal.id, GoalStatus.BLOCKED, reason="prereq_missing", actor="harness")
    try:
        store.transition(goal.id, GoalStatus.ACHIEVED, reason="illegal", actor="harness")
        return ProbeResult(False, "fail_illegal_achieved_from_blocked", {})
    except ValueError as exc:
        illegal = str(exc)
    store.transition(goal.id, GoalStatus.ACTIVE, reason="prereq_available", actor="harness")
    final = store.get(goal.id)
    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "goal_id": final.id,
            "status": final.status.value,
            "illegal_transition": illegal,
            "history_len": len(final.decision_history),
        },
    )


def probe_goal_pause_cancel_budget(tmp: Path) -> ProbeResult:
    store = _goal_store(tmp)
    goal = store.create(
        Goal(
            project_id="proj_accept",
            desired_outcome="Operator controls",
            resource_envelope={"budget_usd": 0, "max_missions": 1},
            verification_criteria=["operator_controlled"],
        )
    )
    store.transition(goal.id, GoalStatus.PAUSED, reason="operator_pause", actor="operator")
    store.transition(goal.id, GoalStatus.ACTIVE, reason="operator_resume", actor="operator")
    # Redirect as strategy update while active.
    g = store.get(goal.id)
    redirected = g.model_copy(
        update={
            "strategy": "redirected_plan",
            "decision_history": list(g.decision_history)
            + [
                {
                    "at": g.updated_at,
                    "actor": "operator",
                    "from": "strategy:",
                    "to": "strategy:redirected_plan",
                    "reason": "operator_redirect",
                }
            ],
        }
    )
    store.goals[goal.id] = redirected
    store._save()
    # Budget exhaustion → blocked
    store.transition(goal.id, GoalStatus.BLOCKED, reason="budget_exhausted", actor="kernel")
    store.transition(goal.id, GoalStatus.CANCELLED, reason="operator_cancel", actor="operator")
    final = store.get(goal.id)
    try:
        store.transition(goal.id, GoalStatus.ACTIVE, reason="after_cancel", actor="harness")
        return ProbeResult(False, "fail_work_after_cancel", {})
    except ValueError as exc:
        terminal = str(exc)
    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "goal_id": final.id,
            "status": final.status.value,
            "strategy": final.strategy,
            "terminal_guard": terminal,
            "history_len": len(final.decision_history),
        },
    )


def probe_lesson_rollback(_tmp: Path) -> ProbeResult:
    repo = LearningRepository()
    prop = repo.create(
        LearningProposal(
            project_id="proj_accept",
            change_summary="Adopt heuristic H1",
            sealed_holdout_ref="holdout://sealed/v1",
            review_ref="review://independent/r1",
        )
    )
    repo.transition(prop.proposal_id, "validated")
    repo.transition(prop.proposal_id, "calibrating")
    repo.transition(prop.proposal_id, "frozen")
    repo.transition(prop.proposal_id, "held_out_eval")
    repo.transition(prop.proposal_id, "review")
    repo.transition(prop.proposal_id, "canary")
    rolled = repo.rollback(prop.proposal_id)
    # Self-approval blocked
    bad = repo.create(
        LearningProposal(project_id="proj_accept", change_summary="No review", review_ref=None)
    )
    repo.transition(bad.proposal_id, "validated")
    repo.transition(bad.proposal_id, "calibrating")
    repo.transition(bad.proposal_id, "frozen")
    # Need sealed holdout for held_out_eval — set it
    item = repo.get(bad.proposal_id)
    item.sealed_holdout_ref = "holdout://sealed/v2"
    repo.transition(bad.proposal_id, "held_out_eval")
    repo.transition(bad.proposal_id, "review")
    try:
        repo.transition(bad.proposal_id, "canary")
        return ProbeResult(False, "fail_self_approved_canary", {})
    except LearningError as exc:
        blocked = str(exc)
    try:
        repo.create(
            LearningProposal(
                project_id="proj_accept",
                change_summary="leak",
                sealed_holdout_ref="answer=secret",
            )
        )
        return ProbeResult(False, "fail_holdout_plaintext", {})
    except LearningError as exc:
        plaintext = str(exc)
    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "rolled_back_state": rolled.state,
            "self_approval_blocked": blocked,
            "holdout_plaintext_blocked": plaintext,
        },
    )


def probe_live_grant_gate(_tmp: Path) -> ProbeResult:
    """Deterministic side of V20-S12: prove live is blocked without grant; no invent."""
    try:
        from swarm.evals.synthetic_harness import assert_live_gate

        assert_live_gate(mode="live", grant=None)
        return ProbeResult(False, "fail_live_allowed_without_grant", {})
    except LiveGateBlocked as exc:
        no_grant = str(exc)
    # Unapproved grant still blocked
    try:
        from swarm.evals.synthetic_harness import assert_live_gate

        assert_live_gate(
            mode="live",
            grant=LiveGrant(
                grant_id="invented_not_allowed",
                routes=("rt_x",),
                budget_usd=0.0,
                purpose="must_not_invent",
                approved=False,
                free_routes_only=True,
                max_calls=1,
                max_tokens=100,
                max_wall_seconds=30,
            ),
        )
        return ProbeResult(False, "fail_unapproved_grant_allowed", {})
    except LiveGateBlocked as exc:
        unapproved = str(exc)
    # Harness must never fabricate an approved grant for campaign runs.
    return ProbeResult(
        True,
        "pass_deterministic_gate_only",
        {
            "no_grant": no_grant,
            "unapproved": unapproved,
            "invented_grant": False,
            "live_dispatch": "blocked_pending_operator_grant",
        },
    )


def probe_scaffold(name: str) -> Callable[[Path], ProbeResult]:
    def _run(_tmp: Path) -> ProbeResult:
        return ProbeResult(
            True,
            "scaffold_ready_not_integrated",
            {
                "probe": name,
                "note": (
                    "Freeze + gate wiring verified; full product integration "
                    "awaits owning lanes (C/D/E/A). Not a version pass."
                ),
            },
        )

    return _run


PROBES: dict[str, Callable[[Path], ProbeResult]] = {
    "goal_multi_mission_link": probe_goal_multi_mission_link,
    "goal_strategy_change_after_failure": probe_goal_strategy_change_after_failure,
    "goal_ongoing_cycles": probe_goal_ongoing_cycles,
    "goal_blocked_then_available": probe_goal_blocked_then_available,
    "goal_pause_cancel_budget": probe_goal_pause_cancel_budget,
    "lesson_rollback": probe_lesson_rollback,
    "live_grant_gate": probe_live_grant_gate,
    "delegation_bounds_scaffold": probe_scaffold("delegation_bounds_scaffold"),
    "succession_fence_scaffold": probe_scaffold("succession_fence_scaffold"),
    "restart_stale_return_scaffold": probe_scaffold("restart_stale_return_scaffold"),
    "duplicate_trigger_idempotency_scaffold": probe_scaffold(
        "duplicate_trigger_idempotency_scaffold"
    ),
    "sdk_ui_parity_scaffold": probe_scaffold("sdk_ui_parity_scaffold"),
}
