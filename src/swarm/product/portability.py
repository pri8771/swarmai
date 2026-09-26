"""V2.3 portability export/import — never include secrets or live authority.

Bundle schema 2 (ART-V23-PORTABILITY) adds verifiable history sections:
``history``, ``receipts``, ``approvals``, ``leases`` and ``artifact_digests``, each
with its own digest. Imported approvals and leases are tombstoned: they are kept
for provenance but can never execute. Schema-1 bundles still import unchanged.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, payload_hash, utc_now

FORBIDDEN = ("password", "secret", "token", "api_key", "apikey", "credential", "private_key")
BUNDLE_SCHEMA = "2"
READER_SCHEMA = 2
SECTION_NAMES = ("history", "receipts", "approvals", "leases", "artifact_digests")
ENV_REF = re.compile(r"^env:[A-Z_][A-Z0-9_]*$")
SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[abpr]-[A-Za-z0-9\-]{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{12,}"),
    re.compile(r"(?i)(password|secret|token|api_key)=[^\s&]+"),
)


def _reject_secrets(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            lowered = str(key).lower()
            if any(f in lowered for f in FORBIDDEN) and not isinstance(value, dict | list):
                if value not in (None, "") and not (
                    isinstance(value, str) and ENV_REF.match(value)
                ):
                    raise ValueError(f"secret_in_bundle:{path}.{key}")
            _reject_secrets(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _reject_secrets(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        for pattern in SECRET_VALUE_PATTERNS:
            if pattern.search(obj):
                raise ValueError(f"secret_value_in_bundle:{path}")


def _tombstone(items: list[dict[str, Any]], bundle_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row["original_state"] = row.get("state")
        row["state"] = "tombstoned"
        row["executable"] = False
        row["tombstoned_by_bundle"] = bundle_id
        out.append(row)
    return out


def _remap(items: list[dict[str, Any]], old: str, new: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        if row.get("project_id") == old:
            row["project_id"] = new
        out.append(row)
    return out


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
    schema_version: str = "1"
    sections: dict[str, Any] = field(default_factory=dict)
    section_digests: dict[str, str] = field(default_factory=dict)
    compatibility: dict[str, Any] = field(default_factory=dict)
    remapped_from: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
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
        if self.schema_version != "1":
            out["schema_version"] = self.schema_version
            out["sections"] = dict(self.sections)
            out["section_digests"] = dict(self.section_digests)
            out["compatibility"] = dict(self.compatibility)
        if self.remapped_from is not None:
            out["remapped_from"] = self.remapped_from
        return out


def _digest_body(data: dict[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "project_id": data["project_id"],
        "project_config": data.get("project_config") or {},
        "knowledge_refs": data.get("knowledge_refs") or [],
        "capability_pack_config": data.get("capability_pack_config") or {},
        "policy_refs": data.get("policy_refs") or [],
        "artifact_refs": data.get("artifact_refs") or [],
        "version_manifest": data.get("version_manifest") or {},
    }
    if str(data.get("schema_version", "1")) != "1":
        body["schema_version"] = str(data["schema_version"])
        body["section_digests"] = data.get("section_digests") or {}
        body["compatibility"] = data.get("compatibility") or {}
    return body


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
        history: list[dict[str, Any]] | None = None,
        receipts: list[dict[str, Any]] | None = None,
        approvals: list[dict[str, Any]] | None = None,
        leases: list[dict[str, Any]] | None = None,
        artifact_digests: dict[str, str] | None = None,
    ) -> PortabilityBundle:
        bundle_id = new_id("port_")
        config = dict(project_config)
        packs = dict(capability_pack_config or {})
        sections: dict[str, Any] = {
            "history": list(history or []),
            "receipts": list(receipts or []),
            "approvals": _tombstone(list(approvals or []), bundle_id),
            "leases": _tombstone(list(leases or []), bundle_id),
            "artifact_digests": dict(artifact_digests or {}),
        }
        data: dict[str, Any] = {
            "bundle_id": bundle_id,
            "project_id": project_id,
            "project_config": config,
            "knowledge_refs": list(knowledge_refs or []),
            "capability_pack_config": packs,
            "policy_refs": list(policy_refs or []),
            "artifact_refs": list(artifact_refs or []),
            "version_manifest": dict(version_manifest or {}),
            "schema_version": BUNDLE_SCHEMA,
            "sections": sections,
            "section_digests": {n: payload_hash({n: sections[n]}) for n in SECTION_NAMES},
            "compatibility": {"min_reader": READER_SCHEMA, "bundle_schema": BUNDLE_SCHEMA},
        }
        _reject_secrets(data)
        bundle = PortabilityBundle(
            bundle_id=bundle_id,
            project_id=project_id,
            created_at=utc_now().isoformat(),
            integrity_digest=payload_hash(_digest_body(data)),
            project_config=config,
            knowledge_refs=data["knowledge_refs"],
            capability_pack_config=packs,
            policy_refs=data["policy_refs"],
            artifact_refs=data["artifact_refs"],
            version_manifest=data["version_manifest"],
            schema_version=BUNDLE_SCHEMA,
            sections=sections,
            section_digests=data["section_digests"],
            compatibility=data["compatibility"],
        )
        target = out_dir or Path("var/portability")
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{bundle.bundle_id}.json"
        path.write_text(json.dumps(bundle.to_dict(), indent=2) + "\n", encoding="utf-8")
        return bundle

    def import_bundle(
        self, path: Path, *, target_project_id: str | None = None
    ) -> PortabilityBundle:
        data = json.loads(path.read_text(encoding="utf-8"))
        _reject_secrets(data)
        schema = str(data.get("schema_version", "1"))
        if schema not in {"1", BUNDLE_SCHEMA}:
            raise ValueError(f"bundle_incompatible:schema={schema}")
        compat = data.get("compatibility") or {}
        if int(compat.get("min_reader", 1)) > READER_SCHEMA:
            raise ValueError(f"bundle_incompatible:min_reader={compat.get('min_reader')}")
        expected = data.get("integrity_digest")
        digest = payload_hash(_digest_body(data))
        if expected and expected != digest:
            raise ValueError("bundle_integrity_mismatch")
        sections: dict[str, Any] = dict(data.get("sections") or {})
        if schema != "1":
            for name in SECTION_NAMES:
                empty: Any = {} if name == "artifact_digests" else []
                got = payload_hash({name: sections.get(name, empty)})
                if (data.get("section_digests") or {}).get(name) != got:
                    raise ValueError(f"bundle_section_mismatch:{name}")
            for name in ("approvals", "leases"):
                if any(item.get("executable") for item in sections.get(name, [])):
                    raise ValueError(f"bundle_live_authority:{name}")
        project_id = str(data["project_id"])
        remapped_from: str | None = None
        if target_project_id and target_project_id != project_id:
            remapped_from = project_id
            for name in ("history", "receipts", "approvals", "leases"):
                sections[name] = _remap(list(sections.get(name, [])), project_id, target_project_id)
            project_id = target_project_id
        return PortabilityBundle(
            bundle_id=data["bundle_id"],
            project_id=project_id,
            created_at=data.get("created_at") or utc_now().isoformat(),
            integrity_digest=digest,
            project_config=data.get("project_config") or {},
            knowledge_refs=list(data.get("knowledge_refs") or []),
            capability_pack_config=data.get("capability_pack_config") or {},
            policy_refs=list(data.get("policy_refs") or []),
            artifact_refs=list(data.get("artifact_refs") or []),
            version_manifest=data.get("version_manifest") or {},
            schema_version=schema,
            sections=sections,
            section_digests=dict(data.get("section_digests") or {}),
            compatibility=dict(compat),
            remapped_from=remapped_from,
        )
