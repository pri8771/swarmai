"""OpenRouter free-route controls at the HTTP boundary; no external requests."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from swarm.contracts.enums import AvailabilityStatus
from swarm.contracts.provider import InferenceRequest
from swarm.providers.core.adapters import OpenRouterAdapter, OpenRouterFreeRoute
from tests.providers.core.test_core_adapters import _reservation


def _request() -> InferenceRequest:
    return InferenceRequest(
        project_id="proj_openrouter_wire",
        attempt_id="att_1",
        purpose="offline-wire-regression",
        messages=[{"role": "user", "content": "Reply OK"}],
        max_output_tokens=32,
    )


@pytest.mark.asyncio
async def test_live_openrouter_requires_exact_route_before_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"usage": {}})

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    adapter = OpenRouterAdapter(mode="live", enabled=True, secret_ref_names=[])
    route = (await adapter.discover())[0]
    assert route.availability_status == AvailabilityStatus.DISABLED
    with pytest.raises(ValueError, match="explicit free route"):
        await adapter.execute_one(_request(), _reservation(route.route_id))
    assert calls == []


@pytest.mark.parametrize(
    ("model_id", "provider_slug"),
    [
        ("openrouter/auto", "modelrun"),
        ("openrouter/free", "modelrun"),
        ("qwen/qwen3.8-27b", "modelrun"),
        ("qwen/qwen3.8-27b:free", ""),
        ("qwen/qwen3.8-27b:free", "modelrun,paid"),
    ],
)
def test_free_route_rejects_unpinned_or_unsafe_values(model_id: str, provider_slug: str) -> None:
    with pytest.raises(ValueError):
        OpenRouterFreeRoute(model_id=model_id, provider_slug=provider_slug)


@pytest.mark.asyncio
async def test_pinned_free_route_emits_only_zero_price_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"id": "mock-1", "model": "qwen/qwen3.8-27b:free", "usage": {}},
        )

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    adapter = OpenRouterAdapter(
        mode="live",
        enabled=True,
        secret_ref_names=[],
        free_route=OpenRouterFreeRoute(model_id="qwen/qwen3.8-27b:free", provider_slug="modelrun"),
    )
    route = (await adapter.discover())[0]
    assert route.model_id == "qwen/qwen3.8-27b:free"
    assert route.hosted_by == "modelrun"
    await adapter.execute_one(_request(), _reservation(route.route_id))
    assert len(sent) == 1
    assert sent[0] == {
        "model": "qwen/qwen3.8-27b:free",
        "messages": [{"role": "user", "content": "Reply OK"}],
        "stream": False,
        "max_tokens": 32,
        "provider": {
            "only": ["modelrun"],
            "allow_fallbacks": False,
            "max_price": {"prompt": 0, "completion": 0},
            "require_parameters": True,
        },
    }
