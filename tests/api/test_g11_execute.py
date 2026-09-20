"""G11 mission execute API — durable ID + zero-spend worker path."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from swarm.api.app import create_app


def test_execute_extract_mission_zero_spend(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SWARM_ALLOW_PAID", "false")
    app = create_app(
        seed_loopback_token="atk_loopback_demo",
        seed_fixtures=False,
        repo_root=tmp_path,
        install_project_id="proj_install_g11_test",
    )
    client = TestClient(app)
    headers = {"Authorization": "Bearer atk_loopback_demo"}
    created = client.post(
        "/v1/missions",
        headers=headers,
        json={
            "mission": {
                "project_id": "proj_install_g11_test",
                "objective": "extract fields from unfamiliar note: alpha=1 beta=two",
                "acceptance_criteria": ["operator review"],
                "allowed_capabilities": ["code.read"],
                "data_scope_ids": ["scope_local"],
                "resource_policy_id": "policy_default",
                "max_wall_time_seconds": 600,
                "max_graph_nodes": 20,
                "max_active_sessions": 2,
                "max_model_calls": 10,
            },
            "task_family": "extract",
            "required_checks": {
                "inference_ok": True,
                "nonempty_output": True,
                "no_known_answer_path": True,
            },
        },
    )
    assert created.status_code == 200, created.text
    mid = created.json()["mission"]["id"]

    executed = client.post(
        f"/v1/missions/{mid}/execute",
        headers=headers,
        json={"model": "gemma3:4b"},
    )
    assert executed.status_code == 200, executed.text
    body = executed.json()
    assert body["mission_id"] == mid
    assert body["task_family"] == "extract"
    assert body["cost"]["total_usd"] == 0.0
    assert body["mock_vs_live"] == "local_ollama_worker_execution_zero_spend"
    # Honest: may pass or fail depending on local Ollama; never invent.
    assert "accepted" in body
    assert "worker_ok" in body
    assert body["status"] in {"completed", "failed"}
