"""P4 two-container compose validation + optional Docker proof."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from swarm.deploy.doctor import doctor
from swarm.deploy.profiles import get_profile

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy" / "compose" / "portable-protocol.yml"
PROOF = ROOT / "scripts" / "portable_protocol_proof.py"


def test_portable_protocol_compose_exists_and_is_generic() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert "coordinator:" in text
    assert "\n  worker:" in text
    assert "\n  r730:" not in text.lower()
    assert "mac-connector" not in text
    assert "swarm.splitsignal.ai" not in text
    assert "coordinator.example.test" in text
    assert "worker-a.example.test" in text
    # DB must not publish host ports.
    db_idx = text.index("\n  db:")
    tail = text[db_idx:]
    end = len(tail)
    for marker in ("\nnetworks:", "\nvolumes:"):
        at = tail.find(marker)
        if at != -1:
            end = min(end, at)
    assert "ports:" not in tail[:end]
    assert "127.0.0.1:" in text


def test_compose_validate_script() -> None:
    proc = subprocess.run(
        ["uv", "run", "python", str(PROOF), "--mode", "compose-validate"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["checks"]["no_lab_host_service"] is True
    assert payload["checks"]["has_coordinator"] is True


def test_inprocess_proof_script(tmp_path: Path) -> None:
    out = tmp_path / "proof.json"
    proc = subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(PROOF),
            "--mode",
            "inprocess",
            "--workspace",
            str(tmp_path / "ws"),
            "--json-out",
            str(out),
        ],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["named_r730_required"] is False
    assert len(payload["reports"]) >= 4


def test_doctor_still_ok_for_standalone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    result = doctor(profile="standalone", repo_root=ROOT)
    assert result.ok is True
    # Portable compose is additive — existing profiles unchanged.
    assert get_profile("server").non_root is True


@pytest.mark.skipif(
    os.environ.get("SWARM_PORTABLE_DOCKER") != "1",
    reason="Set SWARM_PORTABLE_DOCKER=1 to run two-container Docker proof",
)
def test_two_container_docker_proof() -> None:
    if shutil.which("docker") is None:
        pytest.skip("docker not available")
    # Build may be heavy; require operator opt-in via env.
    up = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE),
            "up",
            "--build",
            "--abort-on-container-exit",
            "--exit-code-from",
            "worker",
        ],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
    )
    down = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE), "down", "-v"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert up.returncode == 0, up.stdout + up.stderr
    assert down.returncode == 0 or True  # best-effort cleanup
