# SW-W1-S11 — inference_server HTTP client + fake router fixture (packet P05)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S11` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s11-router-client` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | none |
| Handoff file | `docs/v2.3/sessions/SW-W1-S11.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v23-w1-s11-router-client origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
This session has **no dependencies**. Go to Step 1.

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/providers/router_client.py` — create
- `src/swarm/contracts/router_capabilities.py` — create
- `tests/fixtures/__init__.py` — create
- `tests/fixtures/router_http/__init__.py` — create
- `tests/fixtures/router_http/fake_router.py` — create
- `tests/providers/test_router_client.py` — create
- `config/router_context_overrides.example.json` — create
- `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md` — create
- `docs/v2.3/sessions/SW-W1-S11.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Build packet P05, SwarmAI's client for the `inference_server` router. Today `src/` has **no** router client and no `X-Router-*` handling.

**This session adds:**
- `swarm.contracts.router_capabilities`: `RouteBilling`, `RouteCapabilities.admissible()` (free-only), `RouterCallReceipt` built from headers, and `classify_error`, which maps router errors to `ErrorClass`.
- `swarm.providers.router_client.RouterClient` on `httpx`:
  - `list_models`, `chat` and `chat_stream`.
  - **No retries**.
  - Refuses routes that are not free.
  - Treats timeouts as `unknown_outcome`, missing usage as unknown (not 0), and an incomplete stream as `partial_stream`.
- An offline `FakeRouter` built on `httpx.MockTransport`, with 10 scenarios, used here and by SW-W2-S2.
- An overrides example file and a contract snapshot doc.

**Live calls stay blocked** (owner LiveGrant, blocker B-05). Nothing in this session may contact a real network address; the tests use `http://router.invalid` with the mock transport.

The code below was compiled and run against `dev @ 8e1c0fde`. `tests/providers` gives 48 passed, including 12 new tests, and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/contracts/router_capabilities.py` (create, exactly)
```python
"""inference_server client contracts (packet P05).

Mirrors the router's observed HTTP surface: ``GET /v1/models`` entries with a
``router`` metadata object, and ``X-Router-*`` response headers. SwarmAI admits
only routes whose billing is ``free``; unknown billing is never free.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field

from swarm.contracts.common import StrictModel
from swarm.contracts.enums import ErrorClass


class RouteBilling(StrEnum):
    FREE = "free"
    TRIAL = "trial"
    PAID = "paid"
    UNKNOWN = "unknown"


def parse_billing(value: Any) -> RouteBilling:
    try:
        return RouteBilling(str(value).strip().lower())
    except ValueError:
        return RouteBilling.UNKNOWN


class RouteCapabilities(StrictModel):
    model_id: str
    kind: Literal["route", "alias", "unknown"] = "unknown"
    billing: RouteBilling = RouteBilling.UNKNOWN
    admission: str | None = None
    context_window: int | None = None
    max_output_tokens: int | None = None
    tokenizer: str | None = None
    supports_tools: bool | None = None
    supports_json: bool | None = None
    metadata_source: Literal["router", "override", "none"] = "none"

    def admissible(
        self, *, needs_tools: bool = False, min_context: int | None = None
    ) -> tuple[bool, str | None]:
        if self.billing != RouteBilling.FREE:
            return False, "paid_route_forbidden"
        if self.admission not in (None, "admitted"):
            return False, f"router_admission:{self.admission}"
        if needs_tools and self.supports_tools is False:
            return False, "tools_unsupported"
        if min_context is not None and self.context_window is not None:
            if self.context_window < min_context:
                return False, "context_window_too_small"
        return True, None


class RouterCallReceipt(StrictModel):
    request_id: str | None = None
    route_id: str | None = None
    provider: str | None = None
    upstream_model: str | None = None
    billing: RouteBilling = RouteBilling.UNKNOWN
    attempts: list[str] = Field(default_factory=list)
    status_code: int | None = None
    usage_known: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    error_class: ErrorClass | None = None
    error_code: str | None = None
    retry_after_s: float | None = None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def receipt_from_response(
    headers: Mapping[str, str], status_code: int | None, usage: Any = None
) -> RouterCallReceipt:
    h = {k.lower(): v for k, v in headers.items()}
    attempts_raw = h.get("x-router-attempts", "")
    retry_after: float | None = None
    if "retry-after" in h:
        try:
            retry_after = float(h["retry-after"])
        except ValueError:
            retry_after = None
    prompt = completion = None
    if isinstance(usage, dict):
        prompt = _int_or_none(usage.get("prompt_tokens"))
        completion = _int_or_none(usage.get("completion_tokens"))
    return RouterCallReceipt(
        request_id=h.get("x-request-id"),
        route_id=h.get("x-router-route"),
        provider=h.get("x-router-provider"),
        upstream_model=h.get("x-router-upstream-model"),
        billing=parse_billing(h.get("x-router-billing", "unknown")),
        attempts=[a for a in attempts_raw.split(",") if a],
        status_code=status_code,
        usage_known=prompt is not None and completion is not None,
        prompt_tokens=prompt,
        completion_tokens=completion,
        retry_after_s=retry_after,
    )


_INVALID = {400, 404, 405, 413, 415, 422}


def classify_error(status_code: int, body: Any) -> tuple[ErrorClass, str]:
    """Map the router error body ``{"error": {"type", "code", "message"}}`` to ErrorClass."""
    code = "unknown_error"
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        code = str(body["error"].get("code") or code)
    if status_code == 401:
        return ErrorClass.AUTHENTICATION, code
    if status_code == 403:
        return ErrorClass.POLICY_DENIED, code
    if status_code == 429:
        return ErrorClass.RATE_LIMIT, code
    if code == "upstream_payment_required":
        return ErrorClass.QUOTA_EXHAUSTED, code
    if code == "unknown_model":
        return ErrorClass.UNSUPPORTED_CAPABILITY, code
    if status_code in _INVALID:
        return ErrorClass.INVALID_REQUEST, code
    if status_code == 504 or code in {"upstream_timeout", "deadline_exceeded"}:
        return ErrorClass.UNKNOWN_OUTCOME, code
    return ErrorClass.TRANSIENT, code
```

### Step 2 — `src/swarm/providers/router_client.py` (create, exactly)
```python
"""HTTP client for the inference_server router (packet P05).

* No HTTP-library retries: the router owns transport retry/fallback; semantic
  retry belongs to SwarmAI's RetryOwner.
* Zero spend: responses whose ``X-Router-Billing`` is not ``free`` are refused
  (``paid_route_forbidden``) when ``require_free`` is set (the default).
* Timeouts and 504s are ``unknown_outcome`` — the upstream may have run.
* The API key is read from an environment variable name and never logged.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from swarm.contracts.enums import ErrorClass
from swarm.contracts.router_capabilities import (
    RouteBilling,
    RouteCapabilities,
    RouterCallReceipt,
    classify_error,
    parse_billing,
    receipt_from_response,
)

OVERRIDE_FIELDS = (
    "context_window",
    "max_output_tokens",
    "tokenizer",
    "supports_tools",
    "supports_json",
)


class RouterClientError(RuntimeError):
    def __init__(
        self,
        error_class: ErrorClass,
        code: str,
        receipt: RouterCallReceipt | None = None,
        *,
        partial_text: str = "",
    ) -> None:
        super().__init__(f"{error_class.value}:{code}")
        self.error_class = error_class
        self.code = code
        self.receipt = receipt
        self.partial_text = partial_text


@dataclass
class ChatResult:
    body: dict[str, Any]
    receipt: RouterCallReceipt

    @property
    def message(self) -> dict[str, Any]:
        choices = self.body.get("choices") or [{}]
        msg = choices[0].get("message") or {}
        return dict(msg)


@dataclass
class StreamResult:
    text: str
    receipt: RouterCallReceipt
    chunks: list[dict[str, Any]] = field(default_factory=list)


def load_overrides(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    models = raw.get("models") if isinstance(raw, dict) else None
    return {str(k): dict(v) for k, v in (models or {}).items() if isinstance(v, dict)}


class RouterClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key_env: str = "SWARM_ROUTER_API_KEY",
        transport: httpx.BaseTransport | None = None,
        timeout_s: float = 30.0,
        overrides: dict[str, dict[str, Any]] | None = None,
        require_free: bool = True,
    ) -> None:
        self._api_key_env = api_key_env
        self._overrides = overrides or {}
        self.require_free = require_free
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            transport=transport or httpx.HTTPTransport(retries=0),
            timeout=timeout_s,
        )

    def close(self) -> None:
        self._http.close()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        key = os.environ.get(self._api_key_env, "")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def _fail(self, resp: httpx.Response) -> RouterClientError:
        try:
            body = resp.json()
        except ValueError:
            body = None
        error_class, code = classify_error(resp.status_code, body)
        receipt = receipt_from_response(resp.headers, resp.status_code)
        receipt = receipt.model_copy(update={"error_class": error_class, "error_code": code})
        return RouterClientError(error_class, code, receipt)

    def _check_billing(self, receipt: RouterCallReceipt) -> None:
        if self.require_free and receipt.billing != RouteBilling.FREE:
            denied = receipt.model_copy(
                update={
                    "error_class": ErrorClass.POLICY_DENIED,
                    "error_code": "paid_route_forbidden",
                }
            )
            raise RouterClientError(ErrorClass.POLICY_DENIED, "paid_route_forbidden", denied)

    def list_models(self) -> list[RouteCapabilities]:
        try:
            resp = self._http.get("/v1/models", headers=self._headers())
        except httpx.TimeoutException as exc:
            raise RouterClientError(ErrorClass.TRANSIENT, "timeout") from exc
        except httpx.TransportError as exc:
            raise RouterClientError(ErrorClass.TRANSIENT, "connect_error") from exc
        if resp.status_code >= 400:
            raise self._fail(resp)
        try:
            data = resp.json().get("data") or []
        except (ValueError, AttributeError) as exc:
            raise RouterClientError(ErrorClass.TRANSIENT, "malformed_models") from exc
        return [self._capabilities(entry) for entry in data if isinstance(entry, dict)]

    def _capabilities(self, entry: dict[str, Any]) -> RouteCapabilities:
        raw_meta = entry.get("router")
        meta: dict[str, Any] = raw_meta if isinstance(raw_meta, dict) else {}
        kind = meta.get("type") if meta.get("type") in ("route", "alias") else "unknown"
        values: dict[str, Any] = {
            "model_id": str(entry.get("id")),
            "kind": kind,
            "billing": parse_billing(meta.get("billing", "unknown")),
            "admission": meta.get("admission"),
            "metadata_source": "none",
        }
        caps = meta.get("capabilities")
        if isinstance(caps, list):
            values["supports_tools"] = "tools" in caps
            values["supports_json"] = "json" in caps or "response_format" in caps
        for name in OVERRIDE_FIELDS:
            if name in meta:
                values[name] = meta[name]
                values["metadata_source"] = "router"
        for name, value in self._overrides.get(values["model_id"], {}).items():
            if name in OVERRIDE_FIELDS and values.get(name) is None:
                values[name] = value
                if values["metadata_source"] == "none":
                    values["metadata_source"] = "override"
        return RouteCapabilities(**values)

    def chat(self, body: dict[str, Any]) -> ChatResult:
        payload = {**body, "stream": False}
        try:
            resp = self._http.post("/v1/chat/completions", json=payload, headers=self._headers())
        except httpx.TimeoutException as exc:
            raise RouterClientError(ErrorClass.UNKNOWN_OUTCOME, "timeout") from exc
        except httpx.TransportError as exc:
            raise RouterClientError(ErrorClass.TRANSIENT, "connect_error") from exc
        if resp.status_code >= 400:
            raise self._fail(resp)
        receipt = receipt_from_response(resp.headers, resp.status_code)
        self._check_billing(receipt)
        try:
            data = resp.json()
        except ValueError as exc:
            malformed = RouterClientError(ErrorClass.UNKNOWN_OUTCOME, "malformed_response", receipt)
            raise malformed from exc
        if not isinstance(data, dict) or not isinstance(data.get("choices"), list):
            raise RouterClientError(ErrorClass.UNKNOWN_OUTCOME, "malformed_response", receipt)
        receipt = receipt_from_response(resp.headers, resp.status_code, data.get("usage"))
        return ChatResult(body=data, receipt=receipt)

    def chat_stream(self, body: dict[str, Any]) -> StreamResult:
        payload = {**body, "stream": True, "stream_options": {"include_usage": True}}
        headers = {**self._headers(), "Accept": "text/event-stream"}
        text_parts: list[str] = []
        chunks: list[dict[str, Any]] = []
        usage: Any = None
        done = False
        try:
            with self._http.stream(
                "POST", "/v1/chat/completions", json=payload, headers=headers
            ) as resp:
                if resp.status_code >= 400:
                    resp.read()
                    raise self._fail(resp)
                receipt = receipt_from_response(resp.headers, resp.status_code)
                self._check_billing(receipt)
                for line in resp.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        done = True
                        break
                    try:
                        chunk = json.loads(data)
                    except ValueError:
                        break
                    if not isinstance(chunk, dict) or "error" in chunk:
                        break
                    chunks.append(chunk)
                    if chunk.get("usage"):
                        usage = chunk["usage"]
                    for choice in chunk.get("choices") or []:
                        piece = (choice.get("delta") or {}).get("content")
                        if isinstance(piece, str):
                            text_parts.append(piece)
        except httpx.TimeoutException as exc:
            raise RouterClientError(
                ErrorClass.PARTIAL_STREAM if text_parts else ErrorClass.UNKNOWN_OUTCOME,
                "timeout",
                partial_text="".join(text_parts),
            ) from exc
        except httpx.TransportError as exc:
            raise RouterClientError(
                ErrorClass.PARTIAL_STREAM, "stream_broken", partial_text="".join(text_parts)
            ) from exc
        final = receipt_from_response(resp.headers, resp.status_code, usage)
        if not done:
            broken = final.model_copy(
                update={"error_class": ErrorClass.PARTIAL_STREAM, "error_code": "stream_incomplete"}
            )
            raise RouterClientError(
                ErrorClass.PARTIAL_STREAM,
                "stream_incomplete",
                broken,
                partial_text="".join(text_parts),
            )
        return StreamResult(text="".join(text_parts), receipt=final, chunks=chunks)
```

### Step 3 — test fixtures (create, exactly)
Create `tests/fixtures/__init__.py` and `tests/fixtures/router_http/__init__.py` as **empty** files. Then create `tests/fixtures/router_http/fake_router.py`:
```python
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
```

### Step 4 — `tests/providers/test_router_client.py` (create, exactly)
```python
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
```

### Step 5 — `config/router_context_overrides.example.json` (create, exactly)
```json
{
  "schema": "swarm.router_context_overrides.v1",
  "note": "Local metadata for models whose inference_server /v1/models entry lacks it. Never sets billing: zero-spend admission uses only the router's billing value.",
  "models": {
    "example-free-route": {
      "context_window": 8192,
      "max_output_tokens": 1024,
      "tokenizer": "unknown",
      "supports_tools": false,
      "supports_json": false
    }
  }
}
```

### Step 6 — `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md` (create, exactly)
````markdown
# inference_server HTTP contract snapshot (client view)

Status: **observed, not released**. inference_server `main` is docs-only; the router code lives on
unmerged branches. This snapshot pins what SwarmAI's `RouterClient` (packet P05) expects. Source:
`inference_server` branch `cursor/v08-v17-offline-ladder-7ebe` @ `96af9d4`,
`src/inference_router/app.py`, `errors.py`, `router.py`, `config.py`. SwarmAI never edits inference_server.

## Endpoints used
| Method | Path | Used by |
|---|---|---|
| GET | `/v1/models` | `RouterClient.list_models()` |
| POST | `/v1/chat/completions` (`stream=false`) | `RouterClient.chat()` |
| POST | `/v1/chat/completions` (`stream=true`, SSE, `data: [DONE]`) | `RouterClient.chat_stream()` |

## `/v1/models` entry
`{"id", "object": "model", "created", "owned_by", "router": {...}}`.
- Route: `router.type="route"`, `billing` ∈ `free|trial|paid|unknown`, `capabilities` (list or null), `admission` (`"admitted"` or a reason).
- Alias: `router.type="alias"`, `routes`, `admitted_routes`; **no billing** → SwarmAI treats it as `unknown` (never free).
- Missing today: `context_window`, `max_output_tokens`, `tokenizer`. SwarmAI reads them from the router if present, else from `config/router_context_overrides.example.json` (overrides can **never** set billing).

## Response headers → `RouterCallReceipt`
`X-Request-Id`, `X-Router-Route`, `X-Router-Provider`, `X-Router-Upstream-Model`, `X-Router-Billing`,
`X-Router-Attempts` (comma list `route=outcome`), `Retry-After` on errors.

## Errors
Body `{"error": {"message", "type", "code"}}`. Mapping in `swarm.contracts.router_capabilities.classify_error`:
401→authentication, 403→policy_denied, 429→rate_limit, `upstream_payment_required`→quota_exhausted,
`unknown_model`→unsupported_capability, other 4xx→invalid_request, 504/`upstream_timeout`/`deadline_exceeded`→unknown_outcome, else transient.

## SwarmAI rules
- No client-side HTTP retries (router owns retry/fallback). One request per call.
- Zero spend: a response whose `X-Router-Billing` is not `free` is refused as `paid_route_forbidden`.
- Missing `usage` → `usage_known=false` (never zero). Timeouts → `unknown_outcome`.
- Stream without `[DONE]` or with an error event → `partial_stream` (partial text kept, never treated as success).

## Asks for the inference_server coordinator (non-blocking)
1. Additive capability fields on `/v1/models`: `context_window`, `max_output_tokens`, `tokenizer`, `supports_tools`, `supports_json`; `billing` on aliases (resolved worst-case).
2. Freeze the header set with a version header (e.g. `X-Router-Contract: 1`).
3. Document the max router-side attempts per request, and `Idempotency-Key` support (or its absence).
````

### Step 7 — run
```bash
uv run pytest tests/providers/test_router_client.py -q    # 12 passed
uv run pytest tests/providers -q
```
If `from tests.fixtures.router_http.fake_router import FakeRouter` fails with `ModuleNotFoundError`, check that both `__init__.py` files exist. `tests/__init__.py` already exists on the base branch.

### Section-5 acceptance
- [ ] `list_models` parses route and alias entries; only `billing == "free"` with `admission` of `admitted` or absent is admissible, and aliases are unknown and therefore not admissible.
- [ ] Overrides fill missing context and tool metadata but can never change billing.
- [ ] `chat` returns a `RouterCallReceipt` from `X-Router-*` headers; missing `usage` gives `usage_known=False`.
- [ ] A paid response raises `paid_route_forbidden`; each error scenario sends exactly one request (no retries) and maps to the documented `ErrorClass`.
- [ ] A complete stream returns the text and usage; a stream without `[DONE]` raises `partial_stream` with the partial text.
- [ ] No real network, no API key in code (the test key is a fake literal via `monkeypatch`).

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s11 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s11
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/providers/test_router_client.py tests/providers -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/providers/router_client.py src/swarm/contracts/router_capabilities.py tests/fixtures/__init__.py tests/fixtures/router_http/__init__.py tests/fixtures/router_http/fake_router.py tests/providers/test_router_client.py config/router_context_overrides.example.json docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md docs/v2.3/sessions/SW-W1-S11.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(router): inference_server HTTP client, capability admission and offline fake router (P05)" -m "Session: SW-W1-S11. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s11-router-client
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s11-router-client --title "[SW-W1-S11] inference_server HTTP client + fake router fixture (packet P05)" --body-file docs/v2.3/sessions/SW-W1-S11.md
git ls-remote origin refs/heads/cursor/v23-w1-s11-router-client   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S11.md` with exactly these headings:
```markdown
# SW-W1-S11 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S11.md` then `git commit -m "WIP(SW-W1-S11): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s11-router-client` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s11-router-client?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S11
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/providers/router_client.py`, `src/swarm/contracts/router_capabilities.py`, `tests/fixtures/__init__.py`, `tests/fixtures/router_http/__init__.py`, `tests/fixtures/router_http/fake_router.py`, `tests/providers/test_router_client.py`, `config/router_context_overrides.example.json`, `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md`, `docs/v2.3/sessions/SW-W1-S11.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: no HTTP-library retries; paid/unknown billing refused; API key never logged.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
