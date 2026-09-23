"""FIX-004 hourly runner lock / no-overlap regressions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKIN = ROOT / "scripts" / "hourly" / "checkin.py"


def test_hourly_checkin_manual(tmp_path: Path) -> None:
    state_dir = tmp_path / "hourly"
    env = {
        **os.environ,
        "SWARM_HOURLY_STATE_DIR": str(state_dir),
        "SWARM_HOST_ALIAS": "test-host",
    }
    proc = subprocess.run(
        [sys.executable, str(CHECKIN), "--repo", str(ROOT), "--trigger", "manual"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    state = json.loads((state_dir / "state.json").read_text())
    assert state["manual_checkins"] >= 1
    assert state["invocation_count"] >= 1
    assert not (state_dir / "hourly.lock").exists()


def test_hourly_lock_blocks_overlap(tmp_path: Path) -> None:
    state_dir = tmp_path / "hourly"
    state_dir.mkdir(parents=True)
    lock = state_dir / "hourly.lock"
    lock.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "started_epoch": __import__("time").time(),
                "started_at": "2026-09-20T00:00:00+00:00",
                "host_alias": "test",
            }
        )
        + "\n"
    )
    env = {**os.environ, "SWARM_HOURLY_STATE_DIR": str(state_dir)}
    proc = subprocess.run(
        [sys.executable, str(CHECKIN), "--repo", str(ROOT), "--trigger", "manual"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 1
    assert "busy" in (proc.stderr + proc.stdout).lower()
