# SW-X1-S1 — SplitSignal consumer adapter (contract swarmai-consumer 1.x) + SPLITSIGNAL_* env in the native loop

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-X1-S1` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-x1-s1-splitsignal-adapter` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | X (cross-repo: after W2, external gate SP1 = inference_server IS-W1-S10 merged) |
| Depends on | SW-W1-S11, SW-W2-S2 |
| Handoff file | `docs/v2.3/sessions/SW-X1-S1.md` |
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
git checkout -b cursor/v23-x1-s1-splitsignal-adapter origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W1-S11, SW-W2-S2. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/providers/router_client.py && echo "OK src/swarm/providers/router_client.py" || echo "MISSING src/swarm/providers/router_client.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/contracts/router_capabilities.py && echo "OK src/swarm/contracts/router_capabilities.py" || echo "MISSING src/swarm/contracts/router_capabilities.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/pursuit/native_loop.py && echo "OK src/swarm/pursuit/native_loop.py" || echo "MISSING src/swarm/pursuit/native_loop.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:tests/pursuit/test_v20_native_loop.py && echo "OK tests/pursuit/test_v20_native_loop.py" || echo "MISSING tests/pursuit/test_v20_native_loop.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/providers/splitsignal_client.py` — create
- `tests/fixtures/splitsignal_http/__init__.py` — create
- `tests/fixtures/splitsignal_http/fake_splitsignal.py` — create
- `tests/providers/test_splitsignal_client.py` — create
- `tests/pursuit/test_v20_native_loop_splitsignal.py` — create
- `src/swarm/pursuit/native_loop.py` — modify (one import + function native_loop_from_env only)
- `tests/pursuit/test_v20_native_loop.py` — modify (one added delenv line only)
- `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md` — modify (append one section)
- `docs/v2.3/sessions/SW-X1-S1.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Make SwarmAI a standard API client of **SplitSignal** (the product in the `inference_server` repo), per the frozen consumer contract `swarmai-consumer 1.x` (inference_server `docs/api/v1/consumers/swarmai.md`, session IS-W1-S10). Add a `SplitSignalClient` adapter that subclasses `RouterClient` (SW-W1-S11) and reuses its types, and make `native_loop_from_env` (SW-W2-S2) prefer `SPLITSIGNAL_*` over the legacy `SWARM_ROUTER_*` personal-router variables. Everything is tested offline against a fake. **No real SplitSignal call is made in this session.**

**Why.** The legacy router client reads `router.billing` from `/v1/models` and `X-Router-*` headers. SplitSignal sends neither. Its `/v1/models` returns the OpenAI list shape `{"object":"list","data":[{"id","object","created","owned_by"}]}`; cost comes from the `splitsignal` metadata on the settled response, and errors are `{"error":{code,message,request_id,retryable}}`. With the legacy client, every SplitSignal route would read as `billing: unknown` and be refused as `paid_route_forbidden`. The inference_server plan also retires the personal router (its X6), so SplitSignal becomes SwarmAI's only inference dependency.

**Decision D-SS1 — coordinator-accepted 2026-09-26 (C3); the owner may override it.** Copy this paragraph into the handoff under "Decisions".
- A route listed by SplitSignal's `/v1/models` under SwarmAI's key is admitted as `billing: free`. The contract says `/v1/models` lists only routes usable now, and in M1 only `cost_class: free` is dispatchable.
- A response whose `splitsignal.cost.amount` is a **known non-zero** decimal is refused after the fact with `policy_denied / paid_route_forbidden`; the receipt keeps `billing: paid`.
- An unknown cost (`amount: null`) is recorded as unknown: `cost_amount = None`, `cost_source = "unknown"`, never `0`. The receipt then has `usage_known = False`, so accounting keeps the budget hold committed and never releases it as zero (F-13 semantics).
- If the body is a `ModelPage` (`items[]` with `cost_class`), `cost_class` is authoritative. The coordinator is getting inference_server fixed so `/v1/models` returns `{"object":"list","data":[...]}` (C4); the adapter accepts both shapes.

### Step 0 — external gate SP1 (the contract is frozen)
SP1 means inference_server session IS-W1-S10 is merged into `cursor/is-v23-integration-460c`. Check it read-only:
```bash
gh api "repos/pri8771/inference_server/contents/docs/api/v1/consumers/swarmai.md?ref=cursor/is-v23-integration-460c" --jq .path \
  && echo "SP1 OK" || echo "SP1 MISSING"
```
- `SP1 OK`: read that file (`gh api ... --jq .content | base64 -d`). Compare it with the facts in this prompt: env var names `SPLITSIGNAL_BASE_URL` / `SPLITSIGNAL_API_KEY` / `SPLITSIGNAL_MODEL`, route ids like `mock/ok`, error codes, and the `/v1/models` shape. If the doc's `/v1/models` example is a `ModelPage` (`items`) instead of `{"object":"list","data":[...]}`, that is fine: the adapter accepts both. Write the difference in the handoff under "Decisions". If the doc changes something else this prompt relies on (env var names, auth header, error envelope field names), STOP (S7) and name the difference.
- `SP1 MISSING`: STOP (S7, section 10) with reason `external gate SP1 not reached`. Do not guess the contract. Exception: if the coordinator explicitly asks for the adapter before SP1, implement it against the offline fake, title the PR `[AWAITING SP1]`, write `awaiting SP1` in the handoff Status, and do not merge it.
- These contract facts are expected and are **not** differences (joint consistency check, `docs/plans/v2.3/JOINT_PLAN.md`): the version line `Consumer contract version: swarmai-consumer 1.0.0` (any `1.x` is compatible); the six `x-ratelimit-*` headers are optional and informational (the real server sends none; the mock and the fake send demo values; the adapter ignores them); a client may strip the trailing `/v1` from `SPLITSIGNAL_BASE_URL` and append `/v1/...` itself; the usage chunk arrives only with `stream_options.include_usage` (the base client sends it).
- Retry rule in the contract: never retry before `Retry-After` has elapsed; a client whose maximum wait is shorter gives up instead. Since SW-FIX-RETRY (`b3162712`), `RetryOwner.decide` returns a give-up with reason `retry_after_exceeds_cap` when `Retry-After` exceeds `max_retry_after_seconds` (30 s) or is not finite. Confirm with `grep -n retry_after_exceeds_cap src/swarm/broker/retry.py` and record the result under "Decisions". If the grep prints nothing, add under "Needs other owner": `src/swarm/broker/retry.py: when retry_after exceeds max_retry_after_seconds, give up instead of retrying at the cap (SplitSignal contract)`. Do not edit that file in this session.
- If `gh api repos/pri8771/inference_server --jq .full_name` does not print `pri8771/inference_server`, this session cannot read the private repo: STOP (S7) with reason `inference_server not readable from this environment`.

### Step 1 — `src/swarm/providers/splitsignal_client.py` (create, exactly)
```python
"""SplitSignal consumer adapter (contract ``swarmai-consumer 1.x``).

SwarmAI is an ordinary OpenAI-compatible API client of SplitSignal:

* Base URL from ``SPLITSIGNAL_BASE_URL`` (it ends in ``/v1``), bearer key from
  ``SPLITSIGNAL_API_KEY``, route from ``SPLITSIGNAL_MODEL``.
* ``GET /v1/models`` returns the OpenAI list shape (``data[].id`` = route id).
  SplitSignal lists only routes usable now, and in M1 only ``cost_class: free``
  is dispatchable, so a listed route is admitted as free (decision D-SS1). A
  ``ModelPage`` body (``items[]`` with ``cost_class``) is also accepted and its
  ``cost_class`` is authoritative.
* The served route comes from ``X-SplitSignal-Served-Route`` / body ``model``;
  cost and usage come from the ``splitsignal`` response metadata. A known
  non-zero cost is refused after the fact as ``paid_route_forbidden``. An
  unknown cost is recorded as ``None`` and never settles as zero (F-13).
* Error bodies are ``{"error": {code, message, request_id, retryable}}``. A
  non-retryable 5xx may still have executed upstream: ``unknown_outcome``.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

import httpx

from swarm.contracts.enums import ErrorClass
from swarm.contracts.router_capabilities import (
    RouteBilling,
    RouteCapabilities,
    RouterCallReceipt,
    parse_billing,
)
from swarm.providers.router_client import (
    ChatResult,
    RouterClient,
    RouterClientError,
    StreamResult,
)

SPLITSIGNAL_CONTRACT = "swarmai-consumer 1.x"
# Used when SPLITSIGNAL_MODEL is unset (inference_server SECRETS_SETUP §8).
DEFAULT_SPLITSIGNAL_MODEL = "gemini/gemini-3.5-flash-lite"

CostSource = Literal["reported", "estimated", "unknown"]


class SplitSignalReceipt(RouterCallReceipt):
    """RouterCallReceipt plus SplitSignal's cost fact.

    ``usage_known`` is the accounting "settled" flag: it is true only when both
    token counts **and** the cost are known, so an unknown cost keeps the budget
    hold committed (F-13) instead of settling as zero. Unknown cost is ``None``.
    """

    cost_amount: str | None = None
    cost_currency: str | None = None
    cost_source: CostSource = "unknown"


_CODE_CLASS: dict[str, ErrorClass] = {
    "unauthenticated": ErrorClass.AUTHENTICATION,
    "forbidden": ErrorClass.POLICY_DENIED,
    "quota_exhausted": ErrorClass.QUOTA_EXHAUSTED,
    "concurrency_exhausted": ErrorClass.RATE_LIMIT,
    "provider_rate_limited": ErrorClass.RATE_LIMIT,
    "capability_unsupported": ErrorClass.UNSUPPORTED_CAPABILITY,
    "no_eligible_route": ErrorClass.UNSUPPORTED_CAPABILITY,
    "not_implemented": ErrorClass.UNSUPPORTED_CAPABILITY,
    "invalid_request": ErrorClass.INVALID_REQUEST,
    "unsupported_field": ErrorClass.INVALID_REQUEST,
    "invalid_cursor": ErrorClass.INVALID_REQUEST,
    "not_found": ErrorClass.INVALID_REQUEST,
    "method_not_allowed": ErrorClass.INVALID_REQUEST,
    "request_too_large": ErrorClass.INVALID_REQUEST,
    "unsupported_media_type": ErrorClass.INVALID_REQUEST,
    "idempotency_conflict": ErrorClass.INVALID_REQUEST,
    "version_conflict": ErrorClass.INVALID_REQUEST,
    "connection_exists": ErrorClass.INVALID_REQUEST,
    "request_in_progress": ErrorClass.UNKNOWN_OUTCOME,
    "request_already_processed": ErrorClass.UNKNOWN_OUTCOME,
    "deadline_exceeded": ErrorClass.UNKNOWN_OUTCOME,
}


def classify_splitsignal_error(status_code: int, body: Any) -> tuple[ErrorClass, str, bool]:
    """Return (error class, code, retryable) for a SplitSignal ErrorEnvelope."""
    err = body.get("error") if isinstance(body, dict) else None
    err = err if isinstance(err, dict) else {}
    code = str(err.get("code") or "unknown_error")
    retryable = err.get("retryable") is True
    if code in _CODE_CLASS:
        return _CODE_CLASS[code], code, retryable
    if status_code >= 500:
        return (ErrorClass.TRANSIENT if retryable else ErrorClass.UNKNOWN_OUTCOME), code, retryable
    if status_code == 429:
        return ErrorClass.RATE_LIMIT, code, retryable
    return ErrorClass.INVALID_REQUEST, code, retryable


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _cost_billing(meta: Any) -> RouteBilling:
    """FREE unless SplitSignal reports a known non-zero cost.

    Unknown cost (``amount: null``) on a route SplitSignal dispatched is still free
    under its M1 free-only gate (D-SS1). The receipt records the cost as unknown
    and does not settle (``usage_known`` false), so no budget is released as zero.
    """
    cost = meta.get("cost") if isinstance(meta, dict) else None
    amount = cost.get("amount") if isinstance(cost, dict) else None
    if amount is None:
        return RouteBilling.FREE
    try:
        return RouteBilling.FREE if Decimal(str(amount)) == 0 else RouteBilling.PAID
    except InvalidOperation:
        return RouteBilling.UNKNOWN


def receipt_from_splitsignal(
    headers: Mapping[str, str],
    status_code: int | None,
    body: Mapping[str, Any] | None,
    *,
    meta: Any = None,
    usage: Any = None,
) -> SplitSignalReceipt:
    h = {k.lower(): v for k, v in headers.items()}
    body = body or {}
    meta = meta if meta is not None else body.get("splitsignal")
    usage = usage if usage is not None else body.get("usage")
    route = h.get("x-splitsignal-served-route") or body.get("model")
    if isinstance(meta, dict) and meta.get("served_route"):
        route = meta["served_route"]
    route_s = str(route) if route else None
    provider, _, upstream = (route_s or "").partition("/")
    attempts: list[str] = []
    if isinstance(meta, dict):
        for key in ("requested_route", "served_route"):
            value = meta.get(key)
            if isinstance(value, str) and value not in attempts:
                attempts.append(value)
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
    request_id = h.get("x-request-id") or body.get("id")
    amount, currency, cost_source = _cost_fact(meta)
    return SplitSignalReceipt(
        request_id=str(request_id) if request_id else None,
        route_id=route_s,
        provider=provider or None,
        upstream_model=upstream or None,
        billing=_cost_billing(meta) if meta is not None else RouteBilling.UNKNOWN,
        attempts=attempts,
        status_code=status_code,
        usage_known=prompt is not None and completion is not None and amount is not None,
        prompt_tokens=prompt,
        completion_tokens=completion,
        retry_after_s=retry_after,
        cost_amount=amount,
        cost_currency=currency,
        cost_source=cost_source,
    )


def _cost_fact(meta: Any) -> tuple[str | None, str | None, CostSource]:
    cost = meta.get("cost") if isinstance(meta, dict) else None
    if not isinstance(cost, dict) or cost.get("amount") is None:
        return None, None, "unknown"
    source = cost.get("source")
    known: CostSource = "estimated" if source == "estimated" else "reported"
    currency = cost.get("currency")
    return str(cost["amount"]), str(currency) if currency else None, known


def _supported(caps: Any, name: str) -> bool | None:
    if not isinstance(caps, dict) or name not in caps:
        return None
    return bool(caps[name] == "supported")


def _limit(limits: Any, name: str) -> int | None:
    fact = limits.get(name) if isinstance(limits, dict) else None
    return _int_or_none(fact.get("value")) if isinstance(fact, dict) else None


class SplitSignalClient(RouterClient):
    def __init__(
        self,
        base_url: str,
        *,
        api_key_env: str = "SPLITSIGNAL_API_KEY",
        transport: httpx.BaseTransport | None = None,
        timeout_s: float = 60.0,
        require_free: bool = True,
    ) -> None:
        root = base_url.rstrip("/")
        if root.endswith("/v1"):
            root = root[: -len("/v1")]
        super().__init__(
            root,
            api_key_env=api_key_env,
            transport=transport,
            timeout_s=timeout_s,
            require_free=require_free,
        )

    def _fail(self, resp: httpx.Response) -> RouterClientError:
        try:
            body = resp.json()
        except ValueError:
            body = None
        error_class, code, _ = classify_splitsignal_error(resp.status_code, body)
        receipt = receipt_from_splitsignal(resp.headers, resp.status_code, None)
        receipt = receipt.model_copy(update={"error_class": error_class, "error_code": code})
        return RouterClientError(error_class, code, receipt)

    def _check_billing(self, receipt: RouterCallReceipt) -> None:
        # Headers carry no cost class; the settled body is checked in chat()/chat_stream().
        return None

    def _refuse_paid(self, receipt: RouterCallReceipt) -> None:
        if self.require_free and receipt.billing == RouteBilling.PAID:
            denied = receipt.model_copy(
                update={
                    "error_class": ErrorClass.POLICY_DENIED,
                    "error_code": "paid_route_forbidden",
                }
            )
            raise RouterClientError(ErrorClass.POLICY_DENIED, "paid_route_forbidden", denied)

    def _capabilities(self, entry: dict[str, Any]) -> RouteCapabilities:
        if "route_id" in entry:
            return RouteCapabilities(
                model_id=str(entry["route_id"]),
                kind="route",
                billing=parse_billing(entry.get("cost_class", "unknown")),
                admission="admitted",
                context_window=_limit(entry.get("limits"), "context_window"),
                max_output_tokens=_limit(entry.get("limits"), "max_output_tokens"),
                supports_tools=_supported(entry.get("capabilities"), "tools"),
                supports_json=_supported(entry.get("capabilities"), "json_output"),
                metadata_source="router",
            )
        return RouteCapabilities(
            model_id=str(entry.get("id")),
            kind="route",
            billing=RouteBilling.FREE,
            admission="admitted",
            metadata_source="router",
        )

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
            raw = resp.json()
            entries = raw.get("data")
            if entries is None:
                entries = raw.get("items")
        except (ValueError, AttributeError) as exc:
            raise RouterClientError(ErrorClass.TRANSIENT, "malformed_models") from exc
        if not isinstance(entries, list):
            raise RouterClientError(ErrorClass.TRANSIENT, "malformed_models")
        return [self._capabilities(e) for e in entries if isinstance(e, dict)]

    def chat(self, body: dict[str, Any]) -> ChatResult:
        result = super().chat(body)
        # The contract makes body ``model`` equal to X-SplitSignal-Served-Route.
        receipt = receipt_from_splitsignal(
            {"x-request-id": result.receipt.request_id or ""},
            result.receipt.status_code,
            result.body,
        )
        self._refuse_paid(receipt)
        return ChatResult(body=result.body, receipt=receipt)

    def chat_stream(self, body: dict[str, Any]) -> StreamResult:
        result = super().chat_stream(body)
        meta: Any = None
        usage: Any = None
        last: dict[str, Any] = {}
        for chunk in result.chunks:
            last = chunk
            if isinstance(chunk.get("splitsignal"), dict):
                meta = chunk["splitsignal"]
            if chunk.get("usage"):
                usage = chunk["usage"]
        receipt = receipt_from_splitsignal(
            {"x-request-id": result.receipt.request_id or ""},
            result.receipt.status_code,
            {"id": last.get("id"), "model": last.get("model")},
            meta=meta,
            usage=usage,
        )
        self._refuse_paid(receipt)
        return StreamResult(text=result.text, receipt=receipt, chunks=result.chunks)
```

### Step 2 — `tests/fixtures/splitsignal_http/__init__.py` (create, empty file) and `tests/fixtures/splitsignal_http/fake_splitsignal.py` (create, exactly)
Every body in this fake was validated against inference_server `docs/api/v1/openapi.yaml` (`V1ModelList`, `ChatCompletion`, `ChatCompletionChunk`, `ErrorEnvelope`, `OfferCapabilities`, `OfferLimits`). The key is the contract's synthetic test key, not a secret.
```python
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
```

### Step 3 — `tests/providers/test_splitsignal_client.py` (create, exactly)
```python
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
```

### Step 4 — `src/swarm/pursuit/native_loop.py` (two edits, nothing else)
Edit 4a: directly **below** the line `from swarm.providers.router_client import RouterClient, RouterClientError`, add:
```python
from swarm.providers.splitsignal_client import DEFAULT_SPLITSIGNAL_MODEL, SplitSignalClient
```
Edit 4b: replace the whole function `native_loop_from_env` (it is the last function in the file). It currently reads exactly:
```python
def native_loop_from_env(
    tools: Mapping[str, ToolFn],
    *,
    grant: LiveGrant | None,
    env: Mapping[str, str] | None = None,
) -> tuple[BoundedNativeLoop | None, str]:
    """Build a live loop only with a router URL, a model and a usable LiveGrant."""
    e = os.environ if env is None else env
    base_url = e.get("SWARM_ROUTER_BASE_URL", "").strip()
    if not base_url:
        return None, "router_not_configured"
    model = e.get("SWARM_ROUTER_MODEL", "").strip()
    if not model:
        return None, "router_model_not_configured"
    pre = preflight_live_grant(grant, purpose="pursuit_native_loop", required_route=model)
    if not pre.ready:
        return None, pre.blocked_reason or "live_grant_not_ready"
    return BoundedNativeLoop(RouterClient(base_url), tools, model=model), "ready"
```
Replace it with exactly:
```python
def native_loop_from_env(
    tools: Mapping[str, ToolFn],
    *,
    grant: LiveGrant | None,
    env: Mapping[str, str] | None = None,
) -> tuple[BoundedNativeLoop | None, str]:
    """Build a live loop only with a base URL, a model and a usable LiveGrant.

    ``SPLITSIGNAL_MODEL`` falls back to ``DEFAULT_SPLITSIGNAL_MODEL``.

    ``SPLITSIGNAL_*`` (the SplitSignal consumer contract) wins over the legacy
    ``SWARM_ROUTER_*`` personal-router variables.
    """
    e = os.environ if env is None else env
    router: RouterClient
    ss_url = e.get("SPLITSIGNAL_BASE_URL", "").strip()
    if ss_url:
        model = e.get("SPLITSIGNAL_MODEL", "").strip() or DEFAULT_SPLITSIGNAL_MODEL
        router = SplitSignalClient(ss_url)
    else:
        base_url = e.get("SWARM_ROUTER_BASE_URL", "").strip()
        if not base_url:
            return None, "router_not_configured"
        model = e.get("SWARM_ROUTER_MODEL", "").strip()
        if not model:
            return None, "router_model_not_configured"
        router = RouterClient(base_url)
    pre = preflight_live_grant(grant, purpose="pursuit_native_loop", required_route=model)
    if not pre.ready:
        router.close()
        return None, pre.blocked_reason or "live_grant_not_ready"
    return BoundedNativeLoop(router, tools, model=model), "ready"
```
If the current text differs from the "currently reads" block, STOP (S4, section 10).

### Step 5 — `tests/pursuit/test_v20_native_loop.py` (one added line)
In `test_executor_without_loop_records_honest_blocker`, directly below `monkeypatch.delenv("SWARM_ROUTER_BASE_URL", raising=False)`, add:
```python
    monkeypatch.delenv("SPLITSIGNAL_BASE_URL", raising=False)
```
Reason: Cloud Agent environments may inject `SPLITSIGNAL_BASE_URL` as a secret. Without this line the test then fails, because the blocker reason changes. This failure was reproduced.

### Step 6 — `tests/pursuit/test_v20_native_loop_splitsignal.py` (create, exactly)
```python
from __future__ import annotations

from swarm.providers.splitsignal_client import DEFAULT_SPLITSIGNAL_MODEL, SplitSignalClient
from swarm.pursuit import native_loop
from swarm.pursuit.native_loop import native_loop_from_env


def test_splitsignal_env_without_model_uses_default(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    seen: dict[str, str] = {}

    class Blocked:
        ready = False
        blocked_reason = "live_grant_missing"

    def fake_preflight(grant, *, purpose, required_route):  # type: ignore[no-untyped-def]
        seen["route"] = required_route
        return Blocked()

    monkeypatch.setattr(native_loop, "preflight_live_grant", fake_preflight)
    env = {"SPLITSIGNAL_BASE_URL": "http://127.0.0.1:8089/v1"}
    loop, reason = native_loop_from_env({}, grant=None, env=env)
    assert loop is None and reason == "live_grant_missing"
    assert seen["route"] == DEFAULT_SPLITSIGNAL_MODEL


def test_splitsignal_env_without_grant_is_blocked() -> None:
    env = {"SPLITSIGNAL_BASE_URL": "http://127.0.0.1:8089/v1", "SPLITSIGNAL_MODEL": "mock/ok"}
    loop, reason = native_loop_from_env({}, grant=None, env=env)
    assert loop is None and reason != "ready"


def test_splitsignal_preferred_over_legacy_router(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class Ready:
        ready = True
        blocked_reason = None

    seen: dict[str, str] = {}

    def fake_preflight(grant, *, purpose, required_route):  # type: ignore[no-untyped-def]
        seen["route"] = required_route
        return Ready()

    monkeypatch.setattr(native_loop, "preflight_live_grant", fake_preflight)
    env = {
        "SPLITSIGNAL_BASE_URL": "http://127.0.0.1:8089/v1",
        "SPLITSIGNAL_MODEL": "mock/ok",
        "SWARM_ROUTER_BASE_URL": "http://legacy.test",
        "SWARM_ROUTER_MODEL": "legacy-free",
    }
    loop, reason = native_loop_from_env({}, grant=None, env=env)
    assert reason == "ready" and loop is not None
    assert isinstance(loop.router, SplitSignalClient)
    assert seen["route"] == "mock/ok"


def test_unknown_cost_keeps_loop_usage_unknown(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from swarm.pursuit.native_loop import BoundedNativeLoop
    from tests.fixtures.splitsignal_http.fake_splitsignal import SYNTHETIC_KEY, FakeSplitSignal

    monkeypatch.setenv("SPLITSIGNAL_API_KEY", SYNTHETIC_KEY)
    fake = FakeSplitSignal()
    known = BoundedNativeLoop(
        SplitSignalClient("http://s.test/v1", transport=fake.transport()), {}, model="mock/ok"
    ).run("say hi")
    unknown = BoundedNativeLoop(
        SplitSignalClient("http://s.test/v1", transport=fake.transport()), {}, model="mock/nocost"
    ).run("say hi")
    assert known.status == "completed" and known.usage_known is True
    assert unknown.status == "completed" and unknown.usage_known is False
```

### Step 7 — `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md` (append at the end)
```markdown
## SplitSignal consumer contract (`swarmai-consumer 1.x`) — SW-X1-S1

- Source: inference_server `docs/api/v1/consumers/swarmai.md` on `cursor/is-v23-integration-460c` (read <DATE>, blob <git sha from gh api --jq .sha>).
- Env: `SPLITSIGNAL_BASE_URL` (ends in `/v1`; the client strips it), `SPLITSIGNAL_API_KEY` (bearer; never logged), `SPLITSIGNAL_MODEL` (route id `<provider>/<model>`; default `gemini/gemini-3.5-flash-lite` when unset). These win over the legacy `SWARM_ROUTER_*`.
- `GET /v1/models`: OpenAI list shape; listed routes are admitted as free (decision D-SS1, coordinator-accepted 2026-09-26, owner may override). A `ModelPage` body's `cost_class` is authoritative.
- Chat: served route = body `model` = `X-SplitSignal-Served-Route`; usage `null` stays unknown; a known non-zero `splitsignal.cost.amount` is refused as `paid_route_forbidden`; an unknown cost is `cost_amount: null` and the receipt does not settle (`usage_known: false`), so no budget is released as zero (C3, F-13).
- Errors: `ErrorEnvelope`. A non-retryable 5xx is `unknown_outcome` (SplitSignal sets `retryable` only when no provider execution can still be running). SwarmAI never auto-retries after a 200 header; the stream `event: error` is `partial_stream`.
- Offline fake: `tests/fixtures/splitsignal_http/fake_splitsignal.py`. Live use still needs a LiveGrant (V20-E07) and sync point SP4 (non-streaming) / SP5 (streaming).
```
Fill `<DATE>` and the blob SHA from Step 0.

### Step 8 — optional: run against the real mock (only if SP2 is reached)
SP2 means `scripts/mock_splitsignal.py` is on `cursor/is-v23-integration-460c`. This step is optional. Its result goes into the handoff only; do not commit the mock. The mock loads `docs/api/v1/consumers/fixtures` relative to its repo root, so export that tree read-only and run the mock from there (a lone `/tmp/mock_splitsignal.py` dies with `FileNotFoundError` and the client then reports `transient:connect_error`, which is not a contract mismatch). Without a clone, fetch `scripts/mock_splitsignal.py` **and** every file under `docs/api/v1/consumers/fixtures/` with `gh api`, keeping the same relative paths under `/tmp/is-mock`.
```bash
mkdir -p /tmp/is-mock && git -C <inference_server clone> archive origin/cursor/is-v23-integration-460c scripts docs/api/v1 | tar -x -C /tmp/is-mock \
  && (cd /tmp/is-mock && python3 scripts/mock_splitsignal.py --port 8089 & echo $! > /tmp/mock.pid; sleep 2) \
  && SPLITSIGNAL_API_KEY="ss_live_00000000000000000000000000000000_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" uv run python -c "
from swarm.providers.splitsignal_client import SplitSignalClient
c = SplitSignalClient('http://127.0.0.1:8089/v1')
print([m.model_id for m in c.list_models()])
r = c.chat({'model': 'mock/ok', 'messages': [{'role': 'user', 'content': 'hi'}]})
print(r.receipt.route_id, r.receipt.billing, r.receipt.usage_known)
"; kill "$(cat /tmp/mock.pid)" 2>/dev/null; true
```
Expected output (observed with the IS-W1-S10 mock: `['mock/ok', 'mock/quota', 'mock/unavailable']` then `mock/ok free False`): a list containing `mock/ok`, then `mock/ok free <True or False>` (`False` is correct when the mock's fixture reports no cost). If it differs, record the exact output under "Needs other owner" (a contract/mock mismatch for the inference_server coordinator). Do **not** change the adapter to fit the mock.

### Acceptance (this session)
- [ ] Step 0 printed `SP1 OK`, and the contract facts match (or the differences are recorded).
- [ ] `uv run pytest tests/providers/test_splitsignal_client.py tests/pursuit -q` passes (27 new tests in the two new files, plus the existing ones).
- [ ] `SPLITSIGNAL_BASE_URL=http://x.test/v1 uv run pytest tests/pursuit/test_v20_native_loop.py -q` passes.
- [ ] `tests/providers/test_router_client.py` is unchanged and still passes (the legacy path works).
- [ ] No real network call: every test uses `FakeSplitSignal().transport()` or an explicit `env` dict.
- [ ] `grep -rn "ss_live_" src/` prints nothing (the synthetic key lives only in tests).
- [ ] `test_chat_unknown_cost_never_settles_as_zero` and `test_unknown_cost_keeps_loop_usage_unknown` pass.
- [ ] The handoff records D-SS1, the contract blob SHA and the Step 8 result (or `SP2 not reached`).

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_x1_s1 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_x1_s1
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/providers tests/pursuit -q
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
git add src/swarm/providers/splitsignal_client.py tests/fixtures/splitsignal_http/__init__.py tests/fixtures/splitsignal_http/fake_splitsignal.py tests/providers/test_splitsignal_client.py tests/pursuit/test_v20_native_loop_splitsignal.py src/swarm/pursuit/native_loop.py tests/pursuit/test_v20_native_loop.py docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md docs/v2.3/sessions/SW-X1-S1.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(splitsignal): consumer adapter for contract swarmai-consumer 1.x; SPLITSIGNAL_* env wins in native loop" -m "Session: SW-X1-S1. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-x1-s1-splitsignal-adapter
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-x1-s1-splitsignal-adapter --title "[SW-X1-S1] SplitSignal consumer adapter (contract swarmai-consumer 1.x) + SPLITSIGNAL_* env in the native loop" --body-file docs/v2.3/sessions/SW-X1-S1.md
git ls-remote origin refs/heads/cursor/v23-x1-s1-splitsignal-adapter   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-X1-S1.md` with exactly these headings:
```markdown
# SW-X1-S1 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-X1-S1.md` then `git commit -m "WIP(SW-X1-S1): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-x1-s1-splitsignal-adapter` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-x1-s1-splitsignal-adapter?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-X1-S1
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/providers/splitsignal_client.py`, `tests/fixtures/splitsignal_http/__init__.py`, `tests/fixtures/splitsignal_http/fake_splitsignal.py`, `tests/providers/test_splitsignal_client.py`, `tests/pursuit/test_v20_native_loop_splitsignal.py`, `src/swarm/pursuit/native_loop.py`, `tests/pursuit/test_v20_native_loop.py`, `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md`, `docs/v2.3/sessions/SW-X1-S1.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: D-SS1 free admission; known non-zero cost refused; unknown cost recorded as null and never settles as zero (C3/F-13); error classes; no retry after a 200 header; key never logged.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
