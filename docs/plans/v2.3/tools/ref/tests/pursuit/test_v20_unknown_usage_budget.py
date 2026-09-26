"""SW-W1-S10 / F-13: unknown usage keeps budget committed until reconciled."""

from __future__ import annotations

import pytest

from swarm.pursuit import AccountingError, GoalResourceLedger


def _ledger() -> GoalResourceLedger:
    return GoalResourceLedger.from_envelope(
        "goal_u", {"spend_usd_ceiling": 1.0, "allow_paid": True, "max_model_calls": 3}
    )


def test_unknown_hold_still_counts_against_remaining() -> None:
    ledger = _ledger()
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.6, model_calls=2)
    ledger.settle(hold.hold_id, spend_usd=0.1, model_calls=1, usage_unknown=True)
    remaining = ledger.remaining()
    assert remaining.spend_usd == pytest.approx(0.4)
    assert remaining.model_calls == 1
    with pytest.raises(AccountingError, match="insufficient_spend_budget"):
        ledger.reserve(mission_id="msn_2", spend_usd=0.5)


def test_unknown_hold_uses_larger_of_reserved_and_reported() -> None:
    ledger = _ledger()
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.2, model_calls=1)
    ledger.settle(hold.hold_id, spend_usd=0.7, model_calls=1, usage_unknown=True)
    assert ledger.remaining().spend_usd == pytest.approx(0.3)


def test_unknown_hold_cannot_be_released() -> None:
    ledger = _ledger()
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.5, model_calls=1)
    ledger.settle(hold.hold_id, spend_usd=0.5, model_calls=1, usage_unknown=True)
    with pytest.raises(AccountingError, match="unknown_hold_requires_reconciliation"):
        ledger.release(hold.hold_id)


def test_reconcile_unknown_requires_evidence_and_settles() -> None:
    ledger = _ledger()
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.5, model_calls=1)
    ledger.settle(hold.hold_id, spend_usd=0.5, model_calls=1, usage_unknown=True)
    with pytest.raises(AccountingError, match="reconcile_requires_evidence_ref"):
        ledger.reconcile_unknown(
            hold.hold_id, spend_usd=0.2, model_calls=1, tool_calls=0, evidence_ref=""
        )
    ledger.reconcile_unknown(
        hold.hold_id, spend_usd=0.2, model_calls=1, tool_calls=0, evidence_ref="usage:rq_1"
    )
    assert ledger.holds[hold.hold_id].state == "settled"
    assert ledger.remaining().spend_usd == pytest.approx(0.8)
    assert ledger.remaining().usage_unknown is False
