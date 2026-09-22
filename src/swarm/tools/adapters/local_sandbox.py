"""Local/sandbox adapter — filesystem-bounded, no network."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, AdapterManifest
from swarm.tools.adapters.base import AdapterDeniedError

DEFAULT_COMMAND_ALLOWLIST = (
    ("uv", "run", "pytest"),
    ("python", "-m", "pytest"),
    ("git", "diff"),
    ("git", "status"),
    ("git", "rev-parse"),
)


class LocalSandboxAdapter:
    def __init__(
        self,
        manifest: AdapterManifest,
        *,
        root: Path,
        command_allowlist: list[list[str]] | None = None,
    ) -> None:
        if manifest.adapter_class != "local_sandbox":
            raise ValueError("adapter_class_mismatch")
        self.manifest = AdapterManifest.model_validate(manifest.model_dump())
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        prefixes = command_allowlist if command_allowlist is not None else DEFAULT_COMMAND_ALLOWLIST
        self.command_allowlist = tuple(tuple(prefix) for prefix in prefixes)

    def normalize(self, request: dict[str, Any]) -> ActionEnvelope:
        operation = str(request.get("operation", "fs.write_text"))
        declaration = self.manifest.operations.get(operation)
        if declaration is None:
            raise AdapterDeniedError("unknown_operation")
        payload: dict[str, Any]
        if operation == "fs.write_text":
            payload = {
                "path": str(request.get("path", "out.txt")),
                "text": str(request.get("text", "")),
            }
            dest = str(request.get("destination") or f"file://{self.root / payload['path']}")
        elif operation == "proc.run":
            argv = request.get("argv")
            if (
                not isinstance(argv, list)
                or not argv
                or not all(isinstance(item, str) for item in argv)
            ):
                raise AdapterDeniedError("invalid_argv")
            timeout_s = request.get("timeout_s", 30)
            if (
                isinstance(timeout_s, bool)
                or not isinstance(timeout_s, (int, float))
                or timeout_s <= 0
            ):
                raise AdapterDeniedError("invalid_timeout")
            payload = {"argv": list(argv), "timeout_s": timeout_s}
            dest = str(request.get("destination") or f"proc://{argv[0]}")
        env = ActionEnvelope(
            project_id=str(request["project_id"]),
            actor=str(request.get("actor", "worker")),
            integration_id=self.manifest.integration_id,
            integration_version=self.manifest.integration_version,
            operation=operation,
            destination=dest,
            normalized_payload=payload,
            requested_scopes=list(declaration.scopes),
            side_effect_class=declaration.side_effect_class,
            risk_class=declaration.risk_class,
            lease_generation=request.get("lease_generation"),
            cancellation_generation=request.get("cancellation_generation"),
            policy_version=str(request.get("policy_version", "v17-policy-1")),
            mission_id=request.get("mission_id"),
            task_id=request.get("task_id"),
            attempt_id=request.get("attempt_id"),
            approval_id=request.get("approval_id"),
        )
        return env.ensure_hashes()

    def validate(self, envelope: ActionEnvelope) -> None:
        if envelope.integration_id != self.manifest.integration_id:
            raise ValueError("integration_mismatch")
        if envelope.operation == "fs.write_text":
            self._path_under_root(str(envelope.normalized_payload.get("path", "out.txt")))
        elif envelope.operation == "proc.run":
            self._command_payload(envelope)
        else:
            raise AdapterDeniedError("unknown_operation")

    def observe_pre_state(self, envelope: ActionEnvelope) -> dict[str, Any]:
        if envelope.operation == "fs.write_text":
            path = self._path_under_root(str(envelope.normalized_payload.get("path", "out.txt")))
            return {"sha256": self._file_digest(path)}
        if envelope.operation == "proc.run":
            argv, timeout_s = self._command_payload(envelope)
            return {"argv": argv, "cwd": str(self.root), "timeout_s": timeout_s}
        raise AdapterDeniedError("unknown_operation")

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        if envelope.operation == "fs.write_text":
            path = self._path_under_root(str(envelope.normalized_payload.get("path", "out.txt")))
            path.parent.mkdir(parents=True, exist_ok=True)
            path = self._path_under_root(str(envelope.normalized_payload.get("path", "out.txt")))
            text = str(envelope.normalized_payload.get("text", ""))
            path.write_text(text, encoding="utf-8")
            return {"outcome": "succeeded", "path": str(path)}
        if envelope.operation == "proc.run":
            argv, timeout_s = self._command_payload(envelope)
            completed = subprocess.run(
                argv,
                cwd=self.root,
                shell=False,
                capture_output=True,
                check=False,
                timeout=timeout_s,
            )
            return {
                "outcome": "succeeded",
                "exit_code": completed.returncode,
                "stdout_sha256": self._bytes_digest(completed.stdout),
                "stderr_sha256": self._bytes_digest(completed.stderr),
                "stdout_tail": completed.stdout[-4096:].decode("utf-8", errors="replace"),
                "stderr_tail": completed.stderr[-4096:].decode("utf-8", errors="replace"),
            }
        raise AdapterDeniedError("unknown_operation")

    def observe_post_state(
        self, envelope: ActionEnvelope, execution_result: dict[str, Any]
    ) -> dict[str, Any]:
        if envelope.operation == "fs.write_text":
            path = self._path_under_root(str(envelope.normalized_payload.get("path", "out.txt")))
            if not path.exists():
                return {"sha256": None, "bytes": 0}
            return {"sha256": self._file_digest(path), "bytes": path.stat().st_size}
        if envelope.operation == "proc.run":
            return {"result": execution_result}
        raise AdapterDeniedError("unknown_operation")

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]:
        if envelope.operation == "fs.write_text":
            path = self._path_under_root(str(envelope.normalized_payload.get("path", "out.txt")))
            if path.exists():
                return {"state": "succeeded", "external_id": str(path)}
            return {"state": "failed", "reason": "file_missing"}
        return {"state": "unknown", "reason": "process_outcome_not_observable"}

    def _path_under_root(self, raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute() or ".." in path.parts:
            raise AdapterDeniedError("path_outside_root")
        candidate = (self.root / path).resolve(strict=False)
        if not candidate.is_relative_to(self.root):
            raise AdapterDeniedError("path_outside_root")
        return candidate

    def _command_payload(self, envelope: ActionEnvelope) -> tuple[list[str], float]:
        argv = envelope.normalized_payload.get("argv")
        timeout_s = envelope.normalized_payload.get("timeout_s")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(item, str) for item in argv)
        ):
            raise AdapterDeniedError("invalid_argv")
        if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)) or timeout_s <= 0:
            raise AdapterDeniedError("invalid_timeout")
        if not any(tuple(argv[: len(prefix)]) == prefix for prefix in self.command_allowlist):
            raise AdapterDeniedError("command_not_allowlisted")
        return list(argv), float(timeout_s)

    @staticmethod
    def _bytes_digest(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    def _file_digest(self, path: Path) -> str | None:
        return self._bytes_digest(path.read_bytes()) if path.exists() else None
