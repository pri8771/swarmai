"""R28b-1 declared classification and required authority, with real PG receipts."""

import pytest
from tests.integration.db.effect_fixtures import bind_lease
from tests.integration.db.test_effect_admission_fences import engine as engine
from tests.integration.db.test_effect_admission_fences import factory as factory

from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.adapters.browser_session import BrowserSessionAdapter
from swarm.tools.adapters.local_sandbox import LocalSandboxAdapter
from swarm.tools.effects import DurableEffectRepository, InMemoryEffectStore
from swarm.tools.fences import (
    ActorContext,
    LeaseFenceProvider,
    StaticFenceProvider,
    StaticPolicyProvider,
)
from swarm.tools.manifests import MANIFEST_DIR, load_manifest
from swarm.tools.v17_gateway import (
    ConsequentialToolGateway,
    PolicyDeniedError,
    StaleLeaseError,
    ToolAuthorizationError,
)


def _registry(adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return registry


def gateway(adapter, store, project="r28b1"):
    return ConsequentialToolGateway(
        registry=_registry(adapter),
        store=store,
        fences=(
            LeaseFenceProvider(store.factory)
            if isinstance(store, DurableEffectRepository)
            else StaticFenceProvider(1, 0)
        ),
        policy=StaticPolicyProvider({"network.https", "mcp.call"}, "v17-policy-1"),
    )


def context(project="r28b1"):
    return ActorContext(actor="worker", project_id=project)


def complete_claim(adapter):
    return adapter.normalize(
        {
            "project_id": "r28b1",
            "mission_id": "synthetic-mission",
            "task_id": "synthetic-task",
            "attempt_id": "synthetic-attempt",
            "lease_generation": 1,
            "cancellation_generation": 0,
        }
    )


def test_normalizers_do_not_invent_generations(tmp_path):
    for adapter in (
        ApiMcpAdapter(
            load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
        ),
        BrowserSessionAdapter(
            load_manifest(MANIFEST_DIR / "browser.session@1.json"),
        ),
        LocalSandboxAdapter(load_manifest(MANIFEST_DIR / "local.sandbox@1.json"), root=tmp_path),
    ):
        envelope = adapter.normalize({"project_id": "r28b1"})
        assert envelope.lease_generation is None
        assert envelope.cancellation_generation is None


@pytest.mark.asyncio
async def test_undeclared_operation_denied_before_adapter_action():
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = adapter.normalize({"project_id": "r28b1"})
    envelope.operation = "undeclared.synthetic"
    with pytest.raises(ToolAuthorizationError, match="operation_not_declared"):
        await gateway(adapter, InMemoryEffectStore()).execute_envelope(envelope, context=context())
    assert adapter.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("side", ["consequential", "irreversible"])
@pytest.mark.parametrize(
    "field",
    [
        "mission_id",
        "task_id",
        "attempt_id",
        "lease_generation",
        "cancellation_generation",
    ],
)
async def test_missing_authority_is_denied_before_action(side, field):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    adapter.manifest.operations["echo"].side_effect_class = side
    envelope = complete_claim(adapter)
    envelope.side_effect_class = "none"
    setattr(envelope, field, None)
    with pytest.raises(StaleLeaseError, match="fence_missing"):
        await gateway(adapter, InMemoryEffectStore()).execute_envelope(envelope, context=context())
    assert adapter.call_count == 0


@pytest.mark.asyncio
async def test_underclassification_cannot_skip_durability():
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = complete_claim(adapter)
    envelope.side_effect_class, envelope.risk_class = "none", "low"
    with pytest.raises(PolicyDeniedError, match="durable_store_required"):
        await gateway(adapter, InMemoryEffectStore()).execute_envelope(envelope, context=context())
    assert adapter.call_count == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_underclassification_cannot_skip_approval(factory):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = bind_lease(factory, adapter.normalize({"project_id": "r28b1"}))
    envelope.side_effect_class, envelope.risk_class = "none", "low"
    store = DurableEffectRepository(factory)
    with pytest.raises(PolicyDeniedError, match="approval_required"):
        await gateway(adapter, store).execute_envelope(envelope, context=context())
    assert adapter.call_count == 0
    assert store.get(project_id=envelope.project_id, effect_key=envelope.effect_key) is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claim,expected",
    [
        (("none", "low"), ("consequential", "medium")),
        (("irreversible", "critical"), ("irreversible", "critical")),
    ],
)
async def test_receipt_persists_higher_classification_without_mutating_claim(
    factory, claim, expected
):
    adapter = ApiMcpAdapter(
        load_manifest(MANIFEST_DIR / "mcp.echo@1.json"),
    )
    envelope = bind_lease(factory, adapter.normalize({"project_id": "r28b1"}))
    envelope.side_effect_class, envelope.risk_class = claim
    store = DurableEffectRepository(factory)
    gw = gateway(adapter, store)
    envelope.approval_id = gw.make_approval(envelope, context=context()).approval_id
    receipt = await gw.execute_envelope(envelope, context=context())
    assert receipt.outcome == "succeeded"
    assert (receipt.effective_side_effect_class, receipt.effective_risk_class) == expected
    assert (envelope.side_effect_class, envelope.risk_class) == claim
    persisted = DurableEffectRepository(factory).terminal_receipt(
        project_id=envelope.project_id,
        effect_key=envelope.effect_key,
    )
    assert persisted is not None
    assert (persisted.effective_side_effect_class, persisted.effective_risk_class) == expected
    assert adapter.call_count == 1
