"""V2A-003X — isolated DBOS lease/fencing mapping spike tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.spike.dbos_lease_mapping import (
    mapping_observations,
    run_idempotent_claim_spike,
    run_stale_renew_fence_spike,
)


@pytest.mark.asyncio
async def test_dbos_idempotent_claim_workflow_id(tmp_path: Path) -> None:
    result = await run_idempotent_claim_spike(tmp_path / "lease-map.sqlite")
    assert result["first"]["ok"] is True
    assert result["claim_count_process_1"] == 1
    # After restart, FakeLeaseAuthority is re-seeded (Swarm SQL would reload stamps).
    # DBOS workflow-id dedupe means the workflow body may not re-apply; document both.
    assert result["dbos_version"] == "3.0.0"
    assert "Swarm authority" in result["note"]


@pytest.mark.asyncio
async def test_stale_renew_requires_swarm_authority_stamps(tmp_path: Path) -> None:
    result = await run_stale_renew_fence_spike(tmp_path / "renew-fence.sqlite")
    assert result["claim"]["ok"] is True
    assert result["renew"]["ok"] is False
    assert result["renew"]["reason"] == "authority_stale"
    assert "renew_denied_stale" in result["events"]


def test_mapping_observations_partial_reuse() -> None:
    obs = mapping_observations()
    assert obs["installed_dbos"] == "3.0.0"
    assert obs["recommendation"] == "partial_reuse"
    assert "cancellation_generation" in obs["dbos_gap"]
