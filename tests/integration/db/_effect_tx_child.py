"""Spawn-process entry points for R27c transaction tests (real second OS process)."""

from __future__ import annotations

import asyncio
from typing import Any

from swarm.contracts.actions import ActionEnvelope
from swarm.db.engine import create_db_engine, make_session_factory
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import DurableEffectRepository
from swarm.tools.fences import ActorContext, LeaseFenceProvider, StaticPolicyProvider
from swarm.tools.v17_gateway import ConsequentialToolGateway


class PausingAdapter(ApiMcpAdapter):
    """Signals `started` once inside execute(), then blocks until `release`."""

    def __init__(self, started: Any, release: Any) -> None:
        super().__init__()
        self._started = started
        self._release = release

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        self._started.set()
        if not self._release.wait(timeout=30):
            return {"outcome": "unknown", "external_id": None}
        return super().execute(envelope)


def run_paused_execution(
    database_url: str, envelope_json: str, started: Any, release: Any, result_queue: Any
) -> None:
    """Child: admit + execute one envelope, pausing inside the adapter."""
    engine = create_db_engine(database_url)
    try:
        factory = make_session_factory(engine)
        envelope = ActionEnvelope.model_validate_json(envelope_json)
        adapter = PausingAdapter(started, release)
        gateway = ConsequentialToolGateway(
            adapter=adapter,
            store=DurableEffectRepository(factory),
            fences=LeaseFenceProvider(factory),
            policy=StaticPolicyProvider({"network.https", "mcp.call"}, "v17-policy-1"),
        )
        context = ActorContext(actor="worker", project_id="proj_a")
        receipt = asyncio.run(gateway.execute_envelope(envelope, context=context))
        result_queue.put({"outcome": receipt.outcome, "receipt_id": receipt.receipt_id})
    except Exception as exc:  # noqa: BLE001
        started.set()
        result_queue.put({"error": f"{type(exc).__name__}:{exc}"})
    finally:
        engine.dispose()
