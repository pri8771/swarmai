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
