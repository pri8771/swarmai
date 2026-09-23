"""V1.9 project-scoped extensions — all execution via ToolGateway."""

from swarm.extensions.contracts import ExtensionManifest, ProjectExtensionGrant
from swarm.extensions.loader import ExtensionLoader
from swarm.extensions.registry import ExtensionAuthzError, ExtensionRegistry

__all__ = [
    "ExtensionManifest",
    "ProjectExtensionGrant",
    "ExtensionRegistry",
    "ExtensionAuthzError",
    "ExtensionLoader",
]
