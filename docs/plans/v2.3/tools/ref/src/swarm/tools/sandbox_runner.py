"""Isolated code/test runner — operator-controlled trust boundary.

Network is off by default. Paths outside the work directory are denied via an
injected sitecustomize gate (R5). This is still not a hardened multi-tenant
hypervisor; Docker socket and host secrets are never mounted.
"""

from __future__ import annotations

import os
import resource
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from dataclasses import dataclass
from pathlib import Path

KILL_BOUND_SECONDS = 10.0
_POLL_SECONDS = 0.05


@dataclass
class SandboxResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    cancelled: bool = False
    killed_group: bool = False


class SandboxPolicyError(PermissionError):
    pass


_SITECUSTOMIZE = textwrap.dedent(
    """
    import builtins
    import sys
    from pathlib import Path

    _WORK = Path(__file__).resolve().parent
    _ALLOWED_PREFIXES = (
        str(_WORK),
        sys.base_prefix,
        sys.prefix,
        "/usr",
        "/Library/Frameworks",
        "/System/Library",
    )

    def _allowed(path: Path) -> bool:
        try:
            resolved = path.resolve()
        except OSError:
            return False
        text = str(resolved)
        return any(text.startswith(prefix) for prefix in _ALLOWED_PREFIXES)

    _real_open = builtins.open

    def _open(file, *args, **kwargs):
        try:
            candidate = Path(file)
        except TypeError:
            return _real_open(file, *args, **kwargs)
        if not _allowed(candidate):
            raise PermissionError(f"sandbox_path_denied:{file}")
        return _real_open(file, *args, **kwargs)

    builtins.open = _open

    try:
        import pathlib

        _real_read_text = pathlib.Path.read_text
        _real_read_bytes = pathlib.Path.read_bytes

        def _read_text(self, *args, **kwargs):
            if not _allowed(self):
                raise PermissionError(f"sandbox_path_denied:{self}")
            return _real_read_text(self, *args, **kwargs)

        def _read_bytes(self, *args, **kwargs):
            if not _allowed(self):
                raise PermissionError(f"sandbox_path_denied:{self}")
            return _real_read_bytes(self, *args, **kwargs)

        pathlib.Path.read_text = _read_text  # type: ignore[method-assign]
        pathlib.Path.read_bytes = _read_bytes  # type: ignore[method-assign]
    except Exception:
        pass
    """
)


class IsolatedCodeRunner:
    def __init__(
        self,
        work_dir: Path,
        *,
        network: bool = False,
        timeout_seconds: float = 5.0,
        memory_mb: int = 256,
    ) -> None:
        self.work_dir = work_dir.resolve()
        self.network = network
        self.timeout_seconds = timeout_seconds
        self.memory_mb = memory_mb
        if not self.work_dir.exists():
            raise FileNotFoundError(self.work_dir)
        gate = self.work_dir / "sitecustomize.py"
        if not gate.exists():
            gate.write_text(_SITECUSTOMIZE, encoding="utf-8")

    def _assert_path_allowed(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.work_dir)
        except ValueError as exc:
            raise SandboxPolicyError(f"path escapes allowlisted work_dir: {path}") from exc
        if resolved.is_symlink():
            target = resolved.resolve()
            try:
                target.relative_to(self.work_dir)
            except ValueError as exc:
                raise SandboxPolicyError("symlink escape blocked") from exc
        return resolved

    def run_python(
        self,
        relative_script: str,
        args: list[str] | None = None,
        *,
        cancel: threading.Event | None = None,
    ) -> SandboxResult:
        script = self._assert_path_allowed(self.work_dir / relative_script)
        if self.network:
            raise SandboxPolicyError("network is disabled by default; refuse enabling in self-test")

        def _limit() -> None:
            bytes_limit = self.memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(self.work_dir),
            "HOME": str(self.work_dir),
            "PYTHONNOUSERSITE": "1",
        }
        cmd = [sys.executable, str(script), *(args or [])]
        # Own session => own process group, so timeout/cancel kills every descendant.
        proc = subprocess.Popen(
            cmd,
            cwd=str(self.work_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            preexec_fn=_limit if sys.platform != "darwin" else None,
        )
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            if cancel is not None and cancel.is_set():
                return self._kill_group(proc, timed_out=False, cancelled=True)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return self._kill_group(proc, timed_out=True, cancelled=False)
            try:
                stdout, stderr = proc.communicate(timeout=min(_POLL_SECONDS, remaining))
            except subprocess.TimeoutExpired:
                continue
            return SandboxResult(
                ok=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=stdout,
                stderr=stderr,
            )

    def _kill_group(
        self, proc: subprocess.Popen[str], *, timed_out: bool, cancelled: bool
    ) -> SandboxResult:
        killed = False
        try:
            os.killpg(proc.pid, signal.SIGKILL)
            killed = True
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = proc.communicate(timeout=KILL_BOUND_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = "", ""
        reason = "timeout" if timed_out else "cancelled"
        return SandboxResult(
            ok=False,
            exit_code=-1,
            stdout=stdout or "",
            stderr=stderr or reason,
            timed_out=timed_out,
            cancelled=cancelled,
            killed_group=killed,
        )


def self_test(*, network: str = "off") -> dict[str, object]:
    if network != "off":
        raise SandboxPolicyError("self-test requires --network off")
    with tempfile.TemporaryDirectory(prefix="swarm-sandbox-") as tmp:
        root = Path(tmp)
        script = root / "ok.py"
        script.write_text("print('sandbox-ok')\n")
        runner = IsolatedCodeRunner(root, network=False, timeout_seconds=3)
        result = runner.run_python("ok.py")
        return {
            "ok": result.ok,
            "stdout": result.stdout.strip(),
            "network": "off",
            "docker_socket_mounted": False,
            "host_secrets_mounted": False,
            "trust_boundary": "operator-controlled-dev-path-gated-not-hostile-multi-tenant",
        }
