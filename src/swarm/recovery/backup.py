"""Backup manifest creation — secrets names only (ART-V18)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, payload_hash, utc_now

FORBIDDEN_SECRET_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "private_key",
        "credential",
    }
)


@dataclass
class BackupManifest:
    backup_id: str
    source_site_id: str
    source_epoch: int
    source_commit_sha: str
    schema_revision: str
    created_at: str
    integrity_digest: str
    secret_refs: list[str] = field(default_factory=list)
    included_state_classes: list[str] = field(default_factory=list)
    excluded_state_classes: list[str] = field(default_factory=list)
    migration_heads: list[str] = field(default_factory=list)
    config_manifest_digest: str = ""
    database_artifact_digest: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "source_site_id": self.source_site_id,
            "source_epoch": self.source_epoch,
            "source_commit_sha": self.source_commit_sha,
            "schema_revision": self.schema_revision,
            "created_at": self.created_at,
            "integrity_digest": self.integrity_digest,
            "secret_refs": list(self.secret_refs),
            "included_state_classes": list(self.included_state_classes),
            "excluded_state_classes": list(self.excluded_state_classes),
            "migration_heads": list(self.migration_heads),
            "config_manifest_digest": self.config_manifest_digest,
            "database_artifact_digest": self.database_artifact_digest,
            "extra": dict(self.extra),
        }


def _assert_no_secret_values(payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        lowered = key.lower()
        if any(tok in lowered for tok in FORBIDDEN_SECRET_KEYS):
            if isinstance(value, str) and value and not value.startswith("env:"):
                raise ValueError(f"secret_value_forbidden:{key}")
        if isinstance(value, dict):
            _assert_no_secret_values(value)


def _secret_ref_is_name(ref: str) -> bool:
    if ref.startswith("sk-"):
        return False
    return ref.replace("_", "").isalnum()


class BackupService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("var/recovery/backups")
        self.root.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        *,
        site_id: str,
        epoch: int,
        commit_sha: str,
        schema_revision: str,
        secret_ref_names: list[str] | None = None,
        migration_heads: list[str] | None = None,
        state_snapshot: dict[str, Any] | None = None,
    ) -> BackupManifest:
        snapshot = dict(state_snapshot or {})
        _assert_no_secret_values(snapshot)
        refs = list(secret_ref_names or [])
        for ref in refs:
            if not _secret_ref_is_name(ref):
                raise ValueError(f"secret_ref_must_be_name:{ref}")
        body = {
            "site_id": site_id,
            "epoch": epoch,
            "commit_sha": commit_sha,
            "schema_revision": schema_revision,
            "snapshot": snapshot,
            "secret_refs": refs,
        }
        digest = payload_hash(body)
        manifest = BackupManifest(
            backup_id=new_id("bak_"),
            source_site_id=site_id,
            source_epoch=epoch,
            source_commit_sha=commit_sha,
            schema_revision=schema_revision,
            created_at=utc_now().isoformat(),
            integrity_digest=digest,
            secret_refs=refs,
            included_state_classes=["missions", "leases", "effects", "knowledge"],
            excluded_state_classes=["secrets", "credentials"],
            migration_heads=list(migration_heads or []),
            config_manifest_digest=payload_hash({"schema_revision": schema_revision}),
            database_artifact_digest=digest,
            extra={"snapshot_keys": sorted(snapshot.keys())},
        )
        path = self.root / f"{manifest.backup_id}.json"
        path.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
        return manifest

    def load(self, backup_id: str) -> BackupManifest:
        path = self.root / f"{backup_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        fields = BackupManifest.__dataclass_fields__
        return BackupManifest(**{k: data[k] for k in fields if k in data})
