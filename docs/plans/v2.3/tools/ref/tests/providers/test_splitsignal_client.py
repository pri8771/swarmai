from __future__ import annotations

import pytest

from swarm.contracts.enums import ErrorClass
from swarm.contracts.router_capabilities import RouteBilling
from swarm.providers.router_client import RouterClientError
from swarm.providers.splitsignal_client import (
    SplitSignalClient,
    SplitSignalReceipt,
    classify_splitsignal_error,
)
from tests.fixtures.splitsignal_http.fake_splitsignal import (
    MODEL_PAGE,
    REQUEST_ID,
    SYNTHETIC_KEY,
    FakeSplitSignal,
    error_envelope,
)

BASE = "http://splitsignal.test/v1"


@pytest.fixture
def key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPLITSIGNAL_API_KEY", SYNTHETIC_KEY)


def client(fake: FakeSplitSignal) -> SplitSignalClient:
    return SplitSignalClient(BASE, transport=fake.transport())


def test_base_url_v1_suffix_not_doubled(key: None) -> None:
    fake = FakeSplitSignal()
    client(fake).list_models()
    assert fake.requests[0].url.path == "/v1/models"
    assert fake.requests[0].headers["authorization"] == f"Bearer {SYNTHETIC_KEY}"


def test_v1_model_list_routes_are_free_and_admissible(key: None) -> None:
    models = client(FakeSplitSignal()).list_models()
    assert [m.model_id for m in models] == ["mock/ok", "mock/quota", "mock/unavailable"]
    assert all(m.billing == RouteBilling.FREE for m in models)
    assert models[0].admissible() == (True, None)


def test_model_page_cost_class_is_authoritative(key: None) -> None:
    ok, trial = client(FakeSplitSignal(models_body=MODEL_PAGE)).list_models()
    assert ok.billing == RouteBilling.FREE and ok.context_window == 131072
    assert ok.supports_tools is True and ok.supports_json is False
    assert ok.max_output_tokens is None
    assert trial.billing == RouteBilling.TRIAL
    assert trial.admissible() == (False, "paid_route_forbidden")
    assert trial.admissible(needs_tools=True)[0] is False


def test_missing_key_is_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SPLITSIGNAL_API_KEY", raising=False)
    with pytest.raises(RouterClientError) as exc:
        client(FakeSplitSignal()).list_models()
    assert exc.value.error_class == ErrorClass.AUTHENTICATION
    assert exc.value.code == "unauthenticated"


def test_chat_success_receipt(key: None) -> None:
    result = client(FakeSplitSignal()).chat(
        {"model": "mock/ok", "messages": [{"role": "user", "content": "hi"}]}
    )
    assert result.message["content"] == "Hello from mock."
    r = result.receipt
    assert r.request_id == REQUEST_ID
    assert r.route_id == "mock/ok" and r.provider == "mock" and r.upstream_model == "ok"
    assert r.billing == RouteBilling.FREE
    assert r.usage_known and (r.prompt_tokens, r.completion_tokens) == (12, 5)
    assert r.attempts == ["mock/ok"]
    assert (r.cost_amount, r.cost_currency, r.cost_source) == ("0", "USD", "reported")


def test_chat_unknown_usage_stays_unknown(key: None) -> None:
    r = client(FakeSplitSignal()).chat({"model": "mock/nousage", "messages": []}).receipt
    assert isinstance(r, SplitSignalReceipt)
    assert r.usage_known is False
    assert r.prompt_tokens is None and r.completion_tokens is None
    assert r.cost_amount is None and r.cost_source == "unknown"
    assert r.billing == RouteBilling.FREE


def test_chat_unknown_cost_never_settles_as_zero(key: None) -> None:
    r = client(FakeSplitSignal()).chat({"model": "mock/nocost", "messages": []}).receipt
    assert isinstance(r, SplitSignalReceipt)
    assert (r.prompt_tokens, r.completion_tokens) == (12, 5)
    assert r.cost_amount is None and r.cost_currency is None and r.cost_source == "unknown"
    assert r.usage_known is False
    assert r.billing == RouteBilling.FREE


def test_chat_known_nonzero_cost_is_refused(key: None) -> None:
    with pytest.raises(RouterClientError) as exc:
        client(FakeSplitSignal()).chat({"model": "mock/paid", "messages": []})
    assert exc.value.code == "paid_route_forbidden"
    assert exc.value.receipt is not None
    assert exc.value.receipt.billing == RouteBilling.PAID


def test_chat_paid_allowed_when_require_free_off(key: None) -> None:
    c = SplitSignalClient(BASE, transport=FakeSplitSignal().transport(), require_free=False)
    assert c.chat({"model": "mock/paid", "messages": []}).receipt.billing == RouteBilling.PAID


@pytest.mark.parametrize(
    ("model", "cls", "code", "retry_after"),
    [
        ("mock/quota", ErrorClass.QUOTA_EXHAUSTED, "quota_exhausted", 30.0),
        ("mock/unavailable", ErrorClass.TRANSIENT, "provider_unavailable", 5.0),
        ("mock/lost", ErrorClass.UNKNOWN_OUTCOME, "invalid_provider_response", None),
        ("mock/nope", ErrorClass.INVALID_REQUEST, "invalid_request", None),
    ],
)
def test_chat_errors(
    key: None, model: str, cls: ErrorClass, code: str, retry_after: float | None
) -> None:
    fake = FakeSplitSignal()
    with pytest.raises(RouterClientError) as exc:
        client(fake).chat({"model": model, "messages": []})
    assert exc.value.error_class == cls and exc.value.code == code
    assert exc.value.receipt is not None
    assert exc.value.receipt.retry_after_s == retry_after
    assert len(fake.requests) == 1


def test_stream_success_uses_finish_and_usage_chunks(key: None) -> None:
    result = client(FakeSplitSignal()).chat_stream({"model": "mock/ok", "messages": []})
    assert result.text == "Hello stream."
    r = result.receipt
    assert r.route_id == "mock/ok" and r.request_id == REQUEST_ID
    assert r.billing == RouteBilling.FREE
    assert (r.prompt_tokens, r.completion_tokens) == (12, 2)
    assert r.usage_known is True and r.cost_amount == "0"


def test_stream_error_event_is_partial_stream(key: None) -> None:
    with pytest.raises(RouterClientError) as exc:
        client(FakeSplitSignal()).chat_stream({"model": "mock/broken", "messages": []})
    assert exc.value.error_class == ErrorClass.PARTIAL_STREAM
    assert exc.value.partial_text == "Hello "


@pytest.mark.parametrize(
    ("status", "code", "retryable", "cls"),
    [
        (403, "forbidden", False, ErrorClass.POLICY_DENIED),
        (429, "provider_rate_limited", True, ErrorClass.RATE_LIMIT),
        (422, "no_eligible_route", False, ErrorClass.UNSUPPORTED_CAPABILITY),
        (503, "temporarily_unavailable", True, ErrorClass.TRANSIENT),
        (500, "internal_error", False, ErrorClass.UNKNOWN_OUTCOME),
        (504, "deadline_exceeded", False, ErrorClass.UNKNOWN_OUTCOME),
        (409, "request_in_progress", False, ErrorClass.UNKNOWN_OUTCOME),
    ],
)
def test_classify(status: int, code: str, retryable: bool, cls: ErrorClass) -> None:
    got = classify_splitsignal_error(status, error_envelope(code, retryable=retryable))
    assert got == (cls, code, retryable)


def test_classify_non_json_body() -> None:
    assert classify_splitsignal_error(502, None) == (
        ErrorClass.UNKNOWN_OUTCOME,
        "unknown_error",
        False,
    )
