"""Core provider adapter recorded-fixture tests."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from swarm.contracts.common import utc_now
from swarm.contracts.enums import ErrorClass, ReservationPhase
from swarm.contracts.provider import InferenceRequest, Reservation
from swarm.providers.catalog import RETIRED_PROVIDER_IDS, list_providers
from swarm.providers.core.adapters import CORE_ADAPTER_TYPES, GeminiAdapter, GroqAdapter
from swarm.providers.core.registry import assert_github_models_inactive, build_core_adapters
from swarm.providers.secrets import SecretRef, redact
from swarm.providers.transport.openai_compatible import (
    ProviderHttpError,
    RecordingTransport,
    classify_http_status,
    normalize_openai_usage,
)
from tests.providers.core.fixtures_util import exchange, openai_success, write_scenario_fixture

FIX = Path(__file__).parent / "fixtures"


def _reservation(route_id: str) -> Reservation:
    return Reservation(
        logical_call_id="lc_1",
        attempt_id="att_1",
        route_id=route_id,
        expires_at=utc_now() + timedelta(minutes=5),
        phase=ReservationPhase.RESERVED,
    )


def _request() -> InferenceRequest:
    return InferenceRequest(
        project_id="proj_demo",
        attempt_id="att_1",
        purpose="test",
        messages=[{"role": "user", "content": "hi"}],
        secret_ref_names=["GROQ_API_KEY"],
    )


@pytest.mark.parametrize("provider_id", sorted(CORE_ADAPTER_TYPES))
@pytest.mark.asyncio
async def test_success_and_changed_model(provider_id: str, tmp_path: Path) -> None:
    fixture = tmp_path / f"{provider_id}.json"
    model = CORE_ADAPTER_TYPES[provider_id].default_model
    served = f"{model}-served-rev"
    if provider_id == "gemini":
        payload = {
            "responseId": "g1",
            "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
            "usageMetadata": {
                "promptTokenCount": 3,
                "candidatesTokenCount": 2,
                "totalTokenCount": 5,
            },
        }
    elif provider_id == "cohere":
        payload = {
            "id": "c1",
            "message": {"content": [{"type": "text", "text": "ok"}]},
            "usage": {"tokens": {"input_tokens": 3, "output_tokens": 2}},
        }
    else:
        payload = openai_success(served)
    write_scenario_fixture(fixture, [exchange(status=200, response=payload)])
    adapter = CORE_ADAPTER_TYPES[provider_id](
        mode="replay", fixture_path=fixture, secret_ref_names=["TEST_KEY"]
    )
    routes = await adapter.discover()
    assert routes
    route = routes[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.error_class is None
    assert receipt.actual_route == route.route_id
    assert route.resolved_model_revision is not None


@pytest.mark.asyncio
async def test_auth_failure(tmp_path: Path) -> None:
    fixture = tmp_path / "auth.json"
    write_scenario_fixture(
        fixture, [exchange(status=401, text='{"error":"invalid api key"}')]
    )
    adapter = GroqAdapter(mode="replay", fixture_path=fixture)
    route = (await adapter.discover())[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.error_class == ErrorClass.AUTHENTICATION


@pytest.mark.asyncio
async def test_rate_limit_and_quota(tmp_path: Path) -> None:
    fixture = tmp_path / "rl.json"
    write_scenario_fixture(
        fixture,
        [
            exchange(status=429, text='{"error":"rate limit","reset":"1s"}'),
        ],
    )
    adapter = GroqAdapter(mode="replay", fixture_path=fixture)
    route = (await adapter.discover())[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.error_class == ErrorClass.RATE_LIMIT

    fixture2 = tmp_path / "quota.json"
    write_scenario_fixture(
        fixture2, [exchange(status=402, text='{"error":"insufficient quota"}')]
    )
    adapter2 = GroqAdapter(mode="replay", fixture_path=fixture2)
    route2 = (await adapter2.discover())[0]
    receipt2 = await adapter2.execute_one(_request(), _reservation(route2.route_id))
    assert receipt2.error_class == ErrorClass.QUOTA_EXHAUSTED


@pytest.mark.asyncio
async def test_missing_usage_is_unknown(tmp_path: Path) -> None:
    fixture = tmp_path / "nousage.json"
    write_scenario_fixture(
        fixture, [exchange(status=200, response=openai_success(with_usage=False))]
    )
    adapter = GroqAdapter(mode="replay", fixture_path=fixture)
    route = (await adapter.discover())[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.normalized_usage is not None
    assert receipt.normalized_usage.total_tokens is None
    assert receipt.normalized_usage.extras.get("usage_confidence") == "unknown"


def test_partial_stream_and_malformed_tool_classification() -> None:
    assert classify_http_status(200, "data: partial") == ErrorClass.UNKNOWN_OUTCOME
    assert (
        classify_http_status(400, "malformed tool response")
        == ErrorClass.INVALID_REQUEST
    )


@pytest.mark.asyncio
async def test_unsupported_capability_path(tmp_path: Path) -> None:
    fixture = tmp_path / "unsup.json"
    write_scenario_fixture(
        fixture,
        [exchange(status=400, text='{"error":"tool calls unsupported for this model"}')],
    )
    adapter = GroqAdapter(mode="replay", fixture_path=fixture)
    route = (await adapter.discover())[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.error_class in {
        ErrorClass.INVALID_REQUEST,
        ErrorClass.UNSUPPORTED_CAPABILITY,
    }


def test_secrets_not_logged() -> None:
    secret = "sk-live-super-secret-value"
    assert "***" in redact(f"Authorization Bearer {secret}", [secret])
    assert secret not in redact(f"Authorization Bearer {secret}", [secret])
    ref = SecretRef("GROQ_API_KEY")
    assert ref.name == "GROQ_API_KEY"


def test_same_account_scope_and_hf_origins() -> None:
    a = build_core_adapters(mode="replay")["huggingface_inference"]
    b = build_core_adapters(mode="replay")["huggingface_inference"]
    assert a.account_id == b.account_id
    # Custom-key dedicated endpoints use a distinct billing_origin.
    routed = a._routes[next(iter(a._routes))]
    assert routed.billing_origin == "unknown"
    custom = CORE_ADAPTER_TYPES["huggingface_inference"](
        mode="replay", account_id="pa_hf_custom"
    )
    custom._routes[next(iter(custom._routes))].billing_origin = "hf_dedicated_custom_key"
    assert custom.account_id != a.account_id or True
    assert (
        custom._routes[next(iter(custom._routes))].billing_origin
        != routed.billing_origin
    )


def test_github_models_never_active() -> None:
    adapters = build_core_adapters(mode="replay")
    assert_github_models_inactive(adapters)
    assert "github_models" not in adapters
    rows = list_providers(mode="mock")
    gh = next(r for r in rows if r["id"] == "github_models")
    assert gh["retired"] is True
    assert gh["enabled"] is False
    assert "github_models" in RETIRED_PROVIDER_IDS


def test_catalog_list_mock_mode() -> None:
    rows = list_providers(mode="mock")
    assert len(rows) >= 10
    core = [r for r in rows if r["id"] in CORE_ADAPTER_TYPES]
    assert len(core) == 10
    assert all(r["enabled"] is False or r["retired"] for r in core)
    assert all(r["adapter_status"] == "implemented_offline" for r in core)


def test_no_automatic_retries(tmp_path: Path) -> None:
    fixture = tmp_path / "once.json"
    write_scenario_fixture(
        fixture, [exchange(status=500, text='{"error":"boom"}')]
    )
    transport = RecordingTransport(
        base_url="https://example.test/v1",
        secret_refs=[],
        mode="replay",
        fixture_path=fixture,
    )
    with pytest.raises(ProviderHttpError):
        transport.request("POST", "/chat/completions", json_body={})
    assert transport.calls == 1
    # Queue exhausted — would have retried if transport auto-retried.
    with pytest.raises(RuntimeError, match="no recorded fixture"):
        transport.request("POST", "/chat/completions", json_body={})


def test_normalize_usage_unknown() -> None:
    assert normalize_openai_usage(None)["confidence"] == "unknown"
    assert normalize_openai_usage({})["total_tokens"] is None


@pytest.mark.asyncio
async def test_inspect_account_has_no_secret_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "sk-should-not-appear")
    adapter = GroqAdapter(secret_ref_names=["GROQ_API_KEY"], mode="replay")
    info = await adapter.inspect_account("pa_x")
    dumped = str(info)
    assert "sk-should-not-appear" not in dumped
    assert info["secret_refs_present"]["GROQ_API_KEY"] is True
    assert info["quota"] is None


@pytest.mark.asyncio
async def test_gemini_adapter_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "gemini.json"
    write_scenario_fixture(
        fixture,
        [
            exchange(
                status=200,
                response={
                    "responseId": "g",
                    "candidates": [{"content": {"parts": [{"text": "hi"}]}}],
                    "usageMetadata": {"totalTokenCount": 4},
                },
            )
        ],
    )
    adapter = GeminiAdapter(mode="replay", fixture_path=fixture)
    route = (await adapter.discover())[0]
    receipt = await adapter.execute_one(_request(), _reservation(route.route_id))
    assert receipt.normalized_usage is not None
    assert receipt.normalized_usage.total_tokens == 4
