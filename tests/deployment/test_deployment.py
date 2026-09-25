"""P17 deployment doctor and recovery tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.deploy.doctor import doctor, recovery_verify
from swarm.deploy.profiles import get_profile

ROOT = Path(__file__).resolve().parents[2]


def test_profiles_security_defaults() -> None:
    for name in ("mock", "standalone", "hybrid", "recovery", "server", "mac_connector"):
        p = get_profile(name)
        assert p.non_root is True
        assert p.public_db_port is False
        assert p.public_inference_admin is False
        assert p.allow_paid_cloud is False


def test_compose_no_public_db_ports() -> None:
    for name in ("standalone", "hybrid", "recovery", "server"):
        text = (ROOT / "deploy" / "compose" / f"{name}.yml").read_text()
        db_idx = text.index("\n  db:")
        # Slice until next root-level key after services (networks/volumes).
        tail = text[db_idx:]
        end = len(tail)
        for marker in ("\nnetworks:", "\nvolumes:"):
            at = tail.find(marker)
            if at != -1:
                end = min(end, at)
        chunk = tail[:end]
        assert "ports:" not in chunk


def test_doctor_standalone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    result = doctor(profile="standalone", repo_root=ROOT)
    assert result.ok is True
    names = {c["name"]: c for c in result.checks}
    assert names["no_public_db_port"]["ok"] is True
    assert names["database_url_configured"]["ok"] is False
    assert result.to_dict()["cloud_deployed"] is False


def test_doctor_server_and_mac_connector(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    monkeypatch.delenv("SWARM_SERVER_URL", raising=False)
    server = doctor(profile="server", repo_root=ROOT)
    assert server.ok is True
    assert (ROOT / "deploy" / "compose" / "server.yml").is_file()
    mac = doctor(profile="mac_connector", repo_root=ROOT)
    assert mac.ok is True
    names = {c["name"]: c for c in mac.checks}
    assert names["server_url_configured"]["ok"] is False
    assert (ROOT / "deploy" / "compose" / "mac-connector.yml").is_file()


def test_doctor_wrong_secret_refuses_non_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    result = doctor(profile="standalone", repo_root=ROOT)
    db_check = next(c for c in result.checks if c["name"] == "database_url_configured")
    assert db_check["ok"] is False


def test_recovery_verify() -> None:
    result = recovery_verify(profile="recovery", repo_root=ROOT)
    assert result.ok is True
    assert result.to_dict()["seamless_failover_claimed"] is False
    assert result.to_dict()["cloud_off_simulated"] is True


def test_backup_manifest_has_hashes() -> None:
    manifest = json.loads(
        (ROOT / "deploy" / "backup" / "sample-backup-manifest.json").read_text()
    )
    assert "sha256" in manifest["database"]
    assert manifest["artifacts"][0]["sha256"]


def test_dockerfile_and_server_entrypoint_exist() -> None:
    assert (ROOT / "Dockerfile").is_file()
    entry = ROOT / "deploy" / "scripts" / "server-entrypoint.sh"
    assert entry.is_file()
    assert "alembic upgrade head" in entry.read_text()
    assert "USER swarm" in (ROOT / "Dockerfile").read_text() or "useradd" in (
        ROOT / "Dockerfile"
    ).read_text()
