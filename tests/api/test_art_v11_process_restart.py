"""V2A-002 / ART-V11-RESTART-EVIDENCE — real OS process restart regression."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.v2a002_process_restart_evidence import run_proof


def test_os_process_restart_reopens_durable_mission(tmp_path: Path) -> None:
    out = tmp_path / "process-restart-reopen-operational.json"
    # Distinct uncommon port to avoid colliding with a live proof run.
    evidence = run_proof(port=18792, out_path=out)
    assert evidence["status"] == "pass", json.dumps(evidence.get("checks"), indent=2)
    assert evidence["checks"]["distinct_os_pids"] is True
    assert evidence["checks"]["process_1_exited"] is True
    assert evidence["checks"]["http_reopen_ok"] is True
    assert evidence["checks"]["cli_reopen_ok"] is True
    assert evidence["checks"]["same_durable_id"] is True
    assert evidence["checks"]["same_disk_sha256"] is True
    assert evidence["checks"]["not_create_app_object_only"] is True
    assert evidence["g11_lead_accept_invented"] is False
    assert evidence["process_1"]["pid"] != evidence["process_2"]["pid"]
    assert Path(evidence["evidence_path"]).is_file()


def test_swarm_repo_root_env_selects_durable_root(tmp_path: Path, monkeypatch) -> None:
    from swarm.api.app import create_app

    monkeypatch.setenv("SWARM_REPO_ROOT", str(tmp_path))
    monkeypatch.delenv("SWARM_SEED_LOOPBACK_TOKEN", raising=False)
    app = create_app(seed_loopback_token=None, seed_fixtures=False)
    assert Path(app.state.repo_root) == tmp_path.resolve()
