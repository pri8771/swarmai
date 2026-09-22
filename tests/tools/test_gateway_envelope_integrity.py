"""R30b prerequisite: local engineering checks; no API transport invocation."""

from __future__ import annotations

from typing import Any

import pytest

from swarm.contracts.actions import ActionEnvelope
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.fences import ActorContext, StaticFenceProvider, StaticPolicyProvider
from swarm.tools.manifests import MANIFEST_DIR, load_manifest
from swarm.tools.v17_gateway import ConsequentialToolGateway, ToolAuthorizationError

CONTEXT = ActorContext(actor="worker", project_id="integrity-project")


class RecordingAdapter(ApiMcpAdapter):
    def __init__(self) -> None:
        manifest = load_manifest(MANIFEST_DIR / "mcp.echo@1.json")
        # Engineering-only read operation allows the existing memory store.
        manifest.operations["echo"] = manifest.operations["echo"].model_copy(
            update={"side_effect_class": "none", "risk_class": "low"}
        )
        super().__init__(manifest)
        self.attempts: list[tuple[str, Any]] = []

    def observe_pre_state(self, envelope):
        self.attempts.append(("pre", getattr(envelope, "execution_attempt", None)))
        return {}

    def execute(self, envelope):
        self.attempts.append(("execute", getattr(envelope, "execution_attempt", None)))
        return {"outcome": "succeeded"}

    def observe_post_state(self, envelope, result):
        self.attempts.append(("post", getattr(envelope, "execution_attempt", None)))
        return {}


def gateway(adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return ConsequentialToolGateway(
        registry=registry,
        store=InMemoryEffectStore(),
        fences=StaticFenceProvider(lease_generation=1, cancellation_generation=0),
        policy=StaticPolicyProvider({"network.https", "mcp.call"}, "v17-policy-1"),
    )


def envelope(adapter):
    return adapter.normalize(
        {
            "project_id": CONTEXT.project_id,
            "body": "approved",
            "lease_generation": 1,
            "cancellation_generation": 0,
        }
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("entry", ["execute_envelope", "reconcile"])
@pytest.mark.parametrize("field", ["normalized_payload", "destination"])
async def test_stale_hash_rejects_before_validation_policy_or_store(monkeypatch, entry, field):
    adapter = RecordingAdapter()
    gw = gateway(adapter)
    env = envelope(adapter)
    update = (
        {field: {"body": "changed"}}
        if field == "normalized_payload"
        else {field: "mcp://echo/changed"}
    )
    altered = env.model_copy(update=update)

    def forbidden(*args, **kwargs):
        pytest.fail("authority or adapter boundary reached before integrity denial")

    monkeypatch.setattr(adapter, "validate", forbidden)
    monkeypatch.setattr(gw, "_authorize_policy", forbidden)
    monkeypatch.setattr(gw.store, "get", forbidden)
    monkeypatch.setattr(gw.store, "reserve", forbidden)
    monkeypatch.setattr(gw.store, "get_approval", forbidden)
    with pytest.raises(ToolAuthorizationError, match="payload_hash_mismatch"):
        await getattr(gw, entry)(altered, context=CONTEXT)
    assert not adapter.attempts


@pytest.mark.asyncio
@pytest.mark.parametrize("empty_hash", [False, True])
async def test_custom_key_and_durable_attempt_override_preserve_logical_identity(empty_hash):
    adapter = RecordingAdapter()
    gw = gateway(adapter)
    env = envelope(adapter)
    expected_hash = env.payload_hash
    env = env.model_copy(
        update={
            "effect_key": "custom:mission:task:1",
            "idempotency_key": "stable-key",
            "execution_attempt": 999,
        }
    )
    if empty_hash:
        env.payload_hash = ""
    receipt = await gw.execute_envelope(env, context=CONTEXT)
    assert receipt.outcome == "succeeded"
    assert adapter.attempts == [("pre", 1), ("execute", 1), ("post", 1)]
    assert env.execution_attempt == 999  # caller envelope was not reused as runtime authority
    assert "execution_attempt" not in env.model_dump()
    loaded = ActionEnvelope.model_validate_json(env.model_dump_json())
    assert loaded.execution_attempt is None
    row = gw.store.get(project_id=env.project_id, effect_key=env.effect_key)
    assert row["payload_hash"] == expected_hash
    assert row["effect_key"] == "custom:mission:task:1"
    assert env.idempotency_key == "stable-key"


@pytest.mark.parametrize("field", ["normalized_payload", "destination"])
def test_make_approval_rejects_stale_hash_without_writing(field):
    adapter = RecordingAdapter()
    gw = gateway(adapter)
    env = envelope(adapter)
    altered = env.model_copy(
        update={
            field: {"body": "changed"} if field == "normalized_payload" else "mcp://echo/changed"
        }
    )
    with pytest.raises(ToolAuthorizationError, match="payload_hash_mismatch"):
        gw.make_approval(altered, context=CONTEXT)
    assert gw.store.approvals == {}
    assert adapter.attempts == []


@pytest.mark.parametrize("empty_hash", [False, True])
def test_make_approval_preserves_valid_hash_and_custom_effect_key(empty_hash):
    adapter = RecordingAdapter()
    gw = gateway(adapter)
    env = envelope(adapter)
    expected_hash = env.payload_hash
    env.effect_key = "custom:approval-key"
    if empty_hash:
        env.payload_hash = ""
    grant = gw.make_approval(env, context=CONTEXT)
    assert grant.payload_hash == expected_hash
    assert grant.effect_key == "custom:approval-key"
    assert len(gw.store.approvals) == 1
