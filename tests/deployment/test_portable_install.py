"""P3 portable install docs and doctor start-readiness tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from swarm.deploy.doctor import doctor

ROOT = Path(__file__).resolve().parents[2]

_PERSONAL_PATH = re.compile(r"/Users/[A-Za-z0-9._-]+")
_SPLITSIGNAL = "swarm.splitsignal.ai"


def test_portable_install_docs_exist() -> None:
    required = [
        "docs/install/README.md",
        "docs/install/FRESH_INSTALL.md",
        "docs/install/SERVER_WORKER_STARTUP.md",
        "docs/install/CONFIG_AND_SECRETS.md",
        "docs/install/ENROLLMENT_AND_REVOCATION.md",
        "docs/install/STORAGE_BACKUP_RESTORE.md",
        "docs/install/HEALTH_AND_READINESS.md",
        "docs/install/URLS_AND_INGRESS.md",
        "docs/reference/README.md",
        "docs/reference/R730-SERVER.md",
        "docs/reference/MAC-CONNECTOR.md",
        "docs/reference/CLOUDFLARE-TUNNEL.md",
        "examples/fresh-install/README.md",
        "examples/fresh-install/portable.env.example",
        "deploy/env/portable.env.example",
        "deploy/env/worker-connector.env.example",
    ]
    for rel in required:
        assert (ROOT / rel).is_file(), rel


def test_fresh_install_example_has_no_personal_credentials_or_paths() -> None:
    paths = [
        ROOT / "docs/install/FRESH_INSTALL.md",
        ROOT / "examples/fresh-install/README.md",
        ROOT / "examples/fresh-install/portable.env.example",
        ROOT / "deploy/env/portable.env.example",
    ]
    for path in paths:
        text = path.read_text()
        assert _SPLITSIGNAL not in text, path
        assert not _PERSONAL_PATH.search(text), path
        assert "pchordia" not in text.lower(), path
        # Placeholders / blanks only — no obvious committed secrets.
        assert "sk-" not in text
        assert "eyJ" not in text


def test_reference_guides_are_labelled() -> None:
    for rel in (
        "docs/reference/R730-SERVER.md",
        "docs/reference/MAC-CONNECTOR.md",
        "docs/reference/CLOUDFLARE-TUNNEL.md",
    ):
        text = (ROOT / rel).read_text()
        assert "REFERENCE ONLY" in text
        assert "docs/install/" in text or "../install/" in text


def test_tunnel_example_uses_placeholder_hostname() -> None:
    text = (ROOT / "deploy/cloudflare/tunnel.example.yml").read_text()
    assert "coordinator.example.test" in text
    assert _SPLITSIGNAL not in text


def test_doctor_mock_ready_to_start(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    monkeypatch.delenv("SWARM_SERVER_URL", raising=False)
    monkeypatch.delenv("SWARM_PUBLIC_HOSTNAME", raising=False)
    monkeypatch.delenv("SWARM_API_BASE_URL", raising=False)
    monkeypatch.delenv("SWARM_API_PUBLIC_URL", raising=False)
    monkeypatch.delenv("SWARM_PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("SWARM_SECRET_BACKEND", raising=False)
    result = doctor(profile="mock", repo_root=ROOT)
    assert result.ok is True
    assert result.ready_to_start is True
    assert result.config_errors == []


def test_doctor_standalone_not_ready_without_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    monkeypatch.delenv("SWARM_PUBLIC_HOSTNAME", raising=False)
    monkeypatch.delenv("SWARM_API_BASE_URL", raising=False)
    monkeypatch.delenv("SWARM_API_PUBLIC_URL", raising=False)
    monkeypatch.delenv("SWARM_PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("SWARM_SERVER_URL", raising=False)
    result = doctor(profile="standalone", repo_root=ROOT)
    assert result.ok is True
    assert result.ready_to_start is False
    assert "missing_env:SWARM_DATABASE_URL" in result.config_errors
    payload = result.to_dict()
    assert payload["ready_to_start"] is False
    assert "config_errors" in payload


def test_doctor_rejects_bad_public_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWARM_DATABASE_URL", "postgresql+psycopg://swarm:x@127.0.0.1:5432/swarm")
    monkeypatch.delenv("SWARM_SERVER_URL", raising=False)
    monkeypatch.delenv("SWARM_API_PUBLIC_URL", raising=False)
    monkeypatch.delenv("SWARM_PUBLIC_BASE_URL", raising=False)
    monkeypatch.setenv("SWARM_API_BASE_URL", "not-a-url")
    result = doctor(profile="standalone", repo_root=ROOT)
    assert result.ready_to_start is False
    assert any(e.startswith("invalid_api_base_url:") for e in result.config_errors)


def test_doctor_connector_requires_server_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_SERVER_URL", raising=False)
    result = doctor(profile="mac_connector", repo_root=ROOT)
    assert result.ok is True
    assert result.ready_to_start is False
    assert "missing_env:SWARM_SERVER_URL" in result.config_errors


def test_server_env_example_uses_placeholder_hostname() -> None:
    text = (ROOT / "deploy/env/server.env.example").read_text()
    assert "coordinator.example.test" in text
    assert _SPLITSIGNAL not in text
