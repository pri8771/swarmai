import asyncio
import json
import os

from swarm.db.engine import create_db_engine, make_session_factory
from swarm.db.models import Base
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import DurableEffectRepository
from swarm.tools.v17_gateway import ConsequentialToolGateway


async def execute_case(factory, *, operation, body):
    adapter = ApiMcpAdapter()
    store = DurableEffectRepository(factory)
    gateway = ConsequentialToolGateway(
        adapter,
        project_id="synthetic_pg",
        allowed_scopes={"network.https", "mcp.call"},
        current_lease_generation=1,
        current_cancellation_generation=0,
        store=store,
    )
    envelope = adapter.normalize(
        {"project_id": "synthetic_pg", "operation": operation, "body": body}
    )
    envelope.approval_id = gateway.make_approval(envelope).approval_id
    receipt = await gateway.execute_envelope(envelope)
    return {
        "accepted": receipt.outcome,
        "adapter_calls": adapter.call_count,
        "operation": receipt.operation,
        "mission_id": envelope.mission_id,
        "task_id": envelope.task_id,
        "attempt_id": envelope.attempt_id,
        "lease_generation": envelope.lease_generation,
        "cancellation_generation": envelope.cancellation_generation,
        "durable_store_type": type(store).__name__,
        "stored_state": store.get(
            project_id=envelope.project_id, effect_key=envelope.effect_key
        )["state"],
    }


async def main():
    database_url = os.environ["R28B1_DATABASE_URL"]
    engine = create_db_engine(database_url)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    try:
        output = {
            "missing_authority": await execute_case(
                factory, operation="echo", body="missing-authority"
            ),
            "undeclared_operation": await execute_case(
                factory, operation="undeclared.synthetic", body="undeclared"
            ),
        }
        print(json.dumps(output, indent=2, sort_keys=True))
    finally:
        engine.dispose()


asyncio.run(main())
