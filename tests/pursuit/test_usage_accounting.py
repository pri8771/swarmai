"""PC-06 usage/budget accounting + LiveGrant preflight (no fabricated grants)."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.evals.synthetic_harness import LiveGateBlocked, LiveGrant
from swarm.goals.models import Goal, GoalStore
from swarm.pursuit import (
    AccountingError,
    ExecutionOutcome,
    GoalResourceLedger,
    PursuitEngine,
    preflight_live_grant,
    refuse_invented_grant,
)


def test_zero_spend_rejects_paid_reserve() -> None:
    ledger = GoalResourceLedger.from_envelope(
        "goal_x", {"spend_usd_ceiling": 0.0, "max_model_calls": 10, "max_tool_calls": 10}
    )
    with pytest.raises(AccountingError, match="paid_cost_denied"):
        ledger.reserve(mission_id="msn_1", spend_usd=0.01)


def test_reserve_settle_once_and_reject_double() -> None:
    ledger = GoalResourceLedger.from_envelope(
        "goal_x",
        {"spend_usd_ceiling": 0.0, "max_model_calls": 5, "max_tool_calls": 5},
    )
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.0, model_calls=1, tool_calls=1)
    ledger.settle(hold.hold_id, spend_usd=0.0, model_calls=1, tool_calls=1)
    with pytest.raises(AccountingError, match="double_settle"):
        ledger.settle(hold.hold_id, spend_usd=0.0, model_calls=0, tool_calls=0)
    snap = ledger.snapshot()
    assert snap["settled"]["model_calls"] == 1
    assert snap["remaining"]["model_calls"] == 4


def test_unknown_usage_preserved_not_cleared() -> None:
    ledger = GoalResourceLedger.from_envelope(
        "goal_x", {"spend_usd_ceiling": 1.0, "allow_paid": True, "max_model_calls": 3}
    )
    hold = ledger.reserve(mission_id="msn_u", spend_usd=0.5, model_calls=1)
    ledger.settle(hold.hold_id, spend_usd=0.5, model_calls=1, usage_unknown=True)
    assert ledger.holds[hold.hold_id].state == "unknown"
    with pytest.raises(AccountingError, match="unknown_hold_requires_reconciliation"):
        ledger.settle(hold.hold_id, spend_usd=0.0, model_calls=0)
    assert ledger.remaining().usage_unknown is True


def test_child_cannot_exceed_remaining_model_calls() -> None:
    ledger = GoalResourceLedger.from_envelope(
        "goal_x", {"spend_usd_ceiling": 0.0, "max_model_calls": 2, "max_tool_calls": 10}
    )
    ledger.reserve(mission_id="msn_a", model_calls=2)
    with pytest.raises(AccountingError, match="insufficient_model_call_budget"):
        ledger.reserve(mission_id="msn_b", model_calls=1)


def test_settlement_cannot_silently_exceed_call_envelope() -> None:
    ledger = GoalResourceLedger.from_envelope(
        "goal_x", {"spend_usd_ceiling": 0.0, "max_model_calls": 1, "max_tool_calls": 1}
    )
    hold = ledger.reserve(mission_id="msn_a", model_calls=1, tool_calls=1)
    with pytest.raises(AccountingError, match="settle_exceeds_model_call_envelope"):
        ledger.settle(hold.hold_id, model_calls=2, tool_calls=1)
    with pytest.raises(AccountingError, match="settle_exceeds_tool_call_envelope"):
        ledger.settle(hold.hold_id, model_calls=1, tool_calls=2)
    assert ledger.holds[hold.hold_id].state == "held"


def test_pursuit_tick_settles_usage(tmp_path: Path) -> None:
    store = GoalStore(tmp_path / "goals")
    goal = store.create(
        Goal(
            project_id="proj_acct",
            desired_outcome="accounted work",
            verification_criteria=["c1"],
            resource_envelope={
                "spend_usd_ceiling": 0.0,
                "max_model_calls": 10,
                "max_tool_calls": 10,
            },
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )

    class ZeroCostExecutor:
        def execute(self, proposal):  # noqa: ANN001
            from swarm.pursuit.verification import (
                artifact_digest_for_refs,
                issue_criterion_receipt,
            )

            mid = proposal.mission_id or "msn_z"
            digest = artifact_digest_for_refs(["ev:z"], mission_id=mid)
            receipt = issue_criterion_receipt(
                goal_id=proposal.goal_id,
                criterion_id="c1",
                mission_id=mid,
                artifact_digest=digest,
                evidence_ref="ev:z",
            )
            return ExecutionOutcome(
                mission_id=mid,
                success=True,
                evidence_refs=["ev:z"],
                criterion_receipts=[receipt.model_dump(mode="json")],
                cost_usd=0.0,
                model_calls=1,
                tool_calls=1,
                runtime="test",
            )

    engine = PursuitEngine(store, executor=ZeroCostExecutor())
    cycle = engine.tick(goal.id, force=True)
    assert cycle.meta.get("accounting")
    ledger = engine.resource_ledger(goal.id)
    assert ledger.snapshot()["settled"]["model_calls"] == 1
    assert ledger.snapshot()["remaining"]["model_calls"] == 9


def test_live_grant_preflight_missing_and_invent_refused() -> None:
    missing = preflight_live_grant(None)
    assert missing.ready is False
    assert missing.blocked_reason == "missing_live_grant"
    assert missing.to_dict()["invent_grant"] is False

    with pytest.raises(LiveGateBlocked, match="invent_live_grant_forbidden"):
        refuse_invented_grant(invent=True)

    draft = LiveGrant(
        grant_id="lg_draft",
        routes=("rt_local",),
        budget_usd=0.0,
        purpose="qualification",
        approved=False,
        free_routes_only=True,
        max_calls=1,
        max_tokens=10,
        max_wall_seconds=30,
    )
    blocked = preflight_live_grant(draft)
    assert blocked.ready is False
    assert "not approved" in (blocked.blocked_reason or "")

    approved = LiveGrant(
        grant_id="lg_ok",
        routes=("rt_local",),
        budget_usd=0.0,
        purpose="qualification",
        approved=True,
        free_routes_only=True,
        max_calls=1,
        max_tokens=10,
        max_wall_seconds=30,
    )
    ok = preflight_live_grant(approved, required_route="rt_local")
    assert ok.ready is True
    assert ok.grant_id == "lg_ok"
