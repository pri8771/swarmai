"""Offline fake of the SplitSignal consumer surface (contract ``swarmai-consumer 1.x``).

Bodies follow inference_server ``docs/api/v1/openapi.yaml`` (``V1ModelList``,
``ModelPage``, ``ChatCompletion``, ``ChatCompletionChunk``, ``ErrorEnvelope``)
and mirror ``scripts/mock_splitsignal.py``: ``mock/ok`` succeeds, ``mock/quota``
is 429, ``mock/unavailable`` is 503. ``mock/paid`` reports a non-zero cost and
``mock/nousage`` reports no usage and no cost; ``mock/nocost`` reports
tokens but no cost. All keys and ids are synthetic.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

SYNTHETIC_KEY = "ss_live_00000000000000000000000000000000_" + "A" * 43
REQUEST_ID = "00000000-0000-4000-8000-000000000001"
CREATED = 1790000000

MODELS_V1: dict[str, Any] = {
    "object": "list",
    "data": [
        {"id": "mock/ok", "object": "model", "created": CREATED, "owned_by": "mock"},
        {"id": "mock/quota", "object": "model", "created": CREATED, "owned_by": "mock"},
        {"id": "mock/unavailable", "object": "model", "created": CREATED, "owned_by": "mock"},
    ],
}


def _limit(value: int | None) -> dict[str, Any]:
    if value is None:
        return {"value": None, "source": "unknown", "observed_at": None}
    return {"value": value, "source": "provider_catalog", "observed_at": "2026-09-25T00:00:00Z"}


def offer(route_id: str, cost_class: str, *, tools: str = "supported") -> dict[str, Any]:
    """The ModelOffer fields SwarmAI reads (the full schema has more required fields)."""
    return {
        "route_id": route_id,
        "cost_class": cost_class,
        "capabilities": {
            "chat": "supported",
            "stream": "supported",
            "tools": tools,
            "json_output": "unknown",
            "vision": "unsupported",
        },
        "limits": {"context_window": _limit(131072), "max_output_tokens": _limit(None)},
    }


MODEL_PAGE: dict[str, Any] = {
    "items": [offer("mock/ok", "free"), offer("mock/trial", "trial", tools="unknown")],
    "next_cursor": None,
}


def _meta(route: str, amount: str | None, usage_known: bool = True) -> dict[str, Any]:
    tokens = (12, 5) if usage_known else (None, None)
    return {
        "request_id": REQUEST_ID,
        "requested_route": route,
        "served_route": route,
        "attempt_count": 1,
        "outcome": "answered",
        "usage": {
            "input_tokens": tokens[0],
            "output_tokens": tokens[1],
            "reasoning_tokens": None,
            "cached_tokens": None,
            "source": "reported" if usage_known else "unknown",
        },
        "cost": (
            {"amount": amount, "currency": "USD", "source": "reported"}
            if amount is not None
            else {"amount": None, "currency": None, "source": "unknown"}
        ),
    }


def chat_success(
    route: str = "mock/ok", *, amount: str | None = "0", usage_known: bool = True
) -> dict[str, Any]:
    usage = (
        {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17} if usage_known else None
    )
    return {
        "id": REQUEST_ID,
        "object": "chat.completion",
        "created": CREATED,
        "model": route,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello from mock."},
                "finish_reason": "stop",
            }
        ],
        "usage": usage,
        "splitsignal": _meta(route, amount, usage_known),
    }


def _chunk(route: str, **kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": REQUEST_ID,
        "object": "chat.completion.chunk",
        "created": CREATED,
        "model": route,
    }
    base.update(kw)
    return base


def stream_chunks(route: str = "mock/ok") -> list[dict[str, Any]]:
    return [
        _chunk(
            route,
            choices=[
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": "Hello "},
                    "finish_reason": None,
                }
            ],
        ),
        _chunk(
            route, choices=[{"index": 0, "delta": {"content": "stream."}, "finish_reason": None}]
        ),
        _chunk(
            route,
            choices=[{"index": 0, "delta": {}, "finish_reason": "stop"}],
            splitsignal=_meta(route, "0"),
        ),
        _chunk(
            route,
            choices=[],
            usage={"prompt_tokens": 12, "completion_tokens": 2, "total_tokens": 14},
        ),
    ]


def error_envelope(code: str, *, retryable: bool = False, **extra: Any) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": "Safe fixed message.",
            "request_id": REQUEST_ID,
            "retryable": retryable,
            **extra,
        }
    }


RATE_HEADERS = {
    "x-ratelimit-limit-requests": "60",
    "x-ratelimit-remaining-requests": "59",
    "x-ratelimit-reset-requests": "1m0s",
    "x-ratelimit-limit-tokens": "100000",
    "x-ratelimit-remaining-tokens": "99936",
    "x-ratelimit-reset-tokens": "24h0m0s",
}


class FakeSplitSignal:
    """httpx transport handler; ``models_body`` switches V1ModelList / ModelPage."""

    def __init__(self, *, models_body: dict[str, Any] | None = None) -> None:
        self.models_body = models_body if models_body is not None else MODELS_V1
        self.requests: list[httpx.Request] = []

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)

    def _json(self, status: int, body: Any, **headers: str) -> httpx.Response:
        h = {"x-request-id": REQUEST_ID, "cache-control": "no-store", **headers}
        if status >= 400:
            h["x-should-retry"] = "false"
        return httpx.Response(status, json=body, headers=h)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.headers.get("authorization") != f"Bearer {SYNTHETIC_KEY}":
            return self._json(401, error_envelope("unauthenticated"))
        path = request.url.path
        if request.method == "GET" and path == "/v1/models":
            return self._json(200, self.models_body)
        if request.method != "POST" or path != "/v1/chat/completions":
            return self._json(404, error_envelope("not_found"))
        try:
            body = json.loads(request.content or b"{}")
        except ValueError:
            body = {}
        model = body.get("model") if isinstance(body, dict) else None
        if model == "mock/quota":
            return self._json(
                429,
                error_envelope("quota_exhausted", retryable=True, retry_after_s=30),
                **{"retry-after": "30"},
                **RATE_HEADERS,
            )
        if model == "mock/unavailable":
            return self._json(
                503,
                error_envelope("provider_unavailable", retryable=True, retry_after_s=5),
                **{"retry-after": "5"},
            )
        if model == "mock/lost":
            return self._json(502, error_envelope("invalid_provider_response"))
        if model not in {"mock/ok", "mock/paid", "mock/nousage", "mock/nocost", "mock/broken"}:
            return self._json(400, error_envelope("invalid_request", field_paths=["model"]))
        served = {"x-splitsignal-served-route": model, **RATE_HEADERS}
        if body.get("stream"):
            frames = [f"data: {json.dumps(c)}\n\n" for c in stream_chunks(model)]
            if model == "mock/broken":
                frames = frames[:1] + [
                    "event: error\n",
                    f"data: {json.dumps(error_envelope('provider_unavailable'))}\n\n",
                ]
            else:
                frames.append("data: [DONE]\n\n")
            return httpx.Response(
                200,
                content="".join(frames).encode(),
                headers={"content-type": "text/event-stream", "x-request-id": REQUEST_ID, **served},
            )
        if model == "mock/paid":
            return self._json(200, chat_success(model, amount="0.000120"), **served)
        if model == "mock/nousage":
            return self._json(200, chat_success(model, amount=None, usage_known=False), **served)
        if model == "mock/nocost":
            return self._json(200, chat_success(model, amount=None), **served)
        return self._json(200, chat_success(model), **served)
