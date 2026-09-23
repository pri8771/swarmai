"""Extension registry with fail-closed project grants."""

from __future__ import annotations

from typing import Any

from swarm.extensions.contracts import ExtensionManifest, ProjectExtensionGrant


class ExtensionAuthzError(PermissionError):
    pass


class ExtensionRegistry:
    def __init__(self) -> None:
        self._manifests: dict[tuple[str, str], ExtensionManifest] = {}
        self._grants: dict[tuple[str, str, str], ProjectExtensionGrant] = {}

    def register(self, manifest: ExtensionManifest) -> None:
        self._manifests[(manifest.extension_id, manifest.version)] = manifest

    def grant(self, grant: ProjectExtensionGrant) -> ProjectExtensionGrant:
        key = (grant.project_id, grant.extension_id, grant.version)
        if (grant.extension_id, grant.version) not in self._manifests:
            raise ExtensionAuthzError("extension_not_registered")
        self._grants[key] = grant
        return grant

    def effective_scopes(
        self, project_id: str, extension_id: str, version: str
    ) -> dict[str, set[str]]:
        manifest = self._manifests.get((extension_id, version))
        grant = self._grants.get((project_id, extension_id, version))
        if manifest is None:
            raise ExtensionAuthzError("extension_not_registered")
        if grant is None or not grant.enabled or grant.state != "enabled":
            raise ExtensionAuthzError("extension_not_granted")
        return {
            "capabilities": set(manifest.declared_capabilities)
            & set(grant.granted_capabilities),
            "tools": set(manifest.tool_operations) & set(grant.granted_tool_scopes),
            "providers": set(manifest.provider_access)
            & set(grant.granted_provider_scopes),
            "data": set(manifest.read_data_classes + manifest.write_data_classes)
            & set(grant.granted_data_scopes),
        }

    def assert_tool_allowed(
        self, project_id: str, extension_id: str, version: str, operation: str
    ) -> None:
        scopes = self.effective_scopes(project_id, extension_id, version)
        if operation not in scopes["tools"]:
            raise ExtensionAuthzError(f"tool_not_granted:{operation}")

    def disable(self, project_id: str, extension_id: str, version: str) -> None:
        key = (project_id, extension_id, version)
        grant = self._grants.get(key)
        if grant is None:
            raise ExtensionAuthzError("grant_missing")
        grant.state = "disabled"
        grant.enabled = False

    def list_for_project(self, project_id: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for (pid, _eid, _ver), grant in self._grants.items():
            if pid != project_id:
                continue
            out.append(grant.model_dump(mode="json"))
        return out
