"""Tool capability registry and typed specs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import payload_hash


@dataclass(frozen=True)
class ToolSpec:
    name: str
    version: str
    required_scopes: tuple[str, ...]
    side_effecting: bool
    description: str
    network: bool = False


ToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]] | dict[str, Any]]


@dataclass
class CapabilityRegistry:
    tools: dict[str, ToolSpec] = field(default_factory=dict)
    handlers: dict[str, ToolHandler] = field(default_factory=dict)

    def register(self, spec: ToolSpec, handler: ToolHandler) -> None:
        key = f"{spec.name}@{spec.version}"
        self.tools[key] = spec
        self.handlers[key] = handler

    def get(self, name: str, version: str) -> ToolSpec:
        return self.tools[f"{name}@{version}"]

    def handler_for(self, name: str, version: str) -> ToolHandler:
        return self.handlers[f"{name}@{version}"]


def normalize_args(args: dict[str, Any]) -> dict[str, Any]:
    return {k: args[k] for k in sorted(args)}


def hash_operation(tool_version: str, args: dict[str, Any], destination: str) -> str:
    return payload_hash(
        {"tool_version": tool_version, "args": normalize_args(args), "destination": destination}
    )
