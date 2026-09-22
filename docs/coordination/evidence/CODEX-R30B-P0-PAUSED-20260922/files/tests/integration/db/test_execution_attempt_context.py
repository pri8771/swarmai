"""Durable R30b prerequisite; synthetic adapter, real owned PostgreSQL only."""

from __future__ import annotations

import pytest

from swarm.contracts.actions import ActionEnvelope
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.manifests import MANIFEST_DIR, load_manifest
from tests.integration.db.effect_fixtures import bind_lease
from tests.integration.db.test_effect_transactions import (
    _context,
    _gateway,
    _used_count,
    engine,
    factory,
)

__all__ = ["engine", "factory"]
pytestmark = pytest.mark.integration


class AttemptAdapter(ApiMcpAdapter):
    def __init__(self, *, uncertain=False):
        super().__init__(load_manifest(MANIFEST_DIR / "mcp.echo@1.json"))
        self.uncertain = uncertain
        self.phases = []
        self.identities = []

    def record(self, phase, envelope):
        self.phases.append((phase, getattr(envelope, "execution_attempt", None)))
        self.identities.append(
            (envelope.effect_key, envelope.idempotency_key, envelope.payload_hash)
        )

    def observe_pre_state(self, envelope):
        self.record("pre", envelope)
        return {}

    def execute(self, envelope):
        self.record("execute", envelope)
        return {"outcome": "unknown" if self.uncertain else "succeeded"}

    def observe_post_state(self, envelope, result):
        self.record("post", envelope)
        return {}

    def reconcile(self, envelope, prior_receipts):
        self.record("reconcile", envelope)
        return {"state": "not_applied"}


@pytest.mark.asyncio
async def test_reload_reconciles_persisted_attempt_then_retries_with_next_attempt(factory):
    first_adapter = AttemptAdapter(uncertain=True)
    gw = _gateway(first_adapter, factory)
    env = bind_lease(
        factory, first_adapter.normalize({"project_id": "proj_a", "body": "immutable"})
    )
    env.effect_key = "r30b:mission:custom-effect"
    env.idempotency_key = "r30b:logical-stable-key"
    env.approval_id = gw.make_approval(env, context=_context(), max_effect_count=1).approval_id
    serialized = env.model_dump_json()
    first = await gw.execute_envelope(env, context=_context())
    assert first.outcome == "unknown"
    assert first_adapter.phases == [("pre", 1), ("execute", 1), ("post", 1)]
    assert _used_count(factory, env.approval_id) == 1

    # Reconstruct repository, gateway, adapter and envelope; no per-adapter memory survives.
    restored = ActionEnvelope.model_validate_json(serialized)
    fresh_adapter = AttemptAdapter()
    gw2 = _gateway(fresh_adapter, factory)
    assert (
        gw2.store.get(project_id=restored.project_id, effect_key=restored.effect_key)[
            "attempt_count"
        ]
        == 1
    )
    second = await gw2.reconcile(restored, context=_context())
    assert second.outcome == "succeeded"
    assert fresh_adapter.phases == [("reconcile", 1), ("pre", 2), ("execute", 2), ("post", 2)]
    assert second.attempt_number == 3  # receipts count reconciliation; execution attempt is 2
    row = gw2.store.get(project_id=restored.project_id, effect_key=restored.effect_key)
    assert row["attempt_count"] == 2
    assert row["payload_hash"] == restored.payload_hash
    assert row["effect_key"] == restored.effect_key
    assert (
        fresh_adapter.identities
        == [(restored.effect_key, restored.idempotency_key, restored.payload_hash)] * 4
    )
    assert _used_count(factory, restored.approval_id) == 1
