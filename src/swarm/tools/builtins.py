"""Built-in tools and fake external action provider."""

from __future__ import annotations

from typing import Any

from swarm.contracts.common import new_id
from swarm.tools.registry import CapabilityRegistry, ToolSpec


def register_builtin_tools(registry: CapabilityRegistry) -> None:
    registry.register(
        ToolSpec(
            name="workspace.read",
            version="1",
            required_scopes=("workspace.read",),
            side_effecting=False,
            description="Read allowlisted workspace text",
        ),
        lambda args: {"content": args.get("content", ""), "bytes": len(args.get("content", ""))},
    )
    registry.register(
        ToolSpec(
            name="calc.add",
            version="1",
            required_scopes=("calc",),
            side_effecting=False,
            description="Deterministic addition",
        ),
        lambda args: {"sum": float(args["a"]) + float(args["b"])},
    )
    registry.register(
        ToolSpec(
            name="artifact.publish",
            version="1",
            required_scopes=("artifact.write",),
            side_effecting=True,
            description="Publish internal artifact metadata",
        ),
        lambda args: {
            "artifact_id": new_id("art_"),
            "uri": args.get("uri", "memory://artifact"),
            "destination": args.get("destination", "local"),
        },
    )
    registry.register(
        ToolSpec(
            name="tests.run_isolated",
            version="1",
            required_scopes=("tests.run",),
            side_effecting=False,
            description="Run isolated tests via sandbox runner",
            network=False,
        ),
        lambda args: {"ran": True, "script": args.get("script"), "network": False},
    )


class FakeExternalActionProvider:
    """Idempotent fake external side-effect for reconciliation tests."""

    def __init__(self) -> None:
        self.actions: dict[str, dict[str, Any]] = {}
        self.force_unknown_once: set[str] = set()

    def execute(self, *, idempotency_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        if idempotency_key in self.actions:
            return dict(self.actions[idempotency_key])
        if idempotency_key in self.force_unknown_once:
            self.force_unknown_once.remove(idempotency_key)
            return {"outcome": "unknown", "external_id": None}
        result = {
            "outcome": "succeeded",
            "external_id": new_id("ext_"),
            "echo": payload,
        }
        self.actions[idempotency_key] = result
        return dict(result)

    def reconcile(self, idempotency_key: str) -> dict[str, Any] | None:
        return self.actions.get(idempotency_key)
