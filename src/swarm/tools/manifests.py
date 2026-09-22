"""Strict, versioned built-in integration definitions and canonical identity."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from swarm.contracts.actions import AdapterManifest

MANIFEST_DIR = Path(__file__).resolve().parents[3] / "config" / "integrations"
_SECRET = re.compile(
    r"(?i)(sk-[a-z0-9]{8,}|ghp_[a-z0-9]{8,}|AKIA[0-9A-Z]{12,}|-----BEGIN|password\s*=)"
)


def _guard(value: Any) -> None:
    if isinstance(value, str) and _SECRET.search(value):
        raise ValueError("manifest_contains_secret_like_value")
    if isinstance(value, dict):
        for key, item in value.items():
            _guard(key)
            _guard(item)
    elif isinstance(value, list):
        for item in value:
            _guard(item)


def load_manifest(path: Path) -> AdapterManifest:
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    _guard(payload)
    manifest = AdapterManifest.model_validate(payload)
    if path.name != f"{manifest.integration_id}@{manifest.integration_version}.json":
        raise ValueError("manifest_name_mismatch")
    return manifest


def manifest_digest(manifest: AdapterManifest) -> str:
    payload = manifest.model_dump(mode="json")
    _guard(payload)
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_all(directory: Path) -> list[AdapterManifest]:
    directory = Path(directory)
    manifests = []
    seen = set()
    for path in sorted(directory.rglob("*.json")):
        manifest = load_manifest(path)
        identity = (manifest.integration_id, manifest.integration_version)
        if identity in seen:
            raise ValueError("duplicate_manifest")
        seen.add(identity)
        manifests.append(manifest)
    return manifests
