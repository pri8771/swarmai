"""OpenRouter free-route allowlist and live canary admission (offline)."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from swarm.contracts.enums import AvailabilityStatus
from swarm.contracts.provider import InferenceRequest
from swarm.onboarding.canary import CanaryDeniedError, bounded_canary
from swarm.providers.core.adapters import OpenRouterAdapter, OpenRouterFreeRoute
from swarm.providers.openrouter_free import (
    OPENROUTER_FREE_ROUTE_ALLOWLIST,
    is_openrouter_free_model_id,
    openrouter_free_route_ids,
    resolve_openrouter_free_route,
)
from tests.providers.core.test_core_adapters import _reservation


def test_allowlist_contains_pinned_zero_price_qwen_free() -> None:
    assert "qwen/qwen3.8-27b:free" in OPENROUTER_FREE_ROUTE_ALLOWLIST
    spec = OPENROUTER_FREE_ROUTE_ALLOWLIST["qwen/qwen3.8-27b:free"]
    assert spec.provider_slug == "modelrun"
    assert spec.route_id == "rt_openrouter_qwen/qwen3.8-27b:free"
    assert is_openrouter_free_model_id("qwen/qwen3.8-27b:free")
    assert not is_openrouter_free_model_id("openrouter/auto")
    assert not is_openrouter_free_model_id("some/other:free")


def test_resolve_openrouter_free_route_fail_closed() -> None:
    assert resolve_openrouter_free_route("rt_openrouter_qwen/qwen3.8-27b:free") is not None
    assert resolve_openrouter_free_route("rt_openrouter_default") is None
    assert resolve_openrouter_free_route("rt_openrouter_openrouter/auto") is None
    assert resolve_openrouter_free_route("rt_openrouter_meta-llama/llama-3.2-3b-instruct:free") is None
    assert resolve_openrouter_free_route("rt_groq_default") is None
    assert "rt_openrouter_qwen/qwen3.8-27b:free" in openrouter_free_route_ids()


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
        await adapter.execute_one(
            InferenceRequest(
                project_id="proj_or",
                attempt_id="att_1",
                purpose="wire",
                messages=[{"role": "user", "content": "OK"}],
                max_output_tokens=8,
            ),
            _reservation(route.route_id),
        )
    assert calls == []


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
    free = OpenRouterFreeRoute(model_id="qwen/qwen3.8-27b:free", provider_slug="modelrun")
    adapter = OpenRouterAdapter(
        mode="live",
        enabled=True,
        secret_ref_names=[],
        free_route=free,
    )
    route = (await adapter.discover())[0]
    assert route.model_id == "qwen/qwen3.8-27b:free"
    assert route.hosted_by == "modelrun"
    assert route.route_id == free.route_id
    await adapter.execute_one(
        InferenceRequest(
            project_id="proj_or",
            attempt_id="att_1",
            purpose="wire",
            messages=[{"role": "user", "content": "Reply OK"}],
            max_output_tokens=32,
        ),
        _reservation(route.route_id),
    )
    assert len(sent) == 1
    assert sent[0]["provider"] == {
        "only": ["modelrun"],
        "allow_fallbacks": False,
        "max_price": {"prompt": 0, "completion": 0},
        "require_parameters": True,
    }


@pytest.mark.asyncio
async def test_canary_non_free_openrouter_denied_with_billing_flag() -> None:
    denied = await bounded_canary(
        route_id="rt_openrouter_openrouter/auto",
        mode="live",
        billing_known_zero=True,
    )
    assert denied["denied"] is True
    assert denied["reason"] == "openrouter_route_not_on_free_allowlist"
    assert denied["mock_vs_live"] == "not_live"


@pytest.mark.asyncio
async def test_canary_non_allowlisted_free_suffix_still_denied() -> None:
    denied = await bounded_canary(
        route_id="rt_openrouter_meta-llama/llama-3.2-3b-instruct:free",
        mode="live",
        billing_known_zero=True,
    )
    assert denied["denied"] is True
    assert denied["reason"] == "openrouter_route_not_on_free_allowlist"


@pytest.mark.asyncio
async def test_canary_paid_flag_still_blocks_free_route() -> None:
    with pytest.raises(CanaryDeniedError, match="paid_routes_denied"):
        await bounded_canary(
            route_id="rt_openrouter_qwen/qwen3.8-27b:free",
            mode="live",
            billing_known_zero=True,
            allow_paid=True,
        )


@pytest.mark.asyncio
async def test_canary_free_route_admitted_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-a-real-key-value")
    monkeypatch.setenv("SWARM_ALLOW_PAID", "false")

    async def _fake_live(**kwargs: Any) -> dict[str, Any]:
        return {
            "route_id": "rt_openrouter_qwen/qwen3.8-27b:free",
            "provider_id": "openrouter",
            "model_id": "qwen/qwen3.8-27b:free",
            "status": "canaried",
            "denied": False,
            "cost_usd": 0.0,
            "secret_ref_names": ["OPENROUTER_API_KEY"],
            "mock_vs_live": "live_remote_zero_cost",
            "billing_known_zero": True,
            "consumed_allowance": 1,
        }

    with patch(
        "swarm.onboarding.canary._live_openrouter_free_canary",
        new=AsyncMock(side_effect=_fake_live),
    ) as mocked:
        result = await bounded_canary(
            route_id="rt_openrouter_qwen/qwen3.8-27b:free",
            mode="live",
            billing_known_zero=True,
        )
    assert result["denied"] is False
    assert result["cost_usd"] == 0.0
    assert result["secret_ref_names"] == ["OPENROUTER_API_KEY"]
    assert "sk-test" not in json.dumps(result)
    mocked.assert_awaited_once()


@pytest.mark.asyncio
async def test_canary_free_route_missing_key_user_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    # Ensure dotenv cannot resurrect a key from a missing/empty .env in tests.
    with patch("swarm.onboarding.canary.load_repo_dotenv", return_value=0):
        denied = await bounded_canary(
            route_id="rt_openrouter_qwen/qwen3.8-27b:free",
            mode="live",
            billing_known_zero=True,
        )
    assert denied["denied"] is True
    assert denied["reason"] == "missing_OPENROUTER_API_KEY"
    assert any("USER_ACTION" in a for a in denied["user_action_required"])
    assert denied["secret_ref_names"] == ["OPENROUTER_API_KEY"]
    blob = json.dumps(denied)
    assert "sk-" not in blob


@pytest.mark.asyncio
async def test_groq_still_denied_even_with_billing_flag() -> None:
    denied = await bounded_canary(
        route_id="rt_groq_default",
        mode="live",
        billing_known_zero=True,
    )
    assert denied["denied"] is True
    assert denied["mock_vs_live"] == "not_live"
