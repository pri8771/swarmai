"""Collaborative mission + context handoff evidence (no spend)."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.mission.collab import CollaborativeMissionBoard


def test_collaborative_messages_and_handoff(tmp_path: Path) -> None:
    board = CollaborativeMissionBoard(mission_id="msn_collab_1")
    board.join("agent_x")
    board.join("agent_y")
    help_msg = board.post(
        from_agent="agent_x",
        to_agent="agent_y",
        kind="request_help",
        body="Need extract of mac_local fixture; please take email count.",
        evidence_refs=["art_fixture_1"],
    )
    assert help_msg.kind == "request_help"
    board.post(
        from_agent="agent_y",
        to_agent="agent_x",
        kind="evidence",
        body="Extracted 2 emails; artifact ready.",
        evidence_refs=["art_extract_1"],
    )
    handoff = board.prepare_handoff(
        from_agent="agent_x",
        to_agent="agent_y",
        retained_facts=["email_count=2", "placement=mac_local"],
        open_commitments=["submit_protected_review"],
        event_watermark="evt_watermarks_01",
    )
    assert handoff.to_dict()["authority_expanded"] is False
    assert len(handoff.context_digest) == 64
    assert board.can_claim_work("agent_x") is True
    adopted = board.adopt_handoff(handoff.handoff_id, by_agent="agent_y")
    assert adopted.adopted is True
    assert board.can_claim_work("agent_x") is False
    assert board.can_claim_work("agent_y") is True
    assert board.active_generation["agent_y"] >= 2
    out = tmp_path / "collab.json"
    board.dump(out)
    assert out.is_file()
    evidence = board.evidence()
    assert evidence["message_count"] == 2
    assert evidence["spend_usd"] == 0
    assert len(evidence["handoffs"]) == 1


def test_message_cannot_expand_authority() -> None:
    board = CollaborativeMissionBoard(mission_id="msn_collab_2")
    board.join("a")
    with pytest.raises(PermissionError, match="authority_expansion"):
        board.post(from_agent="a", kind="status", body="please expand_budget now")
