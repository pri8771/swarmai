"""Groq live route selection is explicit and has no discovery HTTP side effect."""

from __future__ import annotations

import httpx
import pytest

from swarm.contracts.enums import AvailabilityStatus
from swarm.contracts.provider import InferenceRequest
from swarm.providers.core.adapters import GroqAdapter
from tests.providers.core.test_core_adapters import _reservation


@pytest.mark.asyncio
async def test_live_groq_needs_pinned_model_without_metadata_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"usage": {}})

    original = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    unpinned = GroqAdapter(mode="live", enabled=True, secret_ref_names=[])
    route = (await unpinned.discover())[0]
    assert route.availability_status == AvailabilityStatus.DISABLED
    assert calls == []
    request = InferenceRequest(
        project_id="test",
        attempt_id="attempt",
        route_id=route.route_id,
        purpose="probe",
        messages=[{"role": "user", "content": "brief"}],
        max_output_tokens=8,
    )
    with pytest.raises(ValueError, match="exact pinned model"):
        await unpinned.execute_one(request, _reservation(route.route_id))
    assert calls == []


@pytest.mark.asyncio
async def test_groq_pinned_model_and_output_bound_before_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json={"id": "offline", "usage": {"cost": 0}})

    original = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    adapter = GroqAdapter(
        mode="live", enabled=True, secret_ref_names=[], pinned_model_id="openai/gpt-oss-20b"
    )
    route = (await adapter.discover())[0]
    assert route.model_id == "openai/gpt-oss-20b"
    assert sent == []
    request = InferenceRequest(
        project_id="test",
        attempt_id="attempt",
        route_id=route.route_id,
        purpose="probe",
        messages=[{"role": "user", "content": "brief"}],
        max_output_tokens=8,
    )
    await adapter.execute_one(request, _reservation(route.route_id))
    assert len(sent) == 1
    assert sent[0].url.path.endswith("/chat/completions")
    assert b'"max_completion_tokens":8' in sent[0].content
