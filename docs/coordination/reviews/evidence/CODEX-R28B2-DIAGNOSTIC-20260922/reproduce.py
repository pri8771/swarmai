import asyncio
import inspect
from pathlib import Path

from swarm.tools.adapters.local_sandbox import LocalSandboxAdapter
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.v17_gateway import ConsequentialToolGateway


class StopBeforeEffect(InMemoryEffectStore):
    def __init__(self):
        super().__init__()
        self.reserved_actor = None

    def reserve(self, envelope):
        self.reserved_actor = envelope.actor
        raise RuntimeError("STOP_BEFORE_EFFECT")


async def main():
    adapter = LocalSandboxAdapter(root=Path("/tmp/swarm-r28b2-diagnostic-sandbox"))
    store = StopBeforeEffect()
    gateway = ConsequentialToolGateway(
        adapter,
        project_id="project-a",
        allowed_scopes={"sandbox.fs"},
        current_lease_generation=0,
        current_cancellation_generation=0,
        store=store,
    )
    envelope = adapter.normalize(
        {
            "project_id": "project-a",
            "actor": "forged-untrusted-actor",
            "lease_generation": 0,
            "cancellation_generation": 0,
            "text": "never executed",
        }
    )
    try:
        await gateway.execute_envelope(envelope)
    except RuntimeError as exc:
        assert str(exc) == "STOP_BEFORE_EFFECT"
    else:
        raise AssertionError("expected pre-effect stop")
    assert store.reserved_actor == "forged-untrusted-actor"
    print("execute_envelope_signature=", inspect.signature(gateway.execute_envelope))
    print("forged_actor_reached_reservation=", store.reserved_actor)
    print("adapter_execute_called=false (reserve raised before begin/execute)")


asyncio.run(main())
