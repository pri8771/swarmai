"""V2.3 capability packs — extend extension trust model, no new permission engine."""

from __future__ import annotations

import hashlib

from pydantic import Field

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
    def __init__(self, *, require_signature: bool = False) -> None:
        self.require_signature = require_signature
        self._packs: dict[tuple[str, str], CapabilityPackManifest] = {}
        self._grants: dict[tuple[str, str, str], ProjectPackGrant] = {}

    def register(self, manifest: CapabilityPackManifest) -> None:
        if manifest.revoked:
            raise ExtensionAuthzError("pack_revoked")
        if self.require_signature:
            if not manifest.signature:
                raise ExtensionAuthzError("pack_signature_required")
            if manifest.signature != _expected_signature(manifest):
                raise ExtensionAuthzError("pack_signature_invalid")
        elif manifest.signature and manifest.signature != _expected_signature(manifest):
            raise ExtensionAuthzError("pack_signature_invalid")
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
        if pack.signature and pack.signature != _expected_signature(pack):
            raise ExtensionAuthzError("pack_signature_invalid")
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
        return manifest.model_copy(update={"signature": _expected_signature(manifest)})
