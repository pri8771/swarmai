"""Provider charge and rate-limit receipt evidence, using in-process HTTP only."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from swarm.contracts.enums import ErrorClass
from swarm.contracts.provider import InferenceRequest
from swarm.providers.core.adapters import GroqAdapter, OpenRouterAdapter, OpenRouterFreeRoute
from tests.providers.core.test_core_adapters import _reservation


def _mock_client(monkeypatch: pytest.MonkeyPatch, handler: Any) -> None:
    original = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )


def _request() -> InferenceRequest:
    return InferenceRequest(
        project_id="proj_receipts",
        attempt_id="att_1",
        purpose="offline-receipt-test",
        messages=[{"role": "user", "content": "OK"}],
        max_output_tokens=8,
    )


@pytest.mark.asyncio
async def test_openrouter_cost_backend_and_safe_limit_headers_reach_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-OpenRouter-Metadata"] == "enabled"
        return httpx.Response(
            200,
            json={
                "id": "gen-offline-1",
                "model": "qwen/qwen3.8-27b:free",
                "openrouter_metadata": {
                    "attempt": 1,
                    "is_byok": False,
                    "endpoints": {
                        "available": [
                            {
                                "model": "qwen/qwen3.8-27b:free",
                                "provider": "ModelRun",
                                "selected": True,
                            }
                        ]
                    },
                },
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 1,
                    "total_tokens": 4,
                    "cost": 0,
                    "is_byok": False,
                },
            },
            headers={
                "x-ratelimit-remaining-requests": "41",
                "x-ratelimit-reset-requests": "2m",
                "set-cookie": "must-not-persist",
            },
        )

    _mock_client(monkeypatch, handler)
    adapter = OpenRouterAdapter(
        mode="live",
        secret_ref_names=[],
        free_route=OpenRouterFreeRoute(model_id="qwen/qwen3.8-27b:free", provider_slug="modelrun"),
    )
    route = (await adapter.discover())[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.normalized_usage is not None
    extras = receipt.normalized_usage.extras
    assert extras["provider_cost_usd"] == "0"
    assert extras["provider_cost_source"] == "response.usage.cost"
    assert extras["upstream_provider"] == "ModelRun"
    assert extras["openrouter_routing"] == {
        "attempt": 1,
        "is_byok": False,
        "selected_provider": "ModelRun",
        "selected_model": "qwen/qwen3.8-27b:free",
        "usage_is_byok": False,
    }
    assert extras["rate_limit_headers"] == {
        "x-ratelimit-remaining-requests": "41",
        "x-ratelimit-reset-requests": "2m",
    }
    assert "must-not-persist" not in str(receipt)


@pytest.mark.asyncio
async def test_missing_provider_cost_stays_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_client(
        monkeypatch,
        lambda request: httpx.Response(200, json={"id": "offline-2", "usage": {}}),
    )
    adapter = GroqAdapter(
        mode="live", secret_ref_names=[], pinned_model_id="openai/gpt-oss-20b"
    )
    route = (await adapter.discover())[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.normalized_usage is not None
    assert receipt.normalized_usage.extras["provider_cost_status"] == "unknown"
    assert "provider_cost_usd" not in receipt.normalized_usage.extras


@pytest.mark.asyncio
async def test_rate_limit_error_preserves_safe_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_client(
        monkeypatch,
        lambda request: httpx.Response(
            429,
            json={"error": "rate limited"},
            headers={"retry-after": "2", "x-ratelimit-remaining-requests": "0"},
        ),
    )
    adapter = GroqAdapter(
        mode="live", secret_ref_names=[], pinned_model_id="openai/gpt-oss-20b"
    )
    route = (await adapter.discover())[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.error_class == ErrorClass.RATE_LIMIT
    assert receipt.normalized_usage is not None
    assert receipt.normalized_usage.extras["rate_limit_headers"] == {
        "retry-after": "2",
        "x-ratelimit-remaining-requests": "0",
    }
