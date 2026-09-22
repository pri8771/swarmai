"""Real spawned-process crash seam; the only external effect is a temporary file."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17
from swarm.db.engine import create_db_engine, make_session_factory
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import DurableEffectRepository
from swarm.tools.fences import ActorContext, LeaseFenceProvider, StaticPolicyProvider
from swarm.tools.v17_gateway import ConsequentialToolGateway


def _registry(adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return registry


class FileEffectAdapter(ApiMcpAdapter):
    def __init__(self, path: str, crash: str | None = None) -> None:
        super().__init__()
        self.path = Path(path)
        self.crash = crash
        self.reconcile_calls = 0

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        if self.crash == "before":
            os._exit(9)
        self._calls.append({"effect_key": envelope.effect_key})
        with self.path.open("a") as stream:
            stream.write(envelope.effect_key + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if self.crash == "after":
            os._exit(9)
        return {"outcome": "succeeded", "external_id": envelope.effect_key}

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]:
        self.reconcile_calls += 1
        lines = self.path.read_text().splitlines() if self.path.exists() else []
        return {"state": "succeeded" if envelope.effect_key in lines else "not_applied"}


def run_crash(database_url: str, envelope_json: str, path: str, phase: str) -> None:
    engine = create_db_engine(database_url)
    factory = make_session_factory(engine)
    envelope = ActionEnvelope.model_validate_json(envelope_json)
    gateway = ConsequentialToolGateway(
        registry=_registry(FileEffectAdapter(path, phase)),
        store=DurableEffectRepository(factory),
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider({"network.https", "mcp.call"}, "v17-policy-1"),
    )
    context = ActorContext(actor="worker", project_id="crash_project")
    asyncio.run(gateway.execute_envelope(envelope, context=context))
    os._exit(99)  # The specified crash seam must have terminated the child first.
