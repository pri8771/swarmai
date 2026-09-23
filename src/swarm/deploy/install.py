"""V1.9 clean install / upgrade / rollback orchestration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, payload_hash, utc_now

SECRET_KEY_FRAGMENTS = ("password", "secret", "token", "api_key", "apikey", "credential")


@dataclass
class InstallPlan:
    plan_id: str
    mode: str  # clean|upgrade|rollback
    from_revision: str | None
    to_revision: str
    steps: list[str] = field(default_factory=list)
    backup_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "mode": self.mode,
            "from_revision": self.from_revision,
            "to_revision": self.to_revision,
            "steps": list(self.steps),
            "backup_id": self.backup_id,
        }


@dataclass
class SupportBundle:
    bundle_id: str
    created_at: str
    digest: str
    files: list[str]
    redacted_keys: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "created_at": self.created_at,
            "digest": self.digest,
            "files": list(self.files),
            "redacted_keys": list(self.redacted_keys),
        }


class InstallOrchestrator:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()

    def clean_install_plan(self, *, to_revision: str = "head") -> InstallPlan:
        return InstallPlan(
            plan_id=new_id("inst_"),
            mode="clean",
            from_revision=None,
            to_revision=to_revision,
            steps=[
                "validate_env",
                "alembic_upgrade_head",
                "release_install_check",
                "release_harden",
            ],
        )

    def upgrade_plan(self, *, from_revision: str, to_revision: str = "head") -> InstallPlan:
        return InstallPlan(
            plan_id=new_id("upg_"),
            mode="upgrade",
            from_revision=from_revision,
            to_revision=to_revision,
            steps=["preflight", "backup_before_upgrade", "alembic_upgrade", "verify"],
            backup_id=new_id("bak_"),
        )

    def rollback_plan(self, *, from_revision: str, to_revision: str) -> InstallPlan:
        return InstallPlan(
            plan_id=new_id("rb_"),
            mode="rollback",
            from_revision=from_revision,
            to_revision=to_revision,
            steps=["validate_backup", "restore_backup", "alembic_downgrade_target", "verify"],
            backup_id=new_id("bak_"),
        )

    def execute_plan_dry_run(self, plan: InstallPlan) -> dict[str, Any]:
        return {"status": "dry_run_ok", "plan": plan.to_dict(), "applied": False}

    def run_alembic(self, *args: str) -> int:
        proc = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=str(self.root),
            check=False,
        )
        return int(proc.returncode)

    def support_bundle(self, out_dir: Path | None = None) -> SupportBundle:
        target = out_dir or (self.root / "var" / "support")
        target.mkdir(parents=True, exist_ok=True)
        redacted: list[str] = []
        payload: dict[str, Any] = {
            "python": sys.version.split()[0],
            "cwd": str(self.root),
            "env_names": [],
        }
        for key in sorted(os.environ):
            if any(frag in key.lower() for frag in SECRET_KEY_FRAGMENTS):
                redacted.append(key)
                payload["env_names"].append(key)
            elif key.startswith("SWARM_") or key.startswith("OLLAMA_"):
                payload["env_names"].append(key)
        body = json.dumps(payload, sort_keys=True)
        digest = payload_hash(payload)
        path = target / f"support_{digest[:12]}.json"
        path.write_text(body + "\n", encoding="utf-8")
        lowered = body.lower()
        for frag in ("sk-", "bearer ", "password="):
            if frag in lowered:
                raise ValueError(f"support_bundle_contains_secret_pattern:{frag}")
        return SupportBundle(
            bundle_id=new_id("sup_"),
            created_at=utc_now().isoformat(),
            digest=digest,
            files=[str(path)],
            redacted_keys=redacted,
        )
