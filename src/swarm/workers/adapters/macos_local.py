"""Optional macOS-local adapter — not the default worker connector path.

Mac-only extract fixtures and privacy locality live here. The generic connector
registers this adapter only when explicitly enabled.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAC_CAPABILITIES = ("mac.local.extract", "extract", "chat", "code.read")
MAC_PRIVACY = ("mac_local", "local")
MAC_LOCALITY = ("mac_local", "local", "host_local")


@dataclass(frozen=True)
class MacLocalWork:
    """Result of Mac-only local work (file must not live on the server)."""

    path: str
    email_count: int
    artifact_sha256: str
    emails: tuple[str, ...]
    placement: str = "mac_local"
    host_role: str = "mac_connector"
    runtime: str = "mac_connector_native"
    spend_usd: float = 0.0

    def required_checks(self) -> dict[str, Any]:
        return {
            "email_count": self.email_count,
            "artifact_sha256": self.artifact_sha256,
            "placement": self.placement,
            "host_role": self.host_role,
            "runtime": self.runtime,
        }

    def produced(self, *, worker_id: str, run_id: str) -> dict[str, Any]:
        return {
            "checks": self.required_checks(),
            "worker_id": worker_id,
            "mac_local_path": self.path,
            "emails": list(self.emails),
            "fixture_run_id": run_id,
            "spend_usd": self.spend_usd,
        }


def perform_mac_local_extract(path: Path) -> MacLocalWork:
    """Read a Mac-local fixture and produce protected checks. No model calls."""
    payload = path.read_text(encoding="utf-8")
    emails = tuple(
        sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", payload)))
    )
    digest = hashlib.sha256(
        (path.resolve().as_posix() + "\n" + "|".join(emails) + "\n" + payload).encode("utf-8")
    ).hexdigest()
    return MacLocalWork(
        path=str(path.resolve()),
        email_count=len(emails),
        artifact_sha256=digest,
        emails=emails,
    )


def write_mac_local_fixture(directory: Path, *, run_id: str) -> Path:
    """Create a Mac-local fixture under a *bounded* workspace directory."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"th03-mac-local-{run_id}.txt"
    path.write_text(
        "TH-03 Mac-local fixture for connector adapter tests.\n"
        "Contact mac-agent@example.com and ops@example.com.\n"
        f"run_id={run_id}\n"
        "placement=mac_local\n",
        encoding="utf-8",
    )
    return path


def macos_local_executor(claim: dict[str, Any], workspace_dir: Path) -> dict[str, Any] | None:
    """Execute mac_local extract when scoped; return None if not applicable."""
    import uuid

    task = claim.get("task") or {}
    scopes = set(task.get("scopes") or [])
    caps = set(task.get("required_capabilities") or [])
    if "mac_local" not in scopes and "mac.local.extract" not in caps:
        return None
    run_id = str(task.get("id") or uuid.uuid4().hex[:12])
    path = write_mac_local_fixture(workspace_dir, run_id=run_id)
    work = perform_mac_local_extract(path)
    return {
        "status": "completed",
        "checks": work.required_checks(),
        "artifact_manifest": {
            "placement": "mac_local",
            "path": work.path,
            "sha256": work.artifact_sha256,
            "email_count": work.email_count,
        },
        "usage": {"spend_usd": 0.0, "model_calls": 0},
        "summary": f"mac_local extract emails={work.email_count}",
    }
