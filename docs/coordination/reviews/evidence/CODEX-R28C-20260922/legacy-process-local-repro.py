import asyncio
import json
import sys

sys.path.insert(0, "/Users/pchordia/Downloads/swarm_codex/review/swarm-r28b2-source/src")

from swarm.contracts.workspace import ToolCall
from swarm.tools.gateway import ToolGateway, make_approval
from swarm.tools.registry import CapabilityRegistry, ToolSpec, hash_operation


async def main():
    calls = {"count": 0}
    registry = CapabilityRegistry()

    def consequential_handler(args):
        calls["count"] += 1
        return {"outcome": "succeeded", "external_id": f"synthetic-{calls['count']}"}

    registry.register(
        ToolSpec(
            name="synthetic.send",
            version="1",
            required_scopes=("send",),
            side_effecting=True,
            description="synthetic counting side effect",
        ),
        consequential_handler,
    )
    args = {"destination": "synthetic-target", "body": "fixture"}
    approval = make_approval(
        tool_version="synthetic.send@1",
        args=args,
        destination="synthetic-target",
        project_id="proj_r28c",
    )

    def gateway():
        return ToolGateway(
            registry,
            allowed_scopes={"send"},
            current_lease_generation=7,
            approvals={approval.id: approval},
        )

    def call():
        return ToolCall(
            task_id="task-r28c",
            attempt_id="attempt-r28c",
            tool_version="synthetic.send@1",
            normalized_args=dict(args),
            payload_hash=hash_operation(
                "synthetic.send@1", args, destination="synthetic-target"
            ),
            lease_generation=7,
            operation_id="op-same-across-process-boundaries",
            approval_id=approval.id,
        )

    first_gateway = gateway()
    first = await first_gateway.execute_or_reconcile(call())
    replay_same_instance = await first_gateway.execute_or_reconcile(call())
    count_after_same_instance_replay = calls["count"]

    second_gateway = gateway()
    replay_fresh_instance = await second_gateway.execute_or_reconcile(call())

    observed = {
        "accepted_source": "a06b8a82925daa4dd08a137cb1eb724aaa2d4efb",
        "same_operation_id": first.operation_id,
        "count_after_first_and_same_instance_replay": count_after_same_instance_replay,
        "count_after_fresh_gateway_replay": calls["count"],
        "same_instance_receipt_external_id": replay_same_instance.external_id,
        "fresh_instance_receipt_external_id": replay_fresh_instance.external_id,
        "finding": "process_local_dedupe_reexecutes_on_fresh_gateway",
    }
    assert count_after_same_instance_replay == 1
    assert calls["count"] == 2
    assert first.external_id == replay_same_instance.external_id == "synthetic-1"
    assert replay_fresh_instance.external_id == "synthetic-2"
    print(json.dumps(observed, indent=2, sort_keys=True))


asyncio.run(main())
