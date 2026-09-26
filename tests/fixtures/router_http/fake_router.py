"""Offline fake of the inference_server HTTP surface (no network, no spend).

Shapes follow inference_server ``src/inference_router/app.py`` @ 96af9d4:
``/v1/models`` → ``{"object": "list", "data": [...]}`` with a ``router`` object,
``X-Router-*`` headers, errors as ``{"error": {"message", "type", "code"}}``.

Scenarios: ok, tools, stream, partial_stream, malformed, rate_limited,
unavailable, missing_usage, paid, timeout.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

SCENARIOS = (
    "ok",
    "tools",
    "stream",
    "partial_stream",
    "malformed",
    "rate_limited",
    "unavailable",
    "missing_usage",
    "paid",
    "timeout",
)

FAKE_MODELS: list[dict[str, Any]] = [
    {
        "id": "fake-free",
        "object": "model",
        "created": 0,
        "owned_by": "fake",
        "router": {
            "type": "route",
            "provider_kind": "fake",
            "upstream_model": "fake-1",
            "billing": "free",
            "verified_at": "2026-09-01",
            "capabilities": ["chat", "tools"],
            "admission": "admitted",
        },
    },
    {
        "id": "fake-paid",
        "object": "model",
        "created": 0,
        "owned_by": "fake",
        "router": {
            "type": "route",
            "provider_kind": "fake",
            "upstream_model": "fake-2",
            "billing": "paid",
            "verified_at": None,
            "capabilities": None,
            "admission": "billing_not_allowed",
        },
    },
    {
        "id": "fast",
        "object": "model",
        "created": 0,
        "owned_by": "router-alias",
        "router": {"type": "alias", "routes": ["fake-free"], "admitted_routes": ["fake-free"]},
    },
]

USAGE = {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18}


def route_headers(billing: str = "free", request_id: str = "req_fake_1") -> dict[str, str]:
    return {
        "X-Request-Id": request_id,
        "X-Router-Route": "fake-free" if billing == "free" else "fake-paid",
        "X-Router-Provider": "fake",
        "X-Router-Upstream-Model": "fake-1",
        "X-Router-Billing": billing,
        "X-Router-Attempts": "fake-free=ok",
        "Cache-Control": "no-store",
    }


def _error(status: int, code: str, *, retry_after: int | None = None) -> httpx.Response:
    etype = "rate_limit_error" if status == 429 else "api_error"
    headers = {"X-Request-Id": "req_fake_err"}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    body = {"error": {"message": code, "type": etype, "code": code}}
    return httpx.Response(status, json=body, headers=headers)


def _completion(message: dict[str, Any], *, usage: bool = True) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": "chatcmpl_fake",
        "object": "chat.completion",
        "model": "fake-free",
        "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
    }
    if usage:
        body["usage"] = dict(USAGE)
    return body


def _sse(events: list[str]) -> bytes:
    return "".join(f"data: {e}\n\n" for e in events).encode()


class FakeRouter:
    """``FakeRouter("ok").transport`` plugs into ``RouterClient(transport=...)``."""

    def __init__(self, scenario: str = "ok") -> None:
        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario {scenario}")
        self.scenario = scenario
        self.requests: list[dict[str, Any]] = []
        self.transport = httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content or b"{}") if request.method == "POST" else {}
        self.requests.append(
            {
                "method": request.method,
                "path": request.url.path,
                "body": body,
                "has_auth": "authorization" in request.headers,
            }
        )
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"object": "list", "data": FAKE_MODELS})
        if request.url.path != "/v1/chat/completions":
            return _error(404, "not_found")
        return self._chat(request, body)

    def _chat(self, request: httpx.Request, body: dict[str, Any]) -> httpx.Response:
        s = self.scenario
        if s == "timeout":
            raise httpx.ReadTimeout("fake timeout", request=request)
        if s == "rate_limited":
            return _error(429, "upstream_rate_limited", retry_after=7)
        if s == "unavailable":
            return _error(502, "upstream_unavailable")
        headers = route_headers("paid" if s == "paid" else "free")
        if s == "malformed":
            return httpx.Response(200, content=b"{not json", headers=headers)
        if s in ("stream", "partial_stream"):
            events = [
                json.dumps({"choices": [{"index": 0, "delta": {"content": "hel"}}]}),
                json.dumps({"choices": [{"index": 0, "delta": {"content": "lo"}}]}),
            ]
            if s == "stream":
                events.append(json.dumps({"choices": [], "usage": dict(USAGE)}))
                events.append("[DONE]")
            else:
                events.append(json.dumps({"error": {"code": "upstream_unavailable"}}))
            sse_headers = {**headers, "Content-Type": "text/event-stream"}
            return httpx.Response(200, content=_sse(events), headers=sse_headers)
        if s == "tools":
            messages = body.get("messages") or []
            if not any(m.get("role") == "tool" for m in messages):
                call = {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "workspace.read", "arguments": '{"path": "README.md"}'},
                }
                msg = {"role": "assistant", "content": None, "tool_calls": [call]}
                return httpx.Response(200, json=_completion(msg), headers=headers)
            final = {"role": "assistant", "content": "done after tool"}
            return httpx.Response(200, json=_completion(final), headers=headers)
        msg = {"role": "assistant", "content": "hello"}
        return httpx.Response(
            200, json=_completion(msg, usage=s != "missing_usage"), headers=headers
        )
