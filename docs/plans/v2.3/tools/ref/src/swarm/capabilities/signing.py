"""Keyed capability-pack signatures (F-02): HMAC-SHA256 with per-publisher keys.

Keys never live in the repo. ``trusted_keys_from_env`` reads
``SWARM_PACK_TRUSTED_PUBLISHERS=pub_a,pub_b`` and ``SWARM_PACK_KEY_PUB_A=<secret>``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING

from swarm.extensions.registry import ExtensionAuthzError

if TYPE_CHECKING:
    from swarm.capabilities import CapabilityPackManifest

SIGNATURE_SCHEME = "hmac-sha256-v1"


class PackSigningError(ExtensionAuthzError):
    pass


def canonical_material(manifest: CapabilityPackManifest) -> bytes:
    body = {
        "pack_id": manifest.pack_id,
        "version": manifest.version,
        "content_digest": manifest.content_digest,
        "publisher": manifest.publisher,
        "capability_declarations": sorted(manifest.capability_declarations),
        "procedures": sorted(manifest.procedures),
        "adapters": sorted(manifest.adapters),
        "schemas": sorted(manifest.schemas),
        "prompts": sorted(manifest.prompts),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def is_keyed_signature(signature: str | None) -> bool:
    return bool(signature) and str(signature).startswith(SIGNATURE_SCHEME + ":")


def sign_manifest(manifest: CapabilityPackManifest, *, key: bytes) -> CapabilityPackManifest:
    if not manifest.publisher:
        raise PackSigningError("pack_publisher_required")
    if not key:
        raise PackSigningError("pack_signing_key_empty")
    digest = hmac.new(key, canonical_material(manifest), hashlib.sha256).hexdigest()
    return manifest.model_copy(update={"signature": f"{SIGNATURE_SCHEME}:{digest}"})


def verify_manifest(
    manifest: CapabilityPackManifest, *, trusted_keys: Mapping[str, bytes]
) -> None:
    if not is_keyed_signature(manifest.signature):
        raise PackSigningError("pack_signature_unkeyed")
    if not manifest.publisher or manifest.publisher not in trusted_keys:
        raise PackSigningError("pack_publisher_untrusted")
    expected = sign_manifest(manifest, key=trusted_keys[manifest.publisher]).signature
    if not hmac.compare_digest(str(manifest.signature), str(expected)):
        raise PackSigningError("pack_signature_invalid")


def _env_key_name(publisher: str) -> str:
    return "SWARM_PACK_KEY_" + re.sub(r"[^A-Za-z0-9]", "_", publisher).upper()


def trusted_keys_from_env(env: Mapping[str, str] | None = None) -> dict[str, bytes]:
    source = os.environ if env is None else env
    out: dict[str, bytes] = {}
    for raw in source.get("SWARM_PACK_TRUSTED_PUBLISHERS", "").split(","):
        publisher = raw.strip()
        if not publisher:
            continue
        key = source.get(_env_key_name(publisher), "")
        if key:
            out[publisher] = key.encode("utf-8")
    return out
