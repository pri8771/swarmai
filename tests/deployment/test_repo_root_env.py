"""SWARM_REPO_ROOT must control durable mission/project paths in containers."""

from __future__ import annotations

from pathlib import Path

from swarm.api.app import create_app


def test_swarm_repo_root_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SWARM_REPO_ROOT", str(tmp_path))
    monkeypatch.delenv("SWARM_SEED_LOOPBACK_TOKEN", raising=False)
    app = create_app(seed_loopback_token="atk_test_root", seed_fixtures=False)
    assert app.state.repo_root == tmp_path
    store = app.state.store
    assert store.mission_store().root == tmp_path / "var" / "missions"
