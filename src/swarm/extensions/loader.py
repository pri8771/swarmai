"""Load extension adapters only through ToolGateway boundary."""

from __future__ import annotations

from pathlib import Path

from swarm.extensions.registry import ExtensionAuthzError, ExtensionRegistry
from swarm.tools.adapters.base import IntegrationAdapter
from swarm.tools.adapters.local_sandbox import LocalSandboxAdapter
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.v17_gateway import ConsequentialToolGateway


class ExtensionLoader:
    """Maps extension entrypoints to gateway-mediated adapters — no broker bypass."""

    def __init__(self, registry: ExtensionRegistry) -> None:
        self.registry = registry

    def build_gateway(
        self,
        *,
        project_id: str,
        extension_id: str,
        version: str,
        adapter: IntegrationAdapter | None = None,
        root: Path | None = None,
    ) -> ConsequentialToolGateway:
        scopes = self.registry.effective_scopes(project_id, extension_id, version)
        tool_scopes = scopes["tools"] | scopes["capabilities"]
        if not tool_scopes:
            raise ExtensionAuthzError("empty_effective_scopes")
        chosen = adapter or LocalSandboxAdapter(root=root)
        return ConsequentialToolGateway(
            chosen,
            project_id=project_id,
            allowed_scopes=set(tool_scopes) | {"sandbox.fs"},
            current_lease_generation=1,
            current_cancellation_generation=0,
            store=InMemoryEffectStore(),
        )
