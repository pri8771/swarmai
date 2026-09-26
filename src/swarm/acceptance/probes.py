"""Deterministic probes for frozen V2.0 acceptance scenarios.

Probes exercise real local product contracts with fake upstreams / in-process
registries. Live/host/elapsed gates are never satisfied by inventing grants or
simulating wall-clock time. Harness output never marks versions accepted.
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


def probe_delegation_bounds(tmp: Path) -> ProbeResult:
    """V20-S05: collab + bounded spawn/delegation against real product contracts."""
    import asyncio

    from swarm.contracts.enums import TaskStatus
    from swarm.contracts.fixtures import sample_mission, sample_task
    from swarm.controller.graph import validate_proposal
    from swarm.controller.mission import MissionController, spawn_proposal
    from swarm.goals.models import Goal
    from swarm.mission.collab import CollaborativeMissionBoard
    from swarm.pursuit.models import ContributionKind, MissionProposalDraft
    from swarm.pursuit.policy import admit_proposal

    board = CollaborativeMissionBoard(mission_id="msn_s05_deleg")
    board.join("agent_lead")
    board.join("agent_helper")
    board.post(
        from_agent="agent_lead",
        to_agent="agent_helper",
        kind="delegate",
        body="Please take the mac_local extract slice under parent envelope.",
        evidence_refs=["art_parent_1"],
    )
    try:
        board.post(
            from_agent="agent_helper",
            kind="status",
            body="expand_budget so we can finish faster",
        )
        return ProbeResult(False, "fail_authority_expanded_via_message", {})
    except PermissionError as exc:
        msg_blocked = str(exc)

    async def _spawn_bounds() -> dict[str, Any]:
        ctrl = MissionController()
        mission = sample_mission().model_copy(
            update={
                "id": "msn_s05",
                "data_scope_ids": ["scope_repo_demo"],
                "max_graph_nodes": 2,
            }
        )
        await ctrl.submit_mission(mission)
        parent = sample_task(mission_id=mission.id).model_copy(
            update={
                "id": "task_parent",
                "objective": "parent extract",
                "scopes": ["scope_repo_demo"],
                "status": TaskStatus.READY,
            }
        )
        ctrl.tasks[mission.id][parent.id] = parent

        # Child trying to use a scope outside the mission envelope (no intersection).
        wide = sample_task(mission_id=mission.id).model_copy(
            update={
                "id": "task_wide",
                "objective": "widen scope",
                "parent_task_id": parent.id,
                "scopes": ["scope_secrets_only"],
                "status": TaskStatus.PROPOSED,
            }
        )
        wide_prop = spawn_proposal(
            mission, author_session_id="as_lead", parent=parent, children=[wide]
        )
        wide_result = validate_proposal(
            wide_prop,
            tasks=ctrl.tasks[mission.id],
            mission_revision=mission.revision,
            mission_scopes=set(mission.data_scope_ids),
            max_graph_nodes=mission.max_graph_nodes,
        )
        if wide_result.accepted or wide_result.reason != "scope_not_in_mission":
            return {"ok": False, "why": "scope_widen_not_rejected", "result": wide_result.reason}

        child = sample_task(mission_id=mission.id).model_copy(
            update={
                "id": "task_child_1",
                "objective": "bounded child extract",
                "parent_task_id": parent.id,
                "scopes": ["scope_repo_demo"],
                "task_family": "extraction",
                "status": TaskStatus.PROPOSED,
            }
        )
        p1 = spawn_proposal(mission, author_session_id="as_lead", parent=parent, children=[child])
        await ctrl.propose_graph_change(p1)
        await ctrl.commit_validated_revision(p1.proposal_id)
        mission = ctrl.missions[mission.id]

        # Idempotent spawn key: same objective/family/parent → one child.
        dup = sample_task(mission_id=mission.id).model_copy(
            update={
                "id": "task_child_dup",
                "objective": "bounded child extract",
                "parent_task_id": parent.id,
                "scopes": ["scope_repo_demo"],
                "task_family": "extraction",
                "status": TaskStatus.PROPOSED,
            }
        )
        p2 = spawn_proposal(mission, author_session_id="as_helper", parent=parent, children=[dup])
        dup_result = validate_proposal(
            p2,
            tasks=ctrl.tasks[mission.id],
            mission_revision=mission.revision,
            mission_scopes=set(mission.data_scope_ids),
            max_graph_nodes=mission.max_graph_nodes,
        )
        if dup_result.accepted or dup_result.merged_into != "task_child_1":
            return {"ok": False, "why": "duplicate_spawn_not_merged", "result": dup_result.reason}

        # Depth/width: max_graph_nodes=2 (parent + one child already) blocks further spawn.
        extra = sample_task(mission_id=mission.id).model_copy(
            update={
                "id": "task_overflow",
                "objective": "overflow child",
                "parent_task_id": parent.id,
                "scopes": ["scope_repo_demo"],
                "status": TaskStatus.PROPOSED,
            }
        )
        p3 = spawn_proposal(mission, author_session_id="as_lead", parent=parent, children=[extra])
        overflow = validate_proposal(
            p3,
            tasks=ctrl.tasks[mission.id],
            mission_revision=mission.revision,
            mission_scopes=set(mission.data_scope_ids),
            max_graph_nodes=mission.max_graph_nodes,
        )
        if overflow.accepted or overflow.reason != "max_graph_nodes":
            return {"ok": False, "why": "graph_cap_not_enforced", "result": overflow.reason}

        retained = sorted(ctrl.tasks[mission.id].keys())
        return {
            "ok": True,
            "scope_widen_rejected": wide_result.reason,
            "duplicate_merged_into": dup_result.merged_into,
            "graph_cap": overflow.reason,
            "tasks": retained,
        }

    spawn = asyncio.run(_spawn_bounds())
    if not spawn.get("ok"):
        return ProbeResult(False, f"fail_{spawn.get('why')}", spawn)

    goal = Goal(
        project_id="proj_accept",
        desired_outcome="delegation envelope",
        resource_envelope={"max_spend_usd": 0.0},
        authority_envelope={"tools": ["extract"], "providers": ["fake"]},
        verification_criteria=["bounded"],
    )
    draft = MissionProposalDraft(
        goal_id=goal.id,
        title="child mission",
        objective="spawn with inflated budget",
        kind=ContributionKind.ACT,
        dedupe_key="s05-deleg-1",
        requested_budget_usd=5.0,
        requested_tools=["extract", "admin_bypass"],
        requested_providers=["fake", "paid_live"],
    )
    rejected = admit_proposal(goal, draft)
    if rejected.state != "rejected" or rejected.rejection_reason != "budget_exceeds_envelope":
        return ProbeResult(
            False,
            "fail_budget_not_clamped",
            {"state": rejected.state, "reason": rejected.rejection_reason},
        )
    draft2 = draft.model_copy(update={"requested_budget_usd": 0.0})
    rejected2 = admit_proposal(goal, draft2)
    if rejected2.state != "rejected" or rejected2.rejection_reason != "tools_outside_authority":
        return ProbeResult(
            False,
            "fail_tools_not_clamped",
            {"state": rejected2.state, "reason": rejected2.rejection_reason},
        )

    evidence = board.evidence()
    (tmp / "s05_collab.json").write_text(
        __import__("json").dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "agents": evidence["agents"],
            "message_authority_blocked": msg_blocked,
            "spawn": spawn,
            "budget_rejection": rejected.rejection_reason,
            "tools_rejection": rejected2.rejection_reason,
            "spend_usd": 0.0,
            "note": "deterministic collab+spawn+envelope probes; live also_gate separate",
        },
    )


def probe_succession_fence(tmp: Path) -> ProbeResult:
    """V20-S06: X→Y fenced takeover; stale predecessor commits refused."""
    from swarm.mission.collab import CollaborativeMissionBoard

    board = CollaborativeMissionBoard(mission_id="msn_s06_succ")
    board.join("agent_x")
    board.join("agent_y")
    board.post(
        from_agent="agent_x",
        to_agent="agent_y",
        kind="handoff_kt",
        body="Transferring working context; do not expand authority.",
    )
    handoff = board.prepare_handoff(
        from_agent="agent_x",
        to_agent="agent_y",
        retained_facts=["placement=mac_local", "inbox_preserved"],
        open_commitments=["submit_result_pending_accept"],
        event_watermark="wm_s06",
    )
    if handoff.to_dict().get("authority_expanded") is not False:
        return ProbeResult(False, "fail_handoff_claims_authority", {})
    # Trainee must not act as active writer before cutover.
    if board.can_claim_work("agent_x") is not True:
        return ProbeResult(False, "fail_predecessor_blocked_before_cutover", {})
    y_gen_before = board.active_generation.get("agent_y", 1)
    adopted = board.adopt_handoff(handoff.handoff_id, by_agent="agent_y")
    if not adopted.adopted:
        return ProbeResult(False, "fail_handoff_not_adopted", {})
    if board.can_claim_work("agent_x") is not False:
        return ProbeResult(False, "fail_predecessor_still_claims", {})
    if board.can_claim_work("agent_y") is not True:
        return ProbeResult(False, "fail_successor_cannot_claim", {})
    if board.active_generation.get("agent_y", 0) <= y_gen_before:
        return ProbeResult(False, "fail_generation_not_bumped", {})
    # Only one active claimer after cutover (predecessor fenced).
    active_claimers = [a for a in board.agents if board.can_claim_work(a)]
    if active_claimers != ["agent_y"]:
        return ProbeResult(False, "fail_dual_active_generations", {"active": active_claimers})
    try:
        board.adopt_handoff(handoff.handoff_id, by_agent="agent_x")
        return ProbeResult(False, "fail_wrong_adopter_allowed", {})
    except PermissionError as exc:
        wrong_adopter = str(exc)

    board.dump(tmp / "s06_succession.json")
    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "handoff_id": handoff.handoff_id,
            "context_digest": handoff.context_digest,
            "inbox_cursor": handoff.inbox_cursor,
            "active_claimers": active_claimers,
            "active_generation": board.active_generation,
            "wrong_adopter_blocked": wrong_adopter,
            "spend_usd": 0.0,
        },
    )


def probe_restart_stale_return(tmp: Path) -> ProbeResult:
    """V20-S07: durable restart + stale generation/lease refuse (not two-host proof)."""
    import asyncio

    from swarm.contracts.fixtures import sample_task
    from swarm.contracts.workspace import WorkerLease
    from swarm.goals.models import Goal, GoalKind, GoalStatus
    from swarm.workers.registry import StaleGenerationError, WorkerRegistryService

    store = _goal_store(tmp)
    goal = store.create(
        Goal(
            project_id="proj_accept",
            desired_outcome="Survive coordinator restart",
            verification_criteria=["state_recovered"],
            kind=GoalKind.FINITE,
        )
    )
    store.link_mission(goal.id, "mission_pre_restart")
    store.pause(goal.id, reason="pre_restart_checkpoint", actor="harness")
    store.restart(goal.id, reason="coordinator_restart", actor="harness")
    cold = _goal_store(tmp)
    recovered = cold.get(goal.id)
    if recovered.status != GoalStatus.ACTIVE:
        return ProbeResult(False, "fail_goal_not_recovered", {"status": recovered.status.value})
    if recovered.restart_count < 1:
        return ProbeResult(False, "fail_restart_not_recorded", {})

    async def _stale_lease() -> dict[str, Any]:
        reg = WorkerRegistryService(lease_ttl_seconds=60)
        token = "wt_s07_no_secret"
        lease = await reg.register(
            WorkerLease(
                node_identity="mac-s07",
                architecture="arm64",
                runtime_version="0.1.0",
                capacity_units=1.0,
                capabilities=["extract"],
                labels=["mac"],
            ),
            token=token,
            project_id="proj_accept",
        )
        wid = lease.worker_id
        gen = lease.lease_generation
        reg._workers[wid].privacy_classes = {"mac_local", "local"}
        await reg.heartbeat(wid, gen, token=token)
        task = sample_task(mission_id="msn_s07").model_copy(
            update={
                "id": "tsk_s07",
                "project_id": "proj_accept",
                "required_capabilities": ["extract"],
                "scopes": ["mac_local"],
            }
        )
        reg.enqueue(task)
        claimed = await reg.claim_work(wid, token=token)
        if not claimed.claimed or claimed.lease is None:
            return {"ok": False, "why": "claim_failed"}
        # Disconnect / revoke fences old generation.
        new_gen = await reg.revoke_generation(wid)
        stale_blocked = False
        stale_reason = ""
        try:
            reg.submit_result(
                lease_id=claimed.lease.lease_id,
                worker_id=wid,
                generation=gen,
                token=token,
                status="completed",
                checks={"review_passed": True},
                summary="stale_return",
            )
        except (StaleGenerationError, PermissionError) as exc:
            stale_blocked = True
            stale_reason = str(exc)
        # Reconnect with old generation must also fail.
        reconnect_blocked = False
        try:
            reg.reconnect(wid, generation=gen, token=token)
        except (StaleGenerationError, PermissionError):
            reconnect_blocked = True
        return {
            "ok": stale_blocked and reconnect_blocked and new_gen > gen,
            "stale_submit_blocked": stale_blocked,
            "stale_reason": stale_reason,
            "reconnect_blocked": reconnect_blocked,
            "old_generation": gen,
            "new_generation": new_gen,
            "two_host_claim": False,
            "mode": "single_process_registry_fence",
        }

    stale = asyncio.run(_stale_lease())
    if not stale.get("ok"):
        return ProbeResult(False, "fail_stale_return_accepted", stale)

    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "goal_id": recovered.id,
            "restart_count": recovered.restart_count,
            "history_len": len(recovered.decision_history),
            "stale": stale,
            "host_gate": "blocked_separately_two_local_neq_two_host",
            "spend_usd": 0.0,
        },
    )


def probe_duplicate_trigger_idempotency(tmp: Path) -> ProbeResult:
    """V20-S08: duplicate triggers / lost-ack replay do not double-admit."""
    from swarm.api.store import ProductStore
    from swarm.goals.models import Goal, GoalKind
    from swarm.pursuit.models import ContributionKind
    from swarm.pursuit.policy import dedupe_key_for

    store = _goal_store(tmp)
    goal = store.create(
        Goal(
            project_id="proj_accept",
            desired_outcome="Dedupe pursuit triggers",
            verification_criteria=["one_receipt"],
            kind=GoalKind.ONGOING,
        )
    )
    _g1, r1 = store.accept_trigger(
        goal.id,
        dedupe_key="sched:s08:occurrence-1",
        trigger_kind="schedule",
        actor="scheduler",
        payload={"n": 1},
    )
    _g2, r2 = store.accept_trigger(
        goal.id,
        dedupe_key="sched:s08:occurrence-1",
        trigger_kind="schedule",
        actor="scheduler",
        payload={"n": 1},
    )
    if r1.get("duplicate") is not False:
        return ProbeResult(False, "fail_first_trigger_marked_duplicate", r1)
    if r2.get("duplicate") is not True or r2.get("receipt_id") != r1.get("receipt_id"):
        return ProbeResult(False, "fail_duplicate_trigger_not_deduped", {"r1": r1, "r2": r2})
    final = store.get(goal.id)
    if len(final.trigger_receipts) != 1:
        return ProbeResult(
            False, "fail_double_receipt", {"count": len(final.trigger_receipts)}
        )

    # Lost-ack style API idempotency: same key+digest returns one body; mismatch 409.
    api = ProductStore(repo_root=tmp / "api")
    key = "idem-s08-mission-admit"
    body = {"mission_id": "msn_once", "budget_usd": 0.0}
    digest = "digest_s08_v1"
    first = api.store_idempotent(
        key,
        body,
        actor="operator",
        project_id="proj_accept",
        operation="mission_admit",
        request_digest=digest,
    )
    replay = api.recall_idempotent(
        key,
        actor="operator",
        project_id="proj_accept",
        operation="mission_admit",
        request_digest=digest,
    )
    if replay != first:
        return ProbeResult(
            False,
            "fail_idempotent_replay_mismatch",
            {"first": first, "replay": replay},
        )
    mismatch_blocked = False
    try:
        api.recall_idempotent(
            key,
            actor="operator",
            project_id="proj_accept",
            operation="mission_admit",
            request_digest="digest_different_body",
        )
    except Exception as exc:  # noqa: BLE001 — ApiError or subclass
        mismatch_blocked = "idempotency" in str(exc).lower() or "mismatch" in str(exc).lower()
        if not mismatch_blocked:
            mismatch_blocked = type(exc).__name__ == "ApiError"

    # Pursuit dedupe keys collide for identical logical contribution.
    k1 = dedupe_key_for(
        goal_id=goal.id,
        kind=ContributionKind.ACT,
        title="Extract contacts",
        criteria=["contacts_extracted"],
    )
    k2 = dedupe_key_for(
        goal_id=goal.id,
        kind=ContributionKind.ACT,
        title="  extract   contacts ",
        criteria=["contacts_extracted"],
    )
    if k1 != k2:
        return ProbeResult(False, "fail_pursuit_dedupe_unstable", {"k1": k1, "k2": k2})

    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "trigger_receipt_id": r1["receipt_id"],
            "duplicate_replay": True,
            "idempotent_body": first,
            "payload_mismatch_blocked": mismatch_blocked,
            "pursuit_dedupe_key": k1,
            "spend_usd": 0.0,
        },
    )


def probe_sdk_ui_parity(tmp: Path) -> ProbeResult:
    """V20-S11: SDK and UI share Goal create/lifecycle contracts (fixture API, no spend).

    The probe clears ``SWARM_*`` for its fixture app; the caller's environment is
    restored afterwards so the probe cannot redirect later work (e.g. Alembic's
    ``database_url()``) to the default database.
    """
    import os

    saved = {k: v for k, v in os.environ.items() if k.startswith("SWARM_")}
    try:
        return _probe_sdk_ui_parity(tmp)
    finally:
        for key in [k for k in os.environ if k.startswith("SWARM_")]:
            os.environ.pop(key, None)
        os.environ.update(saved)


def _probe_sdk_ui_parity(tmp: Path) -> ProbeResult:
    import os

    import httpx
    from fastapi.testclient import TestClient
    from httpx import Response

    from swarm.api.app import create_app
    from swarm.goals.models import GoalStatus
    from swarm.sdk import SwarmClient

    # UI createLiveGoal POST body keys (apps/console/src/api/client.ts) must match SDK.
    ui_create_fields = {
        "project_id",
        "desired_outcome",
        "verification_criteria",
        "kind",
        "permitted_agents",
        "resource_envelope",
        "authority_envelope",
        "strategy",
        "stop_conditions",
    }
    sdk_create_fields = {
        "project_id",
        "desired_outcome",
        "verification_criteria",
        "kind",
        "permitted_agents",
        "resource_envelope",
        "authority_envelope",
        "scope",
        "constraints",
        "strategy",
        "stop_conditions",
        "dependencies",
        "open_questions",
        "blockers",
        "owner",
    }
    if not ui_create_fields.issubset(sdk_create_fields):
        return ProbeResult(
            False,
            "fail_ui_fields_missing_from_sdk",
            {"missing": sorted(ui_create_fields - sdk_create_fields)},
        )

    # Lifecycle action paths shared by UI lifecycleLiveGoal and SDK.
    shared_lifecycle = {"pause", "resume", "cancel", "restart"}

    for key in list(os.environ):
        if key.startswith("SWARM_"):
            os.environ.pop(key, None)

    class _StarletteTransport(httpx.BaseTransport):
        def __init__(self, app: Any) -> None:
            self._tc = TestClient(app)

        def handle_request(self, request: httpx.Request) -> Response:
            headers = [(k.decode(), v.decode()) for k, v in request.headers.raw]
            path = request.url.path
            if request.url.query:
                path = f"{path}?{request.url.query.decode()}"
            resp = self._tc.request(
                request.method,
                path,
                headers=dict(headers),
                content=request.content,
            )
            return Response(
                status_code=resp.status_code,
                headers=resp.headers,
                content=resp.content,
                request=request,
            )

    headers = {"Authorization": "Bearer parity-token"}
    ui_body = {
        "project_id": "proj_parity",
        "desired_outcome": "SDK/UI parity goal",
        "verification_criteria": ["same_contract"],
        "kind": "finite",
        "permitted_agents": ["planner", "verifier"],
        "resource_envelope": {"max_budget_usd": 0.0},
        "authority_envelope": {"tools": []},
        "strategy": "ui_then_sdk",
        "stop_conditions": [],
    }

    # Honesty gate (PC-02): operational + DB-down must refuse writes — never echo success.
    # LiveGrant is not invented here; durable authority refusal is the expected eng signal.
    refuse_root = tmp / "server_refuse"
    refuse_app = create_app(
        repo_root=refuse_root,
        seed_loopback_token="parity-token",
        install_project_id="proj_parity",
        db_reachable=False,
    )
    refuse_http = TestClient(refuse_app)
    refused = refuse_http.post("/v1/goals", headers=headers, json=ui_body)
    if refused.status_code == 200:
        return ProbeResult(
            False,
            "fail_echo_success_when_db_down",
            {"status": refused.status_code, "body": refused.text},
        )
    if refused.status_code != 503:
        return ProbeResult(
            False,
            "fail_expected_durable_refuse",
            {"status": refused.status_code, "body": refused.text},
        )
    refuse_code = ""
    try:
        refuse_code = str(refused.json().get("code") or "")
    except Exception:
        refuse_code = ""
    if refuse_code != "durable_authority_unavailable":
        return ProbeResult(
            False,
            "fail_unexpected_refuse_code",
            {"code": refuse_code, "body": refused.text},
        )

    # Contract lifecycle on file-backed eng path (db_reachable=None → no DSN configured).
    # Not LiveGrant, not operator acceptance — local durable files only.
    root = tmp / "server"
    app = create_app(
        repo_root=root,
        seed_loopback_token="parity-token",
        install_project_id="proj_parity",
        db_reachable=None,
    )
    http = TestClient(app)
    via_ui = http.post("/v1/goals", headers=headers, json=ui_body)
    if via_ui.status_code != 200:
        return ProbeResult(
            False,
            "fail_ui_create",
            {"status": via_ui.status_code, "body": via_ui.text},
        )
    ui_goal = via_ui.json()["goal"]
    goal_id = ui_goal["id"]

    with SwarmClient(
        "http://test", token="parity-token", transport=_StarletteTransport(app)
    ) as client:
        listed = client.list_goals(project_id="proj_parity")
        if not any(g.id == goal_id for g in listed):
            return ProbeResult(False, "fail_sdk_cannot_see_ui_goal", {"goal_id": goal_id})
        fetched = client.get_goal(goal_id)
        if fetched.desired_outcome != ui_body["desired_outcome"]:
            return ProbeResult(False, "fail_sdk_ui_outcome_mismatch", {})
        paused = client.interrupt_goal(goal_id, reason="parity interrupt")
        if paused.status != GoalStatus.PAUSED:
            return ProbeResult(False, "fail_sdk_interrupt", {"status": paused.status.value})
        # UI-shaped lifecycle path (POST /v1/goals/{id}/resume)
        resume_http = http.post(
            f"/v1/goals/{goal_id}/resume",
            headers=headers,
            json={"reason": "ui resume"},
        )
        if resume_http.status_code != 200:
            return ProbeResult(
                False,
                "fail_ui_resume",
                {"status": resume_http.status_code, "body": resume_http.text},
            )
        if resume_http.json()["goal"]["status"] != GoalStatus.ACTIVE.value:
            return ProbeResult(False, "fail_ui_resume_status", resume_http.json())
        via_sdk = client.create_goal(
            project_id="proj_parity",
            desired_outcome="SDK-created twin",
            verification_criteria=["same_contract"],
            kind="finite",
            permitted_agents=["planner"],
            resource_envelope={"max_budget_usd": 0.0},
            authority_envelope={"tools": []},
            strategy="sdk_path",
        )
        # Response shape parity on create.
        shape_ui = set(ui_goal.keys())
        shape_sdk = set(via_sdk.model_dump(mode="json").keys())
        if shape_ui != shape_sdk:
            return ProbeResult(
                False,
                "fail_response_shape_parity",
                {"only_ui": sorted(shape_ui - shape_sdk), "only_sdk": sorted(shape_sdk - shape_ui)},
            )

    return ProbeResult(
        True,
        "pass_deterministic",
        {
            "ui_goal_id": goal_id,
            "sdk_goal_id": via_sdk.id,
            "shared_create_fields": sorted(ui_create_fields),
            "shared_lifecycle_actions": sorted(shared_lifecycle),
            "db_down_refused_status": refused.status_code,
            "db_down_refused_code": refuse_code or "durable_authority_unavailable",
            "fixture_only_certifies_acceptance": False,
            "live_grant_invented": False,
            "spend_usd": 0.0,
            "note": (
                "Contract + HTTP parity on file-backed eng path; "
                "DB-down create refused (no echo success); not LiveGrant / not operator accept"
            ),
        },
    )


PROBES: dict[str, Callable[[Path], ProbeResult]] = {
    "goal_multi_mission_link": probe_goal_multi_mission_link,
    "goal_strategy_change_after_failure": probe_goal_strategy_change_after_failure,
    "goal_ongoing_cycles": probe_goal_ongoing_cycles,
    "goal_blocked_then_available": probe_goal_blocked_then_available,
    "goal_pause_cancel_budget": probe_goal_pause_cancel_budget,
    "lesson_rollback": probe_lesson_rollback,
    "live_grant_gate": probe_live_grant_gate,
    # Real product probes (S05–S08/S11). Scaffold aliases retained for freeze hash migration.
    "delegation_bounds": probe_delegation_bounds,
    "succession_fence": probe_succession_fence,
    "restart_stale_return": probe_restart_stale_return,
    "duplicate_trigger_idempotency": probe_duplicate_trigger_idempotency,
    "sdk_ui_parity": probe_sdk_ui_parity,
    "delegation_bounds_scaffold": probe_delegation_bounds,
    "succession_fence_scaffold": probe_succession_fence,
    "restart_stale_return_scaffold": probe_restart_stale_return,
    "duplicate_trigger_idempotency_scaffold": probe_duplicate_trigger_idempotency,
    "sdk_ui_parity_scaffold": probe_sdk_ui_parity,
}
