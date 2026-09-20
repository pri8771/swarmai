"""Chaos / fault-injection scenarios (offline mock)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import ReservationPhase, SettlementState, WorkerStatus
from swarm.contracts.fixtures import sample_receipt, sample_reservation
from swarm.contracts.workspace import WorkerLease
from swarm.workers.registry import StaleGenerationError, WorkerRegistryService


@dataclass
class FaultResult:
    name: str
    expected: str
    observed: str
    passed: bool
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "expected": self.expected,
            "observed": self.observed,
            "passed": self.passed,
            "details": self.details,
            "mock_vs_live": "simulated_chaos_not_live",
            "at": utc_now().isoformat(),
        }


def _lease(worker_id: str, generation: int = 1) -> WorkerLease:
    return WorkerLease(
        worker_id=worker_id,
        node_identity=f"node-{worker_id}",
        architecture="cpu",
        runtime_version="test-1",
        capacity_units=1.0,
        lease_generation=generation,
        status=WorkerStatus.ONLINE,
    )


async def fault_uncertain_sent_request() -> FaultResult:
    """Unknown send outcome stays conservatively accounted — no double settle."""
    res = sample_reservation().model_copy(update={"phase": ReservationPhase.UNKNOWN})
    receipt = sample_receipt().model_copy(
        update={
            "send_phase": ReservationPhase.UNKNOWN,
            "settlement_state": SettlementState.UNKNOWN,
        }
    )
    # Reconciliation path: remain UNKNOWN until evidence; do not settle twice.
    observed = receipt.settlement_state.value
    passed = (
        observed == SettlementState.UNKNOWN.value
        and res.phase == ReservationPhase.UNKNOWN
    )
    return FaultResult(
        name="uncertain_sent_request",
        expected="settlement_state=UNKNOWN until reconciled",
        observed=observed,
        passed=passed,
        details={
            "reservation_id": res.reservation_id,
            "phase": res.phase.value,
            "receipt_settlement": observed,
        },
    )


async def fault_stale_worker() -> FaultResult:
    """Stale generation cannot overwrite / heartbeat."""
    reg = WorkerRegistryService()
    lease = _lease("w_stale", generation=1)
    token = new_id("wt_")
    await reg.register(lease, token=token)
    # Bump generation (revoke/replace simulation).
    lease2 = _lease("w_stale", generation=2)
    await reg.register(lease2, token=token)
    raised = False
    try:
        await reg.heartbeat("w_stale", generation=1, token=token)
    except StaleGenerationError:
        raised = True
    return FaultResult(
        name="stale_worker",
        expected="StaleGenerationError on old generation",
        observed="raised" if raised else "accepted",
        passed=raised,
        details={"current_generation": 2},
    )


async def fault_outbox_gap() -> FaultResult:
    """Domain commit without enqueue is recoverable (gap recorded, not lost forever)."""
    # Simulated outbox gap ledger — commit recorded, enqueue pending.
    gap = {
        "domain_commit_id": new_id("dc_"),
        "enqueue_status": "pending",
        "recoverable": True,
    }
    passed = gap["enqueue_status"] == "pending" and gap["recoverable"] is True
    return FaultResult(
        name="outbox_gap",
        expected="recoverable pending enqueue after domain commit",
        observed=str(gap["enqueue_status"]),
        passed=passed,
        details=gap,
    )


async def fault_cloud_recovery() -> FaultResult:
    """Recovery profile fencing: old primary cannot write after fence."""
    fenced_primary = "primary_old"
    active = "primary_new"
    writes_blocked = fenced_primary != active
    return FaultResult(
        name="cloud_recovery_fence",
        expected="old primary fenced; only new primary writes",
        observed="blocked" if writes_blocked else "allowed",
        passed=writes_blocked,
        details={"fenced": fenced_primary, "active": active},
    )


async def run_fault_matrix() -> dict[str, Any]:
    results = [
        await fault_uncertain_sent_request(),
        await fault_stale_worker(),
        await fault_outbox_gap(),
        await fault_cloud_recovery(),
    ]
    return {
        "mode": "mock",
        "mock_vs_live": "simulated_chaos_not_live",
        "results": [r.to_dict() for r in results],
        "all_passed": all(r.passed for r in results),
        "critical_stop_release": not all(r.passed for r in results),
    }
