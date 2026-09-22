"""R31a real PostgreSQL persistence with offline HTTP transport only."""

import json

import httpx
import pytest
from tests.integration.db.effect_fixtures import bind_lease
from tests.integration.db.test_effect_transactions import engine, factory
from tests.tools.test_http_session_adapter import COOKIE, envelope, identifiers, setup_adapter

from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.effects import DurableEffectRepository
from swarm.tools.fences import ActorContext, LeaseFenceProvider, StaticPolicyProvider
from swarm.tools.v17_gateway import ConsequentialToolGateway, ReconciliationRequiredError

__all__ = ["engine", "factory"]
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.mark.parametrize("reflected", [False, True])
async def test_cookie_absent_from_durable_effect_and_receipts(factory, reflected):
    captured = []

    def handler(request):
        captured.append(request)
        ref, request_id, digest = identifiers(env)
        external_id = COOKIE if reflected else "sub_123456abcdef"
        row = {"id": external_id, "client_ref": ref, "text": "approved text"}
        if request.method == "POST":
            return httpx.Response(201, json=row, headers={"X-Fixture-Request-ID": request_id})
        if "/requests/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "request_id": request_id,
                    "client_ref": ref,
                    "payload_digest": digest,
                    "phase": "terminal",
                    "outcome": "applied",
                    "external_id": external_id,
                },
            )
        return httpx.Response(200, json={"submissions": [row]})

    adapter, _ = setup_adapter(handler)
    registry = AdapterRegistry()
    registry.register(adapter)
    store = DurableEffectRepository(factory)
    gateway = ConsequentialToolGateway(
        registry=registry,
        store=store,
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider({"web.read", "web.submit"}, "v17-policy-1"),
    )
    env = bind_lease(factory, envelope(adapter))
    context = ActorContext(actor=env.actor, project_id=env.project_id)
    env.approval_id = gateway.make_approval(env, context=context).approval_id
    first = await gateway.execute_envelope(env, context=context)
    assert first.outcome == ("unknown" if reflected else "succeeded")
    if reflected:
        with pytest.raises(ReconciliationRequiredError, match="external_outcome_still_unknown"):
            await gateway.reconcile(env, context=context)
    effect = store.get(project_id=env.project_id, effect_key=env.effect_key)
    receipts = store.list_receipts(project_id=env.project_id, effect_key=env.effect_key)
    serialized = json.dumps(
        {
            "envelope": env.model_dump(mode="json"),
            "effect": effect,
            "receipts": [receipt.model_dump(mode="json") for receipt in receipts],
        },
        default=str,
    )
    assert COOKIE not in serialized
    assert sum(request.method == "POST" for request in captured) == 1
    assert effect["attempt_count"] == 1
