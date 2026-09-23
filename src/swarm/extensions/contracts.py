"""Extension manifest + grant contracts (ART-V19)."""

from __future__ import annotations

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now


class ExtensionManifest(StrictModel):
    extension_id: str
    version: str
    content_digest: str
    publisher: str = "local"
    compatibility_range: str = ">=1.7,<4.0"
    declared_capabilities: list[str] = Field(default_factory=list)
    read_data_classes: list[str] = Field(default_factory=list)
    write_data_classes: list[str] = Field(default_factory=list)
    tool_operations: list[str] = Field(default_factory=list)
    provider_access: list[str] = Field(default_factory=list)
    network_scopes: list[str] = Field(default_factory=list)
    filesystem_scopes: list[str] = Field(default_factory=list)
    secrets_refs_required: list[str] = Field(default_factory=list)
    entrypoints: dict[str, str] = Field(default_factory=dict)
    risk_class: str = "low"


class ProjectExtensionGrant(StrictModel):
    grant_id: str = Field(default_factory=lambda: new_id("xgr_"))
    project_id: str
    extension_id: str
    version: str
    enabled: bool = True
    state: str = "enabled"  # enabled|draining|disabled
    granted_capabilities: list[str] = Field(default_factory=list)
    granted_data_scopes: list[str] = Field(default_factory=list)
    granted_tool_scopes: list[str] = Field(default_factory=list)
    granted_provider_scopes: list[str] = Field(default_factory=list)
    approval_ref: str | None = None
    enabled_at: str = Field(default_factory=lambda: utc_now().isoformat())
