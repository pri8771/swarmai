"""V2.3 portability export/import — never include secrets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, payload_hash, utc_now

FORBIDDEN = ("password", "secret", "token", "api_key", "apikey", "credential", "private_key")


def _reject_secrets(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            lowered = str(key).lower()
            if any(f in lowered for f in FORBIDDEN):
                if isinstance(value, str) and value and not str(value).startswith("env:"):
                    raise ValueError(f"secret_in_bundle:{path}.{key}")
            _reject_secrets(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _reject_secrets(item, f"{path}[{i}]")


@dataclass
class PortabilityBundle:
    bundle_id: str
    project_id: str
    created_at: str
    integrity_digest: str
    project_config: dict[str, Any] = field(default_factory=dict)
    knowledge_refs: list[str] = field(default_factory=list)
    capability_pack_config: dict[str, Any] = field(default_factory=dict)
    policy_refs: list[str] = field(default_factory=list)
    artifact_refs: list[str] = field(default_factory=list)
    version_manifest: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "integrity_digest": self.integrity_digest,
            "project_config": dict(self.project_config),
            "knowledge_refs": list(self.knowledge_refs),
            "capability_pack_config": dict(self.capability_pack_config),
            "policy_refs": list(self.policy_refs),
            "artifact_refs": list(self.artifact_refs),
            "version_manifest": dict(self.version_manifest),
        }


class PortabilityService:
    def export_project(
        self,
        *,
        project_id: str,
        project_config: dict[str, Any],
        knowledge_refs: list[str] | None = None,
        capability_pack_config: dict[str, Any] | None = None,
        policy_refs: list[str] | None = None,
        artifact_refs: list[str] | None = None,
        version_manifest: dict[str, str] | None = None,
        out_dir: Path | None = None,
    ) -> PortabilityBundle:
        config = dict(project_config)
        packs = dict(capability_pack_config or {})
        _reject_secrets(config)
        _reject_secrets(packs)
        body = {
            "project_id": project_id,
            "project_config": config,
            "knowledge_refs": list(knowledge_refs or []),
            "capability_pack_config": packs,
            "policy_refs": list(policy_refs or []),
            "artifact_refs": list(artifact_refs or []),
            "version_manifest": dict(version_manifest or {}),
        }
        digest = payload_hash(body)
        bundle = PortabilityBundle(
            bundle_id=new_id("port_"),
            project_id=project_id,
            created_at=utc_now().isoformat(),
            integrity_digest=digest,
            project_config=config,
            knowledge_refs=list(knowledge_refs or []),
            capability_pack_config=packs,
            policy_refs=list(policy_refs or []),
            artifact_refs=list(artifact_refs or []),
            version_manifest=dict(version_manifest or {}),
        )
        target = out_dir or Path("var/portability")
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{bundle.bundle_id}.json"
        path.write_text(json.dumps(bundle.to_dict(), indent=2) + "\n", encoding="utf-8")
        return bundle

    def import_bundle(self, path: Path) -> PortabilityBundle:
        data = json.loads(path.read_text(encoding="utf-8"))
        _reject_secrets(data)
        expected = data.get("integrity_digest")
        body = {
            "project_id": data["project_id"],
            "project_config": data.get("project_config") or {},
            "knowledge_refs": data.get("knowledge_refs") or [],
            "capability_pack_config": data.get("capability_pack_config") or {},
            "policy_refs": data.get("policy_refs") or [],
            "artifact_refs": data.get("artifact_refs") or [],
            "version_manifest": data.get("version_manifest") or {},
        }
        digest = payload_hash(body)
        if expected and expected != digest:
            raise ValueError("bundle_integrity_mismatch")
        return PortabilityBundle(
            bundle_id=data["bundle_id"],
            project_id=data["project_id"],
            created_at=data.get("created_at") or utc_now().isoformat(),
            integrity_digest=digest,
            project_config=body["project_config"],
            knowledge_refs=list(body["knowledge_refs"]),
            capability_pack_config=body["capability_pack_config"],
            policy_refs=list(body["policy_refs"]),
            artifact_refs=list(body["artifact_refs"]),
            version_manifest=body["version_manifest"],
        )
