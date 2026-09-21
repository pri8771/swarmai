#!/usr/bin/env python3
"""RUN-111 durable mission identity proof (API + MissionStore), loopback only."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from swarm.api.app import create_app
from swarm.mission.store import MissionStore


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        app = create_app(
            seed_loopback_token="atk_loopback_demo",
            seed_fixtures=False,
            repo_root=root,
        )
        client = TestClient(app)
        headers = {"Authorization": "Bearer atk_loopback_demo"}
        body = {
            "mission": {
                "project_id": "proj_demo",
                "objective": "triage unfamiliar intermittent timeout family",
                "acceptance_criteria": ["reproducible diagnosis"],
                "allowed_capabilities": ["code.read"],
                "data_scope_ids": ["scope_local"],
                "resource_policy_id": "policy_default",
                "max_wall_time_seconds": 600,
                "max_graph_nodes": 20,
                "max_active_sessions": 2,
                "max_model_calls": 10,
            }
        }
        created = client.post("/v1/missions", headers=headers, json=body)
        assert created.status_code == 200, created.text
        mission = created.json()["mission"]
        mid = mission["id"]

        listed = client.get("/v1/missions", headers=headers)
        assert listed.status_code == 200
        ids = [i["mission_id"] for i in listed.json()["missions"]]
        assert mid in ids

        # Fresh app = process restart simulation, same durable root.
        app2 = create_app(
            seed_loopback_token="atk_loopback_demo",
            seed_fixtures=False,
            repo_root=root,
        )
        client2 = TestClient(app2)
        got = client2.get(f"/v1/missions/{mid}", headers=headers)
        assert got.status_code == 200, got.text
        assert got.json()["mission"]["objective"] == body["mission"]["objective"]

        listed2 = client2.get("/v1/missions", headers=headers)
        assert mid in [i["mission_id"] for i in listed2.json()["missions"]]

        store = MissionStore(root / "var" / "missions")
        record = store.load(mid)
        evidence = {
            "mission_id": mid,
            "api_list_contains": mid in ids,
            "reopened_after_restart": True,
            "list_after_restart_contains": True,
            "store_goal": record.goal,
            "store_source": record.source,
            "fixture_seeded": False,
            "spend": 0,
        }
        out = Path("docs/evidence/run-111")
        out.mkdir(parents=True, exist_ok=True)
        (out / "durable-identity-proof.json").write_text(
            json.dumps(evidence, indent=2) + "\n"
        )
        print(json.dumps(evidence, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
