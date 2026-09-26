"""SW-W1-S11 / P05: RouterClient against the offline fake router."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.contracts.enums import ErrorClass
from swarm.contracts.router_capabilities import RouteBilling, classify_error
from swarm.providers.router_client import RouterClient, RouterClientError, load_overrides
from tests.fixtures.router_http.fake_router import FakeRouter

BASE = "http://router.invalid"
MSG = {"model": "fake-free", "messages": [{"role": "user", "content": "hi"}]}


def _client(scenario: str, **kw: object) -> tuple[RouterClient, FakeRouter]:
    fake = FakeRouter(scenario)
    return RouterClient(BASE, transport=fake.transport, **kw), fake  # type: ignore[arg-type]


def test_list_models_billing_and_admission() -> None:
    client, _ = _client("ok")
    caps = {c.model_id: c for c in client.list_models()}
    assert caps["fake-free"].billing == RouteBilling.FREE
    assert caps["fake-free"].admissible(needs_tools=True) == (True, None)
    assert caps["fake-paid"].admissible() == (False, "paid_route_forbidden")
    # Alias billing is not stated by the router: unknown is never free.
    assert caps["fast"].admissible() == (False, "paid_route_forbidden")


def test_overrides_fill_missing_metadata_but_never_billing(tmp_path: Path) -> None:
    path = tmp_path / "o.json"
    path.write_text(
        json.dumps({"models": {"fake-free": {"context_window": 8192, "billing": "free"},
                               "fast": {"billing": "free"}}}),
        encoding="utf-8",
    )
    client, _ = _client("ok", overrides=load_overrides(path))
    caps = {c.model_id: c for c in client.list_models()}
    assert caps["fake-free"].context_window == 8192
    assert caps["fake-free"].metadata_source == "override"
    assert caps["fast"].billing == RouteBilling.UNKNOWN
    assert caps["fake-free"].admissible(min_context=16000) == (False, "context_window_too_small")


def test_chat_ok_receipt_from_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWARM_ROUTER_API_KEY", "fake-key-not-secret")
    client, fake = _client("ok")
    result = client.chat(MSG)
    assert result.message["content"] == "hello"
    r = result.receipt
    assert (r.request_id, r.route_id, r.billing) == ("req_fake_1", "fake-free", RouteBilling.FREE)
    assert r.usage_known and r.prompt_tokens == 11 and r.attempts == ["fake-free=ok"]
    assert fake.requests[-1]["has_auth"] is True
    assert fake.requests[-1]["body"]["stream"] is False


def test_missing_usage_is_unknown_not_zero() -> None:
    client, _ = _client("missing_usage")
    r = client.chat(MSG).receipt
    assert r.usage_known is False and r.prompt_tokens is None


def test_paid_route_refused() -> None:
    client, _ = _client("paid")
    with pytest.raises(RouterClientError) as err:
        client.chat(MSG)
    assert err.value.code == "paid_route_forbidden"
    assert err.value.error_class == ErrorClass.POLICY_DENIED


@pytest.mark.parametrize(
    ("scenario", "error_class", "code"),
    [
        ("rate_limited", ErrorClass.RATE_LIMIT, "upstream_rate_limited"),
        ("unavailable", ErrorClass.TRANSIENT, "upstream_unavailable"),
        ("malformed", ErrorClass.UNKNOWN_OUTCOME, "malformed_response"),
        ("timeout", ErrorClass.UNKNOWN_OUTCOME, "timeout"),
    ],
)
def test_errors_classified_without_retry(scenario: str, error_class: ErrorClass, code: str) -> None:
    client, fake = _client(scenario)
    with pytest.raises(RouterClientError) as err:
        client.chat(MSG)
    assert (err.value.error_class, err.value.code) == (error_class, code)
    assert len(fake.requests) == 1
    if scenario == "rate_limited":
        assert err.value.receipt is not None and err.value.receipt.retry_after_s == 7.0


def test_stream_complete_and_partial() -> None:
    client, _ = _client("stream")
    result = client.chat_stream(MSG)
    assert result.text == "hello" and result.receipt.usage_known
    partial, _ = _client("partial_stream")
    with pytest.raises(RouterClientError) as err:
        partial.chat_stream(MSG)
    assert err.value.error_class == ErrorClass.PARTIAL_STREAM
    assert err.value.partial_text == "hello"


def test_tool_call_roundtrip_shape() -> None:
    client, _ = _client("tools")
    first = client.chat(MSG)
    call = first.message["tool_calls"][0]
    assert call["id"] == "call_1" and call["function"]["name"] == "workspace.read"
    follow = {
        **MSG,
        "messages": [*MSG["messages"], first.message,
                     {"role": "tool", "tool_call_id": "call_1", "content": "ok"}],
    }
    assert client.chat(follow).message["content"] == "done after tool"


def test_classify_error_table() -> None:
    assert classify_error(401, None)[0] == ErrorClass.AUTHENTICATION
    assert classify_error(404, {"error": {"code": "unknown_model"}})[0] == (
        ErrorClass.UNSUPPORTED_CAPABILITY
    )
    assert classify_error(502, {"error": {"code": "upstream_payment_required"}})[0] == (
        ErrorClass.QUOTA_EXHAUSTED
    )
    assert classify_error(504, {"error": {"code": "deadline_exceeded"}})[0] == (
        ErrorClass.UNKNOWN_OUTCOME
    )
    assert classify_error(400, {"error": {"code": "invalid_request"}})[0] == (
        ErrorClass.INVALID_REQUEST
    )
