"""Regression detectors for injected accounting / recovery / permission failures."""

from __future__ import annotations

from swarm.contracts.enums import ReservationPhase, SettlementState
from swarm.contracts.fixtures import sample_receipt, sample_reservation


class DoubleSettleError(PermissionError):
    pass


class SettlementLedger:
    """Minimal ledger that refuses double-settle of the same logical call."""

    def __init__(self) -> None:
        self._settled: set[str] = set()

    def settle(self, logical_call_id: str, state: SettlementState) -> None:
        if state == SettlementState.UNKNOWN:
            # Unknown must not settle — reconcile later.
            return
        if logical_call_id in self._settled:
            raise DoubleSettleError(f"double_settle:{logical_call_id}")
        if state == SettlementState.SETTLED:
            self._settled.add(logical_call_id)


def detect_unknown_must_not_double_settle() -> bool:
    """Injected failure pattern: UNKNOWN outcome then second settle attempt."""
    ledger = SettlementLedger()
    receipt = sample_receipt().model_copy(
        update={
            "send_phase": ReservationPhase.UNKNOWN,
            "settlement_state": SettlementState.UNKNOWN,
        }
    )
    ledger.settle(receipt.logical_call_id, receipt.settlement_state)
    # First real settle OK.
    ledger.settle(receipt.logical_call_id, SettlementState.SETTLED)
    try:
        ledger.settle(receipt.logical_call_id, SettlementState.SETTLED)
        return False  # detector failed — double settle allowed
    except DoubleSettleError:
        return True


def detect_reservation_unknown_phase_preserved() -> bool:
    res = sample_reservation().model_copy(update={"phase": ReservationPhase.UNKNOWN})
    return res.phase == ReservationPhase.UNKNOWN
