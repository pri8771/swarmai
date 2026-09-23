"""G11 RUN-111 — durable mission identity across API store restarts."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.api.store import ProductStore
from swarm.contracts.fixtures import sample_mission


@pytest.mark.asyncio
async def test_api_mission_survives_store_restart(tmp_path: Path) -> None:
    store_a = ProductStore(repo_root=tmp_path)
    mission = sample_mission()
    created = await store_a.create_mission(mission, actor="tester")
    mid = created.id
    assert (tmp_path / "var" / "missions" / f"{mid}.json").exists()

    # Simulate process restart: empty controller, same durable root.
    store_b = ProductStore(repo_root=tmp_path)
    assert mid not in store_b.controller.missions
    loaded = store_b.get_mission(mid)
    assert loaded.id == mid
    assert loaded.objective == created.objective
    assert loaded.project_id == created.project_id

    listed = store_b.list_public_missions(project_id=created.project_id)
    assert any(row["mission_id"] == mid for row in listed)


@pytest.mark.asyncio
async def test_cli_file_mission_visible_to_api_list(tmp_path: Path) -> None:
    from swarm.contracts.common import utc_now
    from swarm.mission.store import MissionRecord, MissionStore

    missions = MissionStore(tmp_path / "var" / "missions")
    mid = "msn_cli_shared"
    missions.save(
        MissionRecord(
            mission_id=mid,
            goal="cli-created unfamiliar goal",
            status="running",
            created_at=utc_now().isoformat(),
            updated_at=utc_now().isoformat(),
            project_id="proj_shared",
            source="cli",
            contract=sample_mission()
            .model_copy(update={"id": mid, "objective": "cli-created unfamiliar goal"})
            .model_dump(mode="json"),
        )
    )
    api = ProductStore(repo_root=tmp_path)
    rows = api.list_public_missions(project_id="proj_shared")
    assert any(r["mission_id"] == mid for r in rows)
    assert api.get_mission(mid).objective == "cli-created unfamiliar goal"
