"""V2.3 capability packs — extend extension trust model, no new permission engine."""

from __future__ import annotations

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id
from swarm.extensions.registry import ExtensionAuthzError


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


class ProjectPackGrant(StrictModel):
    grant_id: str = Field(default_factory=lambda: new_id("pgr_"))
    project_id: str
    pack_id: str
    version: str
    enabled: bool = True
    granted_capabilities: list[str] = Field(default_factory=list)


class CapabilityPackRegistry:
    def __init__(self) -> None:
        self._packs: dict[tuple[str, str], CapabilityPackManifest] = {}
        self._grants: dict[tuple[str, str, str], ProjectPackGrant] = {}

    def register(self, manifest: CapabilityPackManifest) -> None:
        if manifest.revoked:
            raise ExtensionAuthzError("pack_revoked")
        self._packs[(manifest.pack_id, manifest.version)] = manifest

    def revoke(self, pack_id: str, version: str) -> None:
        pack = self._packs.get((pack_id, version))
        if pack is None:
            raise ExtensionAuthzError("pack_missing")
        pack.revoked = True

    def grant(self, grant: ProjectPackGrant) -> ProjectPackGrant:
        pack = self._packs.get((grant.pack_id, grant.version))
        if pack is None or pack.revoked:
            raise ExtensionAuthzError("pack_unavailable")
        # Cannot widen beyond declarations.
        illegal = set(grant.granted_capabilities) - set(pack.capability_declarations)
        if illegal:
            raise ExtensionAuthzError(f"capability_widen_forbidden:{sorted(illegal)}")
        self._grants[(grant.project_id, grant.pack_id, grant.version)] = grant
        return grant

    def effective(self, project_id: str, pack_id: str, version: str) -> set[str]:
        pack = self._packs.get((pack_id, version))
        grant = self._grants.get((project_id, pack_id, version))
        if pack is None or pack.revoked or grant is None or not grant.enabled:
            raise ExtensionAuthzError("pack_not_enabled")
        return set(pack.capability_declarations) & set(grant.granted_capabilities)
