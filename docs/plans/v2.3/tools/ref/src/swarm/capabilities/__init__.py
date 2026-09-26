"""V2.3 capability packs — extend extension trust model, no new permission engine.

Two signature modes:

* **keyed** (production): ``CapabilityPackRegistry(trusted_keys=...)``. Signatures
  must be ``hmac-sha256-v1:`` from a trusted publisher (see ``signing.py``);
  unkeyed digests are refused.
* **legacy** (fixtures only, ``trusted_keys=None``): the historical unkeyed
  sha256 digest. It proves integrity, not authorship (F-02) and must not be used
  on operational paths.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from pydantic import Field

from swarm.capabilities.signing import is_keyed_signature, verify_manifest
from swarm.contracts.common import StrictModel, new_id
from swarm.extensions.registry import ExtensionAuthzError

__all__ = [
    "CapabilityPackManifest",
    "CapabilityPackRegistry",
    "ProjectPackGrant",
]


class CapabilityPackManifest(StrictModel):
    pack_id: str
    version: str
    content_digest: str
    procedures: list[str] = Field(default_factory=list)
    adapters: list[str] = Field(default_factory=list)
    schemas: list[str] = Field(default_factory=list)
    prompts: list[str] = Field(default_factory=list)
    capability_declarations: list[str] = Field(default_factory=list)
    signature: str | None = None
    revoked: bool = False
    publisher: str | None = None


class ProjectPackGrant(StrictModel):
    grant_id: str = Field(default_factory=lambda: new_id("pgr_"))
    project_id: str
    pack_id: str
    version: str
    enabled: bool = True
    granted_capabilities: list[str] = Field(default_factory=list)


def _expected_signature(manifest: CapabilityPackManifest) -> str:
    material = (
        f"{manifest.pack_id}|{manifest.version}|{manifest.content_digest}|"
        f"{','.join(sorted(manifest.capability_declarations))}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class CapabilityPackRegistry:
    def __init__(
        self,
        *,
        require_signature: bool = False,
        trusted_keys: Mapping[str, bytes] | None = None,
    ) -> None:
        self.require_signature = require_signature
        self.trusted_keys = dict(trusted_keys) if trusted_keys is not None else None
        self._packs: dict[tuple[str, str], CapabilityPackManifest] = {}
        self._grants: dict[tuple[str, str, str], ProjectPackGrant] = {}

    @property
    def keyed(self) -> bool:
        return self.trusted_keys is not None

    def _check_signature(self, manifest: CapabilityPackManifest) -> None:
        if not manifest.signature:
            if self.require_signature:
                raise ExtensionAuthzError("pack_signature_required")
            return
        if self.trusted_keys is not None:
            verify_manifest(manifest, trusted_keys=self.trusted_keys)
            return
        if is_keyed_signature(manifest.signature):
            raise ExtensionAuthzError("pack_keyed_signature_needs_trusted_keys")
        if manifest.signature != _expected_signature(manifest):
            raise ExtensionAuthzError("pack_signature_invalid")

    def register(self, manifest: CapabilityPackManifest) -> None:
        if manifest.revoked:
            raise ExtensionAuthzError("pack_revoked")
        self._check_signature(manifest)
        self._packs[(manifest.pack_id, manifest.version)] = manifest

    def revoke(self, pack_id: str, version: str) -> None:
        pack = self._packs.get((pack_id, version))
        if pack is None:
            raise ExtensionAuthzError("pack_missing")
        pack.revoked = True

    def verify_trust(self, pack_id: str, version: str) -> CapabilityPackManifest:
        pack = self._packs.get((pack_id, version))
        if pack is None:
            raise ExtensionAuthzError("pack_missing")
        if pack.revoked:
            raise ExtensionAuthzError("pack_revoked")
        self._check_signature(pack)
        return pack

    def grant(self, grant: ProjectPackGrant) -> ProjectPackGrant:
        pack = self.verify_trust(grant.pack_id, grant.version)
        # Cannot widen beyond declarations.
        illegal = set(grant.granted_capabilities) - set(pack.capability_declarations)
        if illegal:
            raise ExtensionAuthzError(f"capability_widen_forbidden:{sorted(illegal)}")
        self._grants[(grant.project_id, grant.pack_id, grant.version)] = grant
        return grant

    def effective(self, project_id: str, pack_id: str, version: str) -> set[str]:
        pack = self.verify_trust(pack_id, version)
        grant = self._grants.get((project_id, pack_id, version))
        if grant is None or not grant.enabled:
            raise ExtensionAuthzError("pack_not_enabled")
        return set(pack.capability_declarations) & set(grant.granted_capabilities)

    @staticmethod
    def sign(manifest: CapabilityPackManifest) -> CapabilityPackManifest:
        """Legacy unkeyed digest (fixtures only). Use signing.sign_manifest for real packs."""
        return manifest.model_copy(update={"signature": _expected_signature(manifest)})
