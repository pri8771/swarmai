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
            state = fh.read().rsplit(")", 1)[1].split()[0]
    except (FileNotFoundError, ProcessLookupError):
        # Reaped between kill(0) and the read: a zombie PID 1 just collected.
        return False
    except OSError:
        return True
    return state not in ("Z", "X")


def _wait_pid(root: Path) -> int:
    for _ in range(200):
        pid_file = root / "child.pid"
        if pid_file.exists() and pid_file.read_text().strip():
            return int(pid_file.read_text())
        time.sleep(0.05)
    raise AssertionError("grandchild never started")


def _assert_dead(pid: int) -> None:
    deadline = time.monotonic() + KILL_BOUND_SECONDS
    alive = _alive(pid)
    while alive and time.monotonic() < deadline:
        time.sleep(0.05)
        alive = _alive(pid)
    assert not alive, "grandchild survived the kill bound"


def test_timeout_kills_grandchildren(tmp_path: Path) -> None:
    (tmp_path / "spawn.py").write_text(SPAWNER, encoding="utf-8")
    # Long enough that the grandchild is always spawned before the timeout fires.
    timeout = 4.0
    runner = IsolatedCodeRunner(tmp_path, timeout_seconds=timeout, memory_mb=512)
    started = time.monotonic()
    result = runner.run_python("spawn.py")
    assert result.timed_out and result.killed_group and not result.ok
    assert time.monotonic() - started < timeout + KILL_BOUND_SECONDS
    _assert_dead(_wait_pid(tmp_path))


def test_cancel_kills_group_before_timeout(tmp_path: Path) -> None:
    (tmp_path / "spawn.py").write_text(SPAWNER, encoding="utf-8")
    runner = IsolatedCodeRunner(tmp_path, timeout_seconds=60, memory_mb=512)
    cancel = threading.Event()
    seen: dict[str, float] = {}

    def _cancel_once_grandchild_exists() -> None:
        seen["pid"] = _wait_pid(tmp_path)
        seen["cancel_at"] = time.monotonic()
        cancel.set()

    trigger = threading.Thread(target=_cancel_once_grandchild_exists, daemon=True)
    trigger.start()
    result = runner.run_python("spawn.py", cancel=cancel)
    returned_at = time.monotonic()
    trigger.join(timeout=1)
    assert "cancel_at" in seen, "cancel was never triggered"
    assert result.cancelled and not result.timed_out and result.killed_group
    assert returned_at - seen["cancel_at"] < KILL_BOUND_SECONDS
    _assert_dead(int(seen["pid"]))


def test_normal_run_unchanged(tmp_path: Path) -> None:
    (tmp_path / "ok.py").write_text("print('ok')\n", encoding="utf-8")
    result = IsolatedCodeRunner(tmp_path).run_python("ok.py")
    assert result.ok and result.stdout.strip() == "ok"
    assert not result.cancelled and not result.killed_group


def test_alive_treats_reaped_zombie_as_dead(monkeypatch: pytest.MonkeyPatch) -> None:
    """kill(0) can succeed on a zombie that PID 1 reaps before /proc is read."""
    import builtins

    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    real_open = builtins.open

    def _gone(path, *a, **kw):  # type: ignore[no-untyped-def]
        if str(path).startswith("/proc/"):
            raise FileNotFoundError(path)
        return real_open(path, *a, **kw)

    monkeypatch.setattr(builtins, "open", _gone)
    assert _alive(4_000_000) is False
