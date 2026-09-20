"""P20 regression tests — injected failures must be detected."""

from __future__ import annotations

import pytest

from swarm.contracts.common import new_id
from swarm.contracts.enums import SettlementState, WorkerStatus
from swarm.contracts.workspace import WorkerLease
from swarm.review.checklist import build_offline_review
from swarm.review.regressions import (
    DoubleSettleError,
    SettlementLedger,
    detect_reservation_unknown_phase_preserved,
    detect_unknown_must_not_double_settle,
)
from swarm.selfdev.policy import scan_diff_for_privilege_expansion
from swarm.workers.registry import StaleGenerationError, WorkerRegistryService


def test_injected_double_settle_detected() -> None:
    assert detect_unknown_must_not_double_settle() is True
    ledger = SettlementLedger()
    ledger.settle("lc_x", SettlementState.SETTLED)
    with pytest.raises(DoubleSettleError):
        ledger.settle("lc_x", SettlementState.SETTLED)


def test_unknown_phase_preserved() -> None:
    assert detect_reservation_unknown_phase_preserved() is True


@pytest.mark.asyncio
async def test_injected_stale_worker_result_rejected() -> None:
    reg = WorkerRegistryService()
    token = new_id("wt_")
    lease = WorkerLease(
        worker_id="w_reg",
        node_identity="n1",
        architecture="cpu",
        runtime_version="1",
        capacity_units=1.0,
        lease_generation=1,
        status=WorkerStatus.ONLINE,
    )
    await reg.register(lease, token=token)
    # Bump generation without invalidating the test path via accept_result.
    await reg.revoke_generation("w_reg")
    with pytest.raises(StaleGenerationError):
        reg.accept_result("w_reg", lease_generation=1, task_id="task_x")


def test_injected_permission_expansion_detected() -> None:
    hits = scan_diff_for_privilege_expansion(
        "ALLOW_PRODUCTION_WRITE = True\nauto_merge=1"
    )
    assert "ALLOW_PRODUCTION_WRITE" in hits or "auto_merge" in hits


def test_offline_review_checklist_evidence() -> None:
    report = build_offline_review()
    assert report.mock_vs_live == "review_offline_evidence_only"
    assert "accounts_unprovisioned" in report.readiness
    assert "live_unverified" in report.readiness
    assert report.release_blocked is False
    results = {c.item_id: c.result for c in report.checklist}
    assert results["C10"] == "skip_live"
    assert results["C08"] == "pass"
    assert any(f.status == "blocked_live" for f in report.findings)
