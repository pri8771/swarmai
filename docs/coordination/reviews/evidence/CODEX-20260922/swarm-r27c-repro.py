"""Offline reviewer reproducer; no external adapter or product state.

The controlled not_applied transition mirrors the existing R27c test seam.
This is engineering defect evidence, not a live checkpoint.
"""
import asyncio
import json

from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.v17_gateway import ConsequentialToolGateway


def gateway(adapter, store):
    return ConsequentialToolGateway(
        adapter, project_id="review_project",
        allowed_scopes={"network.https", "mcp.call"},
        current_lease_generation=1, store=store,
    )


async def main():
    store = InMemoryEffectStore()

    def fail_without_effect(operation, payload):
        raise RuntimeError("controlled_no_effect")

    adapter = ApiMcpAdapter(transport=fail_without_effect)
    first_gateway = gateway(adapter, store)
    envelope = adapter.normalize({"project_id": "review_project", "body": "review"})
    grant_a = first_gateway.make_approval(envelope)
    envelope.approval_id = grant_a.approval_id
    first = await first_gateway.execute_envelope(envelope)
    assert first.outcome == "failed"
    store.effects[(envelope.project_id, envelope.effect_key)]["state_reason"] = "not_applied"
    adapter_b = ApiMcpAdapter()
    retry_gateway = gateway(adapter_b, store)
    # A valid one-use payload grant may cover more than one effect key.
    grant_b = grant_a.model_copy(update={
        "approval_id": "apr_review_b", "effect_key": None, "used_count": 0,
    })
    retry_gateway.put_approval(grant_b)
    envelope.approval_id = grant_b.approval_id
    retry = await retry_gateway.execute_envelope(envelope)
    after_retry = store.approvals[grant_b.approval_id].used_count
    second_envelope = envelope.model_copy(update={"effect_key": "review_second_effect"})
    second = await retry_gateway.execute_envelope(second_envelope)
    print(json.dumps({
        "source_sha": "05fe7807db3509d68dd8a86a0616c9e8ffaa2307",
        "evidence_class": "OFFLINE_IN_MEMORY_ENGINEERING_REPRODUCTION",
        "first_outcome": first.outcome,
        "retry_with_new_grant": retry.outcome,
        "grant_b_used_count_after_retry": after_retry,
        "second_effect_with_same_one_use_grant": second.outcome,
        "grant_b_used_count_final": store.approvals[grant_b.approval_id].used_count,
        "adapter_b_calls": adapter_b.call_count,
        "finding_reproduced": after_retry == 0 and adapter_b.call_count == 2,
    }, indent=2))
    assert after_retry == 0 and adapter_b.call_count == 2


asyncio.run(main())
