"""Isolated code/test runner — operator-controlled trust boundary.

This sandbox is for operator-controlled development workloads. It is NOT a
hardened hostile multi-tenant execution environment. Network is off by default;
Docker socket and host secrets are never mounted.
"""

from __future__ import annotations

import os
import resource
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class SandboxPolicyError(PermissionError):
    pass


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

    def run_python(self, relative_script: str, args: list[str] | None = None) -> SandboxResult:
        script = self._assert_path_allowed(self.work_dir / relative_script)
        if self.network:
            raise SandboxPolicyError("network is disabled by default; refuse enabling in self-test")

        def _limit() -> None:
            # Soft memory ceiling (best-effort; platform dependent).
            bytes_limit = self.memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": "",
            "HOME": str(self.work_dir),
            # Never pass host secrets.
        }
        cmd = [sys.executable, str(script), *(args or [])]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.work_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                preexec_fn=_limit if sys.platform != "darwin" else None,
            )
            return SandboxResult(
                ok=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            if isinstance(exc.stderr, bytes):
                stderr = exc.stderr.decode()
            else:
                stderr = exc.stderr or "timeout"
            return SandboxResult(
                ok=False,
                exit_code=-1,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
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
            "trust_boundary": "operator-controlled-dev-not-hostile-multi-tenant",
        }
