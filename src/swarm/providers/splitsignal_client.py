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
