"""P17 / V2A-H6A deployment doctor, secrets, and compose smoke tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from swarm.db.engine import DatabaseConfigError, database_url
from swarm.deploy.doctor import doctor, recovery_verify
from swarm.deploy.profiles import get_profile

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_DIR = ROOT / "deploy" / "compose"


def test_profiles_security_defaults() -> None:
    for name in ("mock", "standalone", "hybrid", "recovery"):
        p = get_profile(name)
        assert p.non_root is True
        assert p.public_db_port is False
        assert p.public_inference_admin is False
        assert p.allow_paid_cloud is False


def test_compose_no_public_db_ports() -> None:
    for name in ("standalone", "hybrid", "recovery"):
        text = (COMPOSE_DIR / f"{name}.yml").read_text()
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


def test_compose_has_no_fixed_swarm_password() -> None:
    for name in ("standalone", "hybrid", "recovery"):
        text = (COMPOSE_DIR / f"{name}.yml").read_text()
        assert "POSTGRES_PASSWORD: swarm" not in text
        assert "swarm:swarm@" not in text
        assert "${SWARM_POSTGRES_PASSWORD:?" in text
        assert "${SWARM_DATABASE_URL:?" in text
        assert "127.0.0.1:8765:8765" in text


def test_database_url_fail_closed_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    with pytest.raises(DatabaseConfigError, match="unset"):
        database_url()


def test_database_url_rejects_fixed_demo_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "SWARM_DATABASE_URL",
        "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm",
    )
    with pytest.raises(DatabaseConfigError, match="forbidden fixed demo credential"):
        database_url()


def test_doctor_standalone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    result = doctor(profile="standalone", repo_root=ROOT)
    assert result.ok is True
    names = {c["name"]: c for c in result.checks}
    assert names["no_public_db_port"]["ok"] is True
    assert names["database_url_configured"]["ok"] is False
    assert names["compose_no_fixed_db_password"]["ok"] is True
    assert names["compose_loopback_api_bind"]["ok"] is True
    assert names["compose_requires_secret_vars"]["ok"] is True
    assert result.to_dict()["cloud_deployed"] is False


def test_doctor_wrong_secret_refuses_non_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    result = doctor(profile="standalone", repo_root=ROOT)
    db_check = next(c for c in result.checks if c["name"] == "database_url_configured")
    assert db_check["ok"] is False


def test_doctor_rejects_fixed_credential_in_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "SWARM_DATABASE_URL",
        "postgresql+psycopg://swarm:swarm@db:5432/swarm",
    )
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


def test_generate_compose_env_and_compose_config_smoke() -> None:
    """Real compose config smoke when docker is available; else static secret checks."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_compose_env",
        ROOT / "scripts" / "generate_compose_env.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    env_path = COMPOSE_DIR / ".env"
    backup = env_path.read_text() if env_path.exists() else None
    try:
        if env_path.exists():
            env_path.unlink()
        written = mod.generate(force=False)
        assert written == env_path
        text = env_path.read_text()
        assert "SWARM_POSTGRES_PASSWORD=" in text
        assert "swarm:swarm@" not in text
        password_line = next(
            line for line in text.splitlines() if line.startswith("SWARM_POSTGRES_PASSWORD=")
        )
        secret = password_line.split("=", 1)[1]
        assert secret

        proc = subprocess.run(
            [
                os.environ.get("PYTHON", "python3"),
                str(ROOT / "scripts" / "generate_compose_env.py"),
                "--force",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "wrote deploy/compose/.env" in proc.stdout
        assert secret not in proc.stdout
        assert secret not in proc.stderr

        docker = shutil.which("docker")
        if docker is None:
            pytest.skip("docker_unavailable")
        cfg = subprocess.run(
            [
                docker,
                "compose",
                "--env-file",
                str(env_path),
                "-f",
                str(COMPOSE_DIR / "standalone.yml"),
                "config",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert cfg.returncode == 0, cfg.stderr
        assert "host_ip: 127.0.0.1" in cfg.stdout
        assert 'published: "8765"' in cfg.stdout or "published: 8765" in cfg.stdout
        assert "POSTGRES_PASSWORD: swarm\n" not in cfg.stdout
        assert "swarm:swarm@" not in cfg.stdout
        assert "internal: true" in cfg.stdout
        # Unconfigured compose must fail closed (no auto-loaded .env).
        sidelined = env_path.with_suffix(".env.sidelined-test")
        env_path.replace(sidelined)
        try:
            bare_env = {
                k: v
                for k, v in os.environ.items()
                if not k.startswith("SWARM_") and k != "POSTGRES_PASSWORD"
            }
            bare = subprocess.run(
                [
                    docker,
                    "compose",
                    "-f",
                    str(COMPOSE_DIR / "standalone.yml"),
                    "config",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=bare_env,
            )
            assert bare.returncode != 0
            assert "SWARM_POSTGRES_PASSWORD" in (bare.stderr + bare.stdout)
        finally:
            if sidelined.exists():
                sidelined.replace(env_path)
    finally:
        if backup is None:
            if env_path.exists():
                env_path.unlink()
        else:
            env_path.write_text(backup)
