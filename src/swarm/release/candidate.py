"""V2.0 CandidateManifest freeze (ART-V20)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now

# Must equal the Alembic head; tests/release/test_schema_revision.py enforces it.
CURRENT_SCHEMA_REVISION = "a23opsplatform0001"


@dataclass
class CandidateManifest:
    candidate_id: str
    source_sha: str
    schema_revision: str
    dependency_lock_digest: str
    runtime_manifest_digest: str
    policy_versions: dict[str, str] = field(default_factory=dict)
    provider_tool_extension_versions: dict[str, str] = field(default_factory=dict)
    artifact_registry_digest: str = ""
    test_protocol_versions: dict[str, str] = field(default_factory=dict)
    eval_protocol_versions: dict[str, str] = field(default_factory=dict)
    frozen_at: str = ""
    invalidated_at: str | None = None
    invalidation_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "source_sha": self.source_sha,
            "schema_revision": self.schema_revision,
            "dependency_lock_digest": self.dependency_lock_digest,
            "runtime_manifest_digest": self.runtime_manifest_digest,
            "policy_versions": dict(self.policy_versions),
            "provider_tool_extension_versions": dict(self.provider_tool_extension_versions),
            "artifact_registry_digest": self.artifact_registry_digest,
            "test_protocol_versions": dict(self.test_protocol_versions),
            "eval_protocol_versions": dict(self.eval_protocol_versions),
            "frozen_at": self.frozen_at,
            "invalidated_at": self.invalidated_at,
            "invalidation_reason": self.invalidation_reason,
        }


def _file_digest(path: Path) -> str:
    if not path.is_file():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CandidateFreezer:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()

    def freeze(
        self,
        *,
        source_sha: str,
        schema_revision: str = "a18site001",
        policy_versions: dict[str, str] | None = None,
    ) -> CandidateManifest:
        lock = self.root / "uv.lock"
        registry = self.root / "docs" / "coordination" / "ARTIFACT_REGISTRY.json"
        manifest = CandidateManifest(
            candidate_id=new_id("cand_"),
            source_sha=source_sha,
            schema_revision=schema_revision,
            dependency_lock_digest=_file_digest(lock),
            runtime_manifest_digest=_file_digest(self.root / "pyproject.toml"),
            policy_versions=policy_versions or {"spend": "zero", "allow_paid": "false"},
            provider_tool_extension_versions={"gateway": "v17", "broker": "v12"},
            artifact_registry_digest=_file_digest(registry),
            test_protocol_versions={"pytest": "8.x", "offline": "1"},
            eval_protocol_versions={"starter": "provisional"},
            frozen_at=utc_now().isoformat(),
        )
        out = self.root / "var" / "release" / f"{manifest.candidate_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
        tracked = self.root / "docs" / "evidence" / "v20" / "candidate_manifest.json"
        tracked.parent.mkdir(parents=True, exist_ok=True)
        tracked.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
        return manifest
