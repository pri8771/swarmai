"""SW-W1-S13 / V20-E08: timeout and cancel kill the whole sandbox process group within bound."""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import pytest

from swarm.tools.sandbox_runner import KILL_BOUND_SECONDS, IsolatedCodeRunner

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups")

SPAWNER = """
import subprocess, sys, time
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
with open("child.pid", "w") as fh:
    fh.write(str(child.pid))
print("spawned", flush=True)
time.sleep(120)
"""


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as fh:
            return fh.read().split()[2] != "Z"
    except OSError:
        return True


def _wait_pid(root: Path) -> int:
    for _ in range(200):
        pid_file = root / "child.pid"
        if pid_file.exists() and pid_file.read_text().strip():
            return int(pid_file.read_text())
        time.sleep(0.05)
    raise AssertionError("grandchild never started")


def _assert_dead(pid: int) -> None:
    deadline = time.monotonic() + KILL_BOUND_SECONDS
    while time.monotonic() < deadline and _alive(pid):
        time.sleep(0.05)
    assert not _alive(pid), "grandchild survived the kill bound"


def test_timeout_kills_grandchildren(tmp_path: Path) -> None:
    (tmp_path / "spawn.py").write_text(SPAWNER, encoding="utf-8")
    runner = IsolatedCodeRunner(tmp_path, timeout_seconds=1.5, memory_mb=512)
    started = time.monotonic()
    result = runner.run_python("spawn.py")
    assert result.timed_out and result.killed_group and not result.ok
    assert time.monotonic() - started < 1.5 + KILL_BOUND_SECONDS
    _assert_dead(_wait_pid(tmp_path))


def test_cancel_kills_group_before_timeout(tmp_path: Path) -> None:
    (tmp_path / "spawn.py").write_text(SPAWNER, encoding="utf-8")
    runner = IsolatedCodeRunner(tmp_path, timeout_seconds=60, memory_mb=512)
    cancel = threading.Event()
    threading.Timer(1.0, cancel.set).start()
    started = time.monotonic()
    result = runner.run_python("spawn.py", cancel=cancel)
    assert result.cancelled and not result.timed_out and result.killed_group
    assert time.monotonic() - started < 1.0 + KILL_BOUND_SECONDS
    _assert_dead(_wait_pid(tmp_path))


def test_normal_run_unchanged(tmp_path: Path) -> None:
    (tmp_path / "ok.py").write_text("print('ok')\n", encoding="utf-8")
    result = IsolatedCodeRunner(tmp_path).run_python("ok.py")
    assert result.ok and result.stdout.strip() == "ok"
    assert not result.cancelled and not result.killed_group
