import asyncio
import json

from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.v17_gateway import ConsequentialToolGateway


class SyntheticDurableStore(InMemoryEffectStore):
    """Test-only store flag; no database/provider/external action."""

    durable = True


def gateway(adapter, store):
    return ConsequentialToolGateway(
        adapter,
        project_id="synthetic",
        allowed_scopes={"network.https", "mcp.call"},
        current_lease_generation=1,
        current_cancellation_generation=0,
        store=store,
    )


async def main():
    observed = {}

    # Manifest class is consequential/medium, but caller lowers the envelope.
    adapter = ApiMcpAdapter()
    gw = gateway(adapter, InMemoryEffectStore())
    env = adapter.normalize({"project_id": "synthetic", "body": "underclass"})
    env.side_effect_class = "none"
    env.risk_class = "low"
    receipt = await gw.execute_envelope(env)
    observed["underclassification"] = {
        "accepted": receipt.outcome,
        "adapter_calls": adapter.call_count,
        "receipt_effective_side_effect_class": receipt.model_dump().get(
            "effective_side_effect_class"
        ),
        "receipt_effective_risk_class": receipt.model_dump().get("effective_risk_class"),
        "approval_id": receipt.approval_id,
    }

    # Consequential envelope has no mission/task/attempt. Generations came from defaults.
    adapter = ApiMcpAdapter()
    store = SyntheticDurableStore()
    gw = gateway(adapter, store)
    env = adapter.normalize({"project_id": "synthetic", "body": "missing-fences"})
    env.approval_id = gw.make_approval(env).approval_id  # synthetic in-memory only
    receipt = await gw.execute_envelope(env)
    observed["missing_authority"] = {
        "accepted": receipt.outcome,
        "adapter_calls": adapter.call_count,
        "mission_id": env.mission_id,
        "task_id": env.task_id,
        "attempt_id": env.attempt_id,
        "lease_generation": env.lease_generation,
        "cancellation_generation": env.cancellation_generation,
    }

    # Adapter manifest has no per-operation declarations; arbitrary name is accepted.
    adapter = ApiMcpAdapter()
    store = SyntheticDurableStore()
    gw = gateway(adapter, store)
    env = adapter.normalize(
        {"project_id": "synthetic", "operation": "undeclared.synthetic", "body": "x"}
    )
    env.approval_id = gw.make_approval(env).approval_id  # synthetic in-memory only
    receipt = await gw.execute_envelope(env)
    observed["undeclared_operation"] = {
        "accepted": receipt.outcome,
        "operation": receipt.operation,
        "adapter_calls": adapter.call_count,
    }

    print(json.dumps(observed, indent=2, sort_keys=True))


asyncio.run(main())
