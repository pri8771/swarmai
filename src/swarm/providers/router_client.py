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

    def set_timeout(self, timeout_s: float) -> None:
        """Bound subsequent HTTP operations by the caller's remaining wall budget."""
        self._http.timeout = httpx.Timeout(max(float(timeout_s), 0.001))

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
