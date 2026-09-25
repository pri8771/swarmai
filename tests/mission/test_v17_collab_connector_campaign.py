"""Collab + X→Y handoff through continuous connector lease path."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.mission.collab_connector_campaign import run_collab_connector_campaign


@pytest.mark.asyncio
async def test_collab_through_continuous_connector(tmp_path: Path) -> None:
    report = await run_collab_connector_campaign(
        evidence_dir=tmp_path / "evidence",
        fixture_dir=tmp_path / "fixtures",
    )
    assert report.ok is True
    assert report.one_shot is False
    assert report.self_accepted is False
    assert report.predecessor_blocked_after_handoff is True
    assert report.successor_submitted is True
    assert report.spend_usd == 0.0
    steps = {s["step"]: s for s in report.connector_steps}
    assert steps["claim"]["claimed"] is True
    assert steps["renew"]["state"] == "renewed"
    assert steps["submit_result"]["acceptance_state"] == "pending"
    assert steps["predecessor_post_handoff_claim"]["claimed"] is False
    handoffs = report.collab["handoffs"]
    assert len(handoffs) == 1
    assert handoffs[0]["adopted"] is True
    assert handoffs[0]["authority_expanded"] is False
    assert report.collab["active_generation"]["agent_y"] >= 2
    assert list((tmp_path / "evidence").glob("collab-connector-*.json"))
