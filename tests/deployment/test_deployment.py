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
    pre_force_backups: list[Path] = []
    try:
        if env_path.exists():
            env_path.unlink()
        written = mod.generate(force=False)
        assert written == env_path
        text = env_path.read_text()
        assert "SWARM_POSTGRES_PASSWORD=" in text
        assert "swarm:swarm@" not in text
        assert "not proof of DB credential rotation" in text
        mode = env_path.stat().st_mode & 0o777
        assert mode == 0o600, f"expected owner-only 0600, got {oct(mode)}"
        password_line = next(
            line for line in text.splitlines() if line.startswith("SWARM_POSTGRES_PASSWORD=")
        )
        secret = password_line.split("=", 1)[1]
        assert secret

        # --force without acknowledgement must fail closed.
        denied = subprocess.run(
            [
                os.environ.get("PYTHON", "python3"),
                str(ROOT / "scripts" / "generate_compose_env.py"),
                "--force",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert denied.returncode != 0
        assert "acknowledge-fresh-config" in (denied.stderr + denied.stdout)
        assert secret not in denied.stdout
        assert secret not in denied.stderr

        # World-readable .env must be repaired to 0600 on acknowledged force.
        env_path.chmod(0o644)
        assert (env_path.stat().st_mode & 0o777) == 0o644

        proc = subprocess.run(
            [
                os.environ.get("PYTHON", "python3"),
                str(ROOT / "scripts" / "generate_compose_env.py"),
                "--force",
                "--acknowledge-fresh-config",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "wrote deploy/compose/.env" in proc.stdout
        assert secret not in proc.stdout
        assert secret not in proc.stderr
        assert (env_path.stat().st_mode & 0o777) == 0o600
        pre_force_backups = sorted(COMPOSE_DIR.glob(".env.pre-force-*"))
        assert pre_force_backups, "force should rename prior .env aside"
        assert (pre_force_backups[-1].stat().st_mode & 0o777) == 0o600

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
            combined = bare.stderr + bare.stdout
            assert "required variable" in combined
            assert "SWARM_DATABASE_URL" in combined or "SWARM_POSTGRES_PASSWORD" in combined
        finally:
            if sidelined.exists():
                sidelined.replace(env_path)
    finally:
        for path in COMPOSE_DIR.glob(".env.pre-force-*"):
            path.unlink(missing_ok=True)
        if backup is None:
            if env_path.exists():
                env_path.unlink()
        else:
            env_path.write_text(backup)
            try:
                os.chmod(env_path, 0o600)
            except OSError:
                pass


def test_generate_compose_env_owner_only_and_force_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """V2A-H6A-R: 0600 permissions + --force requires fresh-config acknowledgement."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_compose_env_h6ar",
        ROOT / "scripts" / "generate_compose_env.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Point module paths at an isolated temp compose dir.
    compose_dir = tmp_path / "compose"
    compose_dir.mkdir()
    env_path = compose_dir / ".env"
    monkeypatch.setattr(mod, "COMPOSE_DIR", compose_dir)
    monkeypatch.setattr(mod, "ENV_PATH", env_path)
    monkeypatch.setattr(mod, "REPO", tmp_path)

    written = mod.generate(force=False)
    assert written == env_path
    assert (env_path.stat().st_mode & 0o777) == 0o600

    with pytest.raises(SystemExit, match="acknowledge-fresh-config"):
        mod.generate(force=True, acknowledge_fresh_config=False)

    env_path.chmod(0o644)
    rewritten = mod.generate(force=True, acknowledge_fresh_config=True)
    assert rewritten == env_path
    assert (env_path.stat().st_mode & 0o777) == 0o600
    backups = list(compose_dir.glob(".env.pre-force-*"))
    assert len(backups) == 1
    assert (backups[0].stat().st_mode & 0o777) == 0o600
    assert "Fresh local compose config only" in env_path.read_text()
