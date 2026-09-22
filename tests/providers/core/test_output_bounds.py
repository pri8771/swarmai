"""Wire-level regression for the broker's requested output bound (no sockets)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from swarm.contracts.provider import InferenceRequest
from swarm.providers.core.adapters import CORE_ADAPTER_TYPES, OpenRouterFreeRoute
from tests.providers.core.test_core_adapters import _reservation


@pytest.mark.parametrize("provider_id", sorted(CORE_ADAPTER_TYPES))
@pytest.mark.parametrize("bound", [None, 32])
@pytest.mark.asyncio
async def test_core_output_limit_reaches_http_body(
    provider_id: str, bound: int | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"id": "offline-bound-check", "usage": {}})

    client_type = httpx.Client

    def client(**kwargs: Any) -> httpx.Client:
        return client_type(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "Client", client)
    options: dict[str, Any] = {}
    if provider_id == "openrouter":
        options["free_route"] = OpenRouterFreeRoute(
            model_id="qwen/qwen3.8-27b:free", provider_slug="modelrun"
        )
    adapter = CORE_ADAPTER_TYPES[provider_id](
        mode="live", base_url="https://provider.invalid/v1", secret_ref_names=[], **options
    )
    route_id = f"rt_{provider_id}_default"
    request = InferenceRequest(
        project_id="proj_output_bound",
        attempt_id="att_1",
        purpose="offline-wire-regression",
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        max_output_tokens=bound,
    )
    if provider_id == "openrouter" and bound is None:
        with pytest.raises(ValueError, match="finite output limit"):
            await adapter.execute_one(request, _reservation(route_id))
        assert sent == []
        return
    await adapter.execute_one(request, _reservation(route_id))
    assert len(sent) == 1
    body = sent[0]
    if provider_id == "gemini":
        observed = body.get("generationConfig", {}).get("maxOutputTokens")
    elif provider_id == "groq":
        observed = body.get("max_completion_tokens")
        assert "max_tokens" not in body
    else:
        observed = body.get("max_tokens")
    assert observed == bound
    if bound is None:
        assert "max_tokens" not in body
        assert "max_completion_tokens" not in body
        assert "generationConfig" not in body


@pytest.mark.parametrize("invalid", [0, -1, True, False, 1.5, "32"])
def test_invalid_output_limits_rejected(invalid: object) -> None:
    with pytest.raises(ValidationError):
        InferenceRequest.model_validate(
            {
                "project_id": "proj_output_bound",
                "attempt_id": "att_1",
                "purpose": "offline-wire-regression",
                "messages": [{"role": "user", "content": "OK"}],
                "max_output_tokens": invalid,
            }
        )
