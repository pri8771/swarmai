"""R28c adapter registry identity, routing, and concurrency boundaries."""

from __future__ import annotations

import asyncio
import threading
from typing import Any

import pytest

from swarm.contracts.actions import (
    ActionEnvelope,
    ActionReceiptV17,
    AdapterManifest,
    OperationDecl,
)
from swarm.tools.adapter_registry import AdapterRegistry, ToolAuthorizationError
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.fences import ActorContext, StaticFenceProvider, StaticPolicyProvider
from swarm.tools.v17_gateway import ConsequentialToolGateway


class ReadOnlyAdapter:
    def __init__(
        self,
        integration_id: str,
        *,
        barrier: threading.Barrier | None = None,
        normalized_identity: tuple[str, str] | None = None,
    ) -> None:
        self.tag = integration_id
        self.barrier = barrier
        self.normalized_identity = normalized_identity
        self.normalize_calls = 0
        self.execute_calls = 0
        self.manifest = AdapterManifest(
            integration_id=integration_id,
            integration_version="1",
            adapter_class="local_sandbox",
            operations={
                "read": OperationDecl(
                    side_effect_class="none",
                    risk_class="low",
                    scopes=[f"read.{integration_id}"],
                    read_data_classes=["fixture"],
                    write_data_classes=[],
                )
            },
            read_data_classes=["fixture"],
            risk_class="low",
        )

    def normalize(self, request: dict[str, Any]) -> ActionEnvelope:
        self.normalize_calls += 1
        identity = self.normalized_identity or (
            self.manifest.integration_id,
            self.manifest.integration_version,
        )
        return ActionEnvelope(
            project_id=str(request["project_id"]),
            actor=str(request["actor"]),
            integration_id=identity[0],
            integration_version=identity[1],
            operation="read",
            destination=f"fixture://{self.tag}/{request['value']}",
            normalized_payload={"value": request["value"]},
            requested_scopes=[f"read.{self.tag}"],
            side_effect_class="none",
            risk_class="low",
            lease_generation=1,
            cancellation_generation=0,
        ).ensure_hashes()

    def validate(self, envelope: ActionEnvelope) -> None:
        assert envelope.integration_id == self.tag

    def observe_pre_state(self, envelope: ActionEnvelope) -> dict[str, Any]:
        return {"adapter": self.tag, "phase": "pre"}

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        self.execute_calls += 1
        if self.barrier is not None:
            self.barrier.wait(timeout=2)
        return {
            "outcome": "succeeded",
            "adapter": self.tag,
            "value": envelope.normalized_payload["value"],
        }

    def observe_post_state(
        self, envelope: ActionEnvelope, execution_result: dict[str, Any]
    ) -> dict[str, Any]:
        assert execution_result["adapter"] == self.tag
        return {"adapter": self.tag, "value": execution_result["value"]}

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]:
        return {"state": "unknown"}


def gateway(*adapters: ReadOnlyAdapter) -> ConsequentialToolGateway:
    registry = AdapterRegistry()
    for adapter in adapters:
        registry.register(adapter)
    return ConsequentialToolGateway(
        registry=registry,
        store=InMemoryEffectStore(),
        fences=StaticFenceProvider(1, 0),
        policy=StaticPolicyProvider(
            {f"read.{adapter.manifest.integration_id}" for adapter in adapters},
            "v17-policy-1",
        ),
    )


def test_registry_duplicate_unknown_and_sorted_manifests() -> None:
    registry = AdapterRegistry()
    zulu = ReadOnlyAdapter("zulu")
    alpha = ReadOnlyAdapter("alpha")
    registry.register(zulu)
    registry.register(alpha)

    assert [manifest.integration_id for manifest in registry.manifests()] == ["alpha", "zulu"]
    assert registry.resolve("alpha", "1") is alpha

    with pytest.raises(ValueError, match="^adapter_already_registered$"):
        registry.register(ReadOnlyAdapter("alpha"))
    with pytest.raises(ToolAuthorizationError, match="^unknown_integration$"):
        registry.resolve("missing", "1")


@pytest.mark.asyncio
async def test_same_gateway_routes_concurrent_requests_without_adapter_cross_talk() -> None:
    barrier = threading.Barrier(2)
    alpha = ReadOnlyAdapter("alpha", barrier=barrier)
    beta = ReadOnlyAdapter("beta", barrier=barrier)
    subject = gateway(alpha, beta)
    context = ActorContext(actor="worker", project_id="proj_registry")

    async def execute(adapter: ReadOnlyAdapter, value: str):
        return await subject.execute_request(
            {"project_id": "proj_registry", "actor": "worker", "value": value},
            integration_id=adapter.manifest.integration_id,
            integration_version=adapter.manifest.integration_version,
            context=context,
        )

    alpha_receipt, beta_receipt = await asyncio.gather(execute(alpha, "one"), execute(beta, "two"))

    assert (alpha.execute_calls, beta.execute_calls) == (1, 1)
    assert (alpha_receipt.integration_id, alpha_receipt.post_observation) == (
        "alpha",
        {"adapter": "alpha", "value": "one"},
    )
    assert (beta_receipt.integration_id, beta_receipt.post_observation) == (
        "beta",
        {"adapter": "beta", "value": "two"},
    )


@pytest.mark.asyncio
async def test_execute_request_resolves_before_normalize_and_rejects_identity_change() -> None:
    spy = ReadOnlyAdapter("registered")
    subject = gateway(spy)
    context = ActorContext(actor="worker", project_id="proj_registry")
    request = {"project_id": "proj_registry", "actor": "worker", "value": "one"}

    with pytest.raises(ToolAuthorizationError, match="^unknown_integration$"):
        await subject.execute_request(
            request,
            integration_id="missing",
            integration_version="1",
            context=context,
        )
    assert spy.normalize_calls == 0

    mismatch = ReadOnlyAdapter("declared", normalized_identity=("other", "1"))
    mismatch_gateway = gateway(mismatch)
    with pytest.raises(ToolAuthorizationError, match="^normalized_integration_mismatch$"):
        await mismatch_gateway.execute_request(
            request,
            integration_id="declared",
            integration_version="1",
            context=context,
        )
    assert mismatch.normalize_calls == 1
    assert mismatch.execute_calls == 0
