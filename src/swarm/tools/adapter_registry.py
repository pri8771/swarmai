"""Explicit, versioned adapter registration for the single action boundary."""

from swarm.contracts.actions import AdapterManifest
from swarm.tools.adapters.base import IntegrationAdapter


class ToolAuthorizationError(PermissionError):
    pass


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[tuple[str, str], IntegrationAdapter] = {}

    def register(self, adapter: IntegrationAdapter) -> None:
        key = (adapter.manifest.integration_id, adapter.manifest.integration_version)
        if key in self._adapters:
            raise ValueError("adapter_already_registered")
        self._adapters[key] = adapter

    def resolve(self, integration_id: str, integration_version: str) -> IntegrationAdapter:
        try:
            return self._adapters[(integration_id, integration_version)]
        except KeyError as exc:
            raise ToolAuthorizationError("unknown_integration") from exc

    def manifests(self) -> list[AdapterManifest]:
        return [self._adapters[key].manifest for key in sorted(self._adapters)]
