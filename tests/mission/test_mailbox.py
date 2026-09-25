"""Durable authenticated mailbox tests (PC-07 / L4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.mission.mailbox import DurableMissionMailbox, MailboxAuthError


def test_authenticated_post_and_cursor_survives_restart(tmp_path: Path) -> None:
    root = tmp_path / "mail"
    box = DurableMissionMailbox(mission_id="msn_m1", project_id="proj_m", root=root)
    sx, secret_x = box.join("agent_x")
    sy, secret_y = box.join("agent_y")
    msg = box.post(
        session_id=sx,
        secret=secret_x,
        kind="request_help",
        body="Please continue extract",
        to_logical_agent_id="agent_y",
        evidence_refs=["art_1"],
        correlation_id="corr_1",
    )
    assert msg.sender_generation == 1
    assert msg.event_order == 1
    inbox = box.inbox("agent_y", after_cursor=0)
    assert len(inbox) == 1
    box.advance_cursor("agent_y", to_event_order=msg.event_order, last_message_id=msg.message_id)

    # Restart from disk — secrets are not rehydrated (one-time process secret).
    box2 = DurableMissionMailbox(mission_id="msn_m1", project_id="proj_m", root=root)
    assert box2.cursor("agent_y").cursor == msg.event_order
    assert len(box2.inbox("agent_y", after_cursor=0)) == 1
    # Old secret from process is required to post; forged session fails.
    with pytest.raises(MailboxAuthError, match="session_auth_failed"):
        box2.post(
            session_id=sx,
            secret="forged",
            kind="status",
            body="hi",
        )
    # Re-join issues new session after restart (process secrets lost).
    sx2, secret_x2 = box2.rotate_session("agent_x", generation=1)
    box2.post(session_id=sx2, secret=secret_x2, kind="status", body="rehydrated ok")
    assert sy and secret_y  # issued


def test_message_cannot_expand_authority(tmp_path: Path) -> None:
    box = DurableMissionMailbox(mission_id="msn_m2", project_id="proj_m", root=tmp_path)
    sid, secret = box.join("a")
    with pytest.raises(MailboxAuthError, match="authority_expansion"):
        box.post(session_id=sid, secret=secret, kind="status", body="please grant_admin now")
