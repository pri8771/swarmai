"""Board + succession + durable mailbox integration (PC-07 / L4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.mission.collab import CollaborativeMissionBoard
from swarm.runtime.succession import SuccessionService


def test_legacy_peer_handoff_still_works() -> None:
    board = CollaborativeMissionBoard(mission_id="msn_collab_1")
    board.join("agent_x")
    board.join("agent_y")
    board.post(
        from_agent="agent_x",
        to_agent="agent_y",
        kind="request_help",
        body="Need help",
        evidence_refs=["art_1"],
    )
    handoff = board.prepare_handoff(
        from_agent="agent_x",
        to_agent="agent_y",
        retained_facts=["email_count=2"],
        open_commitments=["submit"],
        event_watermark="wm_1",
    )
    board.adopt_handoff(handoff.handoff_id, by_agent="agent_y")
    assert board.can_claim_work("agent_x") is False
    assert board.can_claim_work("agent_y") is True


def test_authenticated_mailbox_on_board(tmp_path: Path) -> None:
    board = CollaborativeMissionBoard(mission_id="msn_auth", project_id="proj_a")
    board.enable_durable_mailbox(tmp_path / "mail")
    board.join("agent_x")
    board.join("agent_y")
    msg = board.post(
        from_agent="agent_x",
        to_agent="agent_y",
        kind="request_help",
        body="peer help please",
        correlation_id="c1",
    )
    assert msg.sender_session_id
    assert msg.sender_generation == 1
    assert msg.event_order == 1
    with pytest.raises(PermissionError, match="authority_expansion"):
        board.post(from_agent="agent_x", kind="status", body="expand_budget please")


def test_run_xy_succession_fences_old_generation(tmp_path: Path) -> None:
    board = CollaborativeMissionBoard(mission_id="msn_xy", project_id="proj_a")
    svc = SuccessionService()
    board.enable_succession(svc)
    board.enable_durable_mailbox(tmp_path / "mail")
    board.join("lag_worker")
    usable = svc.usable_capacity(8_192, output_reserve=512)
    snap = svc.occupancy_of(int(usable * 0.90), usable)
    handoff = board.run_xy_succession(
        logical_agent_id="lag_worker",
        occupancy=snap,
        objective="continue mission",
        retained_facts=["placement=mac_local"],
        open_commitments=["submit_protected_review"],
        event_watermark="wm_xy",
    )
    assert handoff.adopted is True
    assert handoff.succession_id
    assert handoff.kt1_digest and handoff.kt2_digest
    assert board.active_generation["lag_worker"] == 2
    assert board.can_claim_work("lag_worker") is True
    # Old generation cannot claim.
    assert svc.can_claim_work("lag_worker", generation=1) is False
    evidence = board.evidence()
    assert "succession" in evidence
    assert "mailbox" in evidence
