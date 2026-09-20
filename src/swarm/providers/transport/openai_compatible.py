"""Recorded HTTP transport for OpenAI-compatible and custom provider APIs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import httpx

from swarm.contracts.enums import ErrorClass
from swarm.providers.secrets import SecretRef, redact

TransportMode = Literal["live", "replay", "record"]


@dataclass
class RecordedExchange:
    method: str
    url: str
    status_code: int
    request_json: dict[str, Any] | None
    response_json: dict[str, Any] | None
    response_text: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


class ProviderHttpError(RuntimeError):
    def __init__(self, status_code: int, body: str, error_class: ErrorClass) -> None:
        super().__init__(f"http_{status_code}")
        self.status_code = status_code
        self.body = body
        self.error_class = error_class


class RecordingTransport:
    """httpx-backed transport with offline replay fixtures. No automatic retries."""

    def __init__(
        self,
        *,
        base_url: str,
        secret_refs: list[SecretRef],
        mode: TransportMode = "replay",
        fixture_path: Path | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.secret_refs = secret_refs
        self.mode = mode
        self.fixture_path = fixture_path
        self.timeout = timeout
        self.calls = 0
        self._replay_queue: list[RecordedExchange] = []
        if mode == "replay" and fixture_path and fixture_path.exists():
            raw = json.loads(fixture_path.read_text())
            self._replay_queue = [RecordedExchange(**item) for item in raw]

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        for ref in self.secret_refs:
            if ref.present():
                headers["Authorization"] = f"Bearer {ref.resolve()}"
                break
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        self.calls += 1
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        if self.mode == "replay":
            return self._replay(method, url, json_body)
        headers = self._auth_headers()
        if extra_headers:
            headers.update(extra_headers)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method, url, json=json_body, params=params, headers=headers
            )
        body_text = response.text
        secrets = [r.resolve() for r in self.secret_refs if r.present()]
        safe_body = redact(body_text, secrets)
        if self.mode == "record" and self.fixture_path is not None:
            self._append_record(method, url, response.status_code, json_body, safe_body)
        if response.status_code >= 400:
            raise ProviderHttpError(
                response.status_code,
                safe_body,
                classify_http_status(response.status_code, safe_body),
            )
        return response.json() if response.content else {}

    def _replay(
        self, method: str, url: str, json_body: dict[str, Any] | None
    ) -> dict[str, Any]:
        if not self._replay_queue:
            raise RuntimeError(f"no recorded fixture left for {method} {url}")
        exchange = self._replay_queue.pop(0)
        if exchange.status_code >= 400:
            raise ProviderHttpError(
                exchange.status_code,
                exchange.response_text or json.dumps(exchange.response_json),
                classify_http_status(
                    exchange.status_code, exchange.response_text or ""
                ),
            )
        return exchange.response_json or {}

    def _append_record(
        self,
        method: str,
        url: str,
        status: int,
        request_json: dict[str, Any] | None,
        body_text: str,
    ) -> None:
        assert self.fixture_path is not None
        try:
            payload = json.loads(body_text) if body_text else None
        except json.JSONDecodeError:
            payload = None
        existing: list[dict[str, Any]] = []
        if self.fixture_path.exists():
            existing = json.loads(self.fixture_path.read_text())
        existing.append(
            {
                "method": method,
                "url": url,
                "status_code": status,
                "request_json": request_json,
                "response_json": payload,
                "response_text": body_text if payload is None else None,
                "headers": {},
            }
        )
        self.fixture_path.parent.mkdir(parents=True, exist_ok=True)
        self.fixture_path.write_text(json.dumps(existing, indent=2) + "\n")


def classify_http_status(status: int, body: str) -> ErrorClass:
    lowered = body.lower()
    if status in (401, 403):
        return ErrorClass.AUTHENTICATION
    if status == 429:
        return ErrorClass.RATE_LIMIT
    if status == 402 or "insufficient quota" in lowered or "quota exceeded" in lowered:
        return ErrorClass.QUOTA_EXHAUSTED
    if "unsupported" in lowered or "not support" in lowered:
        return ErrorClass.UNSUPPORTED_CAPABILITY
    if status >= 500:
        return ErrorClass.TRANSIENT
    if "tool" in lowered and ("malformed" in lowered or "invalid" in lowered):
        return ErrorClass.INVALID_REQUEST
    if status == 400:
        return ErrorClass.INVALID_REQUEST
    return ErrorClass.UNKNOWN_OUTCOME


def normalize_openai_usage(raw: dict[str, Any] | None) -> dict[str, Any]:
    if not raw:
        return {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "confidence": "unknown",
        }
    prompt = raw.get("prompt_tokens")
    completion = raw.get("completion_tokens")
    total = raw.get("total_tokens")
    return {
        "input_tokens": prompt,
        "output_tokens": completion,
        "total_tokens": total,
        "confidence": "exact" if total is not None else "unknown",
        "raw_keys": sorted(raw.keys()),
    }
