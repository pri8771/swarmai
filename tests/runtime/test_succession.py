"""X/Y KT1/KT2 succession fencing tests (PC-07 / L4)."""

from __future__ import annotations

import pytest

from swarm.contracts.agent import LogicalAgent
from swarm.contracts.succession import OccupancyPolicy
from swarm.runtime.succession import SuccessionError, SuccessionService


def _svc() -> SuccessionService:
    return SuccessionService(policy=OccupancyPolicy(trainee_at=0.65, takeover_at=0.80))


def _register(svc: SuccessionService, name: str = "lag_primary") -> str:
    logical = LogicalAgent(
        logical_agent_id=name,
        project_id="proj_t",
        display_name=name,
        role="worker",
    )
    svc.register_logical(logical, mission_id="msn_t")
    return name


def test_xy_thresholds_and_policy_validation() -> None:
    with pytest.raises(ValueError, match="require_0_lt_X_lt_Y_lt_1"):
        OccupancyPolicy(trainee_at=0.9, takeover_at=0.5)
    svc = _svc()
    usable = svc.usable_capacity(10_000, output_reserve=1_000)
    assert usable < 10_000 - 1_000
    snap = svc.occupancy_of(int(usable * 0.5), usable)
    assert snap.occupancy < 0.65


def test_kt1_kt2_promote_fences_predecessor() -> None:
    svc = _svc()
    lid = _register(svc)
    usable = svc.usable_capacity(8_192, output_reserve=512)
    # Cross X
    snap_x = svc.occupancy_of(int(usable * 0.70), usable)
    rec = svc.observe_occupancy(
        mission_id="msn_t",
        project_id="proj_t",
        logical_agent_id=lid,
        snapshot=snap_x,
    )
    assert rec is not None
    assert rec.phase == "trainee_created"
    assert rec.trainee_generation == 2

    kt1 = svc.issue_kt1(
        rec.succession_id,
        objective="finish extract",
        decisions=["use mac_local"],
        evidence_refs=["art_1"],
        grants_summary=["scope:mac_local"],
        open_commitments=["submit_result"],
        current_task="extract",
        memory_refs=["mem_1"],
        event_watermark="wm_1",
        inbox_cursor=3,
    )
    svc.trainee_ack_kt1(rec.succession_id, ack_digest=kt1.content_digest)
    assert svc.open_succession(lid).phase == "shadowing"
    # Parent may still effect while shadowing; trainee may not.
    assert svc.can_issue_effects(lid, generation=1) is True
    assert svc.can_issue_effects(lid, generation=2) is False

    # Cross Y
    snap_y = svc.occupancy_of(int(usable * 0.85), usable)
    rec2 = svc.observe_occupancy(
        mission_id="msn_t",
        project_id="proj_t",
        logical_agent_id=lid,
        snapshot=snap_y,
    )
    assert rec2 is not None
    assert rec2.phase == "final_kt"
    assert svc.can_issue_effects(lid, generation=1) is False

    kt2 = svc.issue_kt2(
        rec.succession_id,
        deltas=["email_count=2"],
        unresolved_issues=[],
        final_event_watermark="wm_2",
        final_inbox_cursor=5,
    )
    svc.trainee_ack_kt2(rec.succession_id, ack_digest=kt2.content_digest)
    promoted = svc.promote(rec.succession_id)
    assert promoted.phase == "promoted"
    assert svc.can_issue_effects(lid, generation=1) is False
    assert svc.can_issue_effects(lid, generation=2) is True
    lineage = svc.get_lineage(lid)
    assert lineage.active().generation == 2
    assert lineage.active().role == "active"


def test_kt1_integrity_mismatch_blocks() -> None:
    svc = _svc()
    lid = _register(svc)
    usable = svc.usable_capacity(4_096, output_reserve=256)
    snap = svc.occupancy_of(int(usable * 0.70), usable)
    rec = svc.observe_occupancy(
        mission_id="msn_t",
        project_id="proj_t",
        logical_agent_id=lid,
        snapshot=snap,
    )
    assert rec is not None
    kt1 = svc.issue_kt1(
        rec.succession_id,
        objective="o",
        decisions=[],
        evidence_refs=[],
        grants_summary=[],
        open_commitments=[],
        current_task="t",
        memory_refs=[],
        event_watermark="w",
        inbox_cursor=0,
    )
    with pytest.raises(SuccessionError, match="kt1_integrity_mismatch"):
        svc.trainee_ack_kt1(rec.succession_id, ack_digest="deadbeef")
    assert kt1.content_digest
    assert svc.open_succession(lid).phase == "blocked"


def test_abrupt_xy_jump_enters_final_kt() -> None:
    svc = _svc()
    lid = _register(svc)
    usable = svc.usable_capacity(4_096, output_reserve=256)
    snap = svc.occupancy_of(int(usable * 0.95), usable)
    rec = svc.observe_occupancy(
        mission_id="msn_t",
        project_id="proj_t",
        logical_agent_id=lid,
        snapshot=snap,
    )
    assert rec is not None
    assert rec.phase == "final_kt"
