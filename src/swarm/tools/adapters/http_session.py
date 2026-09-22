"""R31a fixed-loopback session transport; cookies remain in process only."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from threading import RLock
from typing import Any
from urllib.parse import urlsplit

import httpx

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, AdapterManifest
from swarm.tools.adapters.base import AdapterDeniedError

_ORIGIN = re.compile(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})")
_ALIAS = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_PATHS = {"page.open": "/app/form", "form.submit": "/app/submit"}


def _origin(value: str) -> str:
    match = _ORIGIN.fullmatch(value)
    if match is None or int(match[1]) > 65535:
        raise AdapterDeniedError("invalid_session_origin")
    return value


class SessionJar:
    """Origin-bound, memory-only cookies; no login or persistence implementation."""

    def __init__(self, origin: str, *, transport: httpx.BaseTransport | None = None) -> None:
        self.origin = _origin(origin)
        self._transport = transport
        self._cookies: dict[str, httpx.Cookies] = {}
        self._secret_values: set[str] = set()
        self._lock = RLock()

    @contextmanager
    def _client(self, alias: str, timeout: int) -> Iterator[httpx.Client]:
        if not _ALIAS.fullmatch(alias):
            raise AdapterDeniedError("invalid_session_alias")
        with self._lock:
            cookies = self._cookies.setdefault(alias, httpx.Cookies())
            self._secret_values.update(cookie.value for cookie in cookies.jar if cookie.value)
            with httpx.Client(
                base_url=self.origin,
                cookies=cookies,
                timeout=timeout,
                follow_redirects=False,
                trust_env=False,
                transport=self._transport,
                event_hooks={"response": [self._remember_response_cookies]},
            ) as client:
                try:
                    yield client
                finally:
                    self._cookies[alias] = httpx.Cookies(client.cookies)
                    self._secret_values.update(
                        cookie.value for cookie in client.cookies.jar if cookie.value
                    )

    def _remember_response_cookies(self, response: httpx.Response) -> None:
        # Reconciliation can rotate cookies between its two GETs. Record each
        # response before a later response replaces or deletes that value.
        with self._lock:
            self._secret_values.update(
                cookie.value for cookie in response.cookies.jar if cookie.value
            )

    def _safe_external_id(self, value: Any) -> bool:
        # The fixture issues exactly this identifier shape. Retain only cookie
        # values in memory, including rotations, to reject reflected secrets.
        with self._lock:
            return (
                isinstance(value, str)
                and re.fullmatch(r"sub_[0-9a-f]{12}", value) is not None
                and not any(secret in value for secret in self._secret_values)
            )

    def authenticate(self, alias: str, fn: Callable[[httpx.Client], None]) -> None:
        """Future separately authorized human-auth hook; never called by adapter."""
        with self._client(alias, 30) as client:
            fn(client)


class HttpSessionAdapter:
    def __init__(self, manifest: AdapterManifest, *, sessions: SessionJar) -> None:
        if manifest.adapter_class != "http_session":
            raise ValueError("adapter_class_mismatch")
        self.manifest = AdapterManifest.model_validate(manifest.model_dump())
        self._sessions = sessions

    def normalize(self, request: dict[str, Any]) -> ActionEnvelope:
        operation = str(request.get("operation", "page.open"))
        declaration = self.manifest.operations.get(operation)
        if operation not in _PATHS or declaration is None:
            raise AdapterDeniedError("unknown_operation")
        payload = {"session_alias": request.get("session_alias", "session_local")}
        if operation == "form.submit":
            payload["text"] = request.get("text", "")
        envelope = ActionEnvelope(
            project_id=str(request["project_id"]),
            actor=str(request.get("actor", "worker")),
            integration_id=self.manifest.integration_id,
            integration_version=self.manifest.integration_version,
            operation=operation,
            destination=str(request.get("destination", "")),
            normalized_payload=payload,
            requested_scopes=list(declaration.scopes),
            side_effect_class=declaration.side_effect_class,
            risk_class=declaration.risk_class,
            lease_generation=request.get("lease_generation"),
            cancellation_generation=request.get("cancellation_generation"),
            policy_version=str(request.get("policy_version", "v17-policy-1")),
            mission_id=request.get("mission_id"),
            task_id=request.get("task_id"),
            attempt_id=request.get("attempt_id"),
            approval_id=request.get("approval_id"),
        )
        self.validate(envelope)
        return envelope.ensure_hashes()

    def validate(self, envelope: ActionEnvelope) -> None:
        if (envelope.integration_id, envelope.integration_version) != (
            self.manifest.integration_id,
            self.manifest.integration_version,
        ):
            raise AdapterDeniedError("integration_mismatch")
        path = _PATHS.get(envelope.operation)
        if path is None or envelope.destination != self._sessions.origin + path:
            raise AdapterDeniedError("destination_denied")
        payload = envelope.normalized_payload
        expected = (
            {"session_alias", "text"} if envelope.operation == "form.submit" else {"session_alias"}
        )
        alias = payload.get("session_alias")
        if set(payload) != expected or not isinstance(alias, str) or not _ALIAS.fullmatch(alias):
            raise AdapterDeniedError("invalid_session_payload")
        if envelope.operation == "form.submit" and not isinstance(payload["text"], str):
            raise AdapterDeniedError("invalid_submit_text")
        if not 0 < envelope.timeout_seconds <= 120:
            raise AdapterDeniedError("invalid_timeout")

    def observe_pre_state(self, envelope: ActionEnvelope) -> dict[str, Any]:
        self.validate(envelope)
        return {"session_alias": envelope.normalized_payload["session_alias"]}

    def _wire(self, envelope: ActionEnvelope) -> tuple[dict[str, str], str, str]:
        attempt = envelope.execution_attempt
        if type(attempt) is not int or attempt < 1:
            raise AdapterDeniedError("durable_execution_attempt_required")
        if not envelope.effect_key:
            raise AdapterDeniedError("effect_key_required")
        ref = hashlib.sha256(envelope.effect_key.encode()).hexdigest()[:32]
        request_id = hashlib.sha256(
            f"{envelope.effect_key}:attempt:{attempt}".encode()
        ).hexdigest()[:32]
        body = {"client_ref": ref, "text": str(envelope.normalized_payload["text"])}
        digest = hashlib.sha256(
            json.dumps({"body": body}, sort_keys=True, default=str).encode()
        ).hexdigest()
        return body, request_id, digest

    def _login_redirect(self, response: httpx.Response) -> bool:
        location = response.headers.get("location", "")
        if response.status_code != 302 or any(ord(c) < 32 or c == "\\" for c in location):
            return False
        try:
            target = urlsplit(location)
        except ValueError:
            return False
        if target.fragment or target.path != "/login":
            return False
        if target.scheme or target.netloc:
            return f"{target.scheme}://{target.netloc}" == self._sessions.origin
        return location.startswith("/login") and not location.startswith("//")

    @staticmethod
    def _json(response: httpx.Response) -> dict[str, Any] | None:
        if len(response.content) > 1024 * 1024:
            return None
        try:
            value = response.json()
        except ValueError:
            return None
        return value if isinstance(value, dict) else None

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        self.validate(envelope)
        submit = envelope.operation == "form.submit"
        body, request_id, _ = self._wire(envelope) if submit else ({}, "", "")
        try:
            with self._sessions._client(
                envelope.normalized_payload["session_alias"], envelope.timeout_seconds
            ) as client:
                response = (
                    client.post(
                        envelope.destination,
                        json=body,
                        headers={"X-Fixture-Request-ID": request_id},
                    )
                    if submit
                    else client.get(envelope.destination)
                )
        except httpx.HTTPError:
            return {"outcome": "unknown", "reason": "transport_uncertain"}
        if self._login_redirect(response):
            return {
                "outcome": "unknown" if submit else "denied",
                "reason": "session_expired_during_submit" if submit else "session_expired",
                "safe_destination": "/app/form",
            }
        if response.is_redirect:
            return {"outcome": "denied", "reason": "unexpected_redirect"}
        value = self._json(response)
        if submit and 200 <= response.status_code < 300 and value is not None:
            if (
                value.get("client_ref") == body["client_ref"]
                and value.get("text") == body["text"]
                and self._sessions._safe_external_id(value.get("id"))
                and response.headers.get("X-Fixture-Request-ID") == request_id
            ):
                return {"outcome": "succeeded", "external_id": value["id"]}
        if not submit and response.status_code == 200 and value == {"form": "ready"}:
            return {"outcome": "succeeded", "navigated_to": "/app/form"}
        return {"outcome": "unknown", "reason": "response_unconfirmed"}

    def observe_post_state(
        self, envelope: ActionEnvelope, execution_result: dict[str, Any]
    ) -> dict[str, Any]:
        # execute emits only bounded, cookie-free fields; no HTTP response objects.
        return dict(execution_result)

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]:
        self.validate(envelope)
        if envelope.operation != "form.submit":
            return {"state": "unknown", "reason": "read_only_action"}
        body, request_id, digest = self._wire(envelope)
        try:
            with self._sessions._client(
                envelope.normalized_payload["session_alias"], envelope.timeout_seconds
            ) as client:
                receipt_response = client.get(f"/app/requests/{request_id}")
                if self._login_redirect(receipt_response):
                    return {
                        "state": "unknown",
                        "reason": "reauth_required_to_reconcile",
                        "safe_destination": "/app/form",
                    }
                if receipt_response.status_code != 200:
                    return {"state": "unknown", "reason": "request_proof_unavailable"}
                rows_response = client.get(
                    "/app/submissions", params={"client_ref": body["client_ref"]}
                )
        except httpx.HTTPError:
            return {"state": "unknown", "reason": "transport_uncertain"}
        if self._login_redirect(rows_response):
            return {
                "state": "unknown",
                "reason": "reauth_required_to_reconcile",
                "safe_destination": "/app/form",
            }
        receipt, data = self._json(receipt_response), self._json(rows_response)
        if rows_response.status_code != 200 or receipt is None or data is None:
            return {"state": "unknown", "reason": "reconciliation_unreadable"}
        rows = data.get("submissions")
        if (
            not isinstance(rows, list)
            or receipt.get("request_id") != request_id
            or receipt.get("client_ref") != body["client_ref"]
            or receipt.get("payload_digest") != digest
        ):
            return {"state": "unknown", "reason": "request_proof_mismatch"}
        if receipt.get("phase") != "terminal":
            return {"state": "unknown", "reason": "request_not_terminal"}
        if (
            receipt.get("outcome") == "not_applied"
            and receipt.get("external_id") is None
            and rows == []
        ):
            return {"state": "not_applied", "reason": "terminal_request_not_applied"}
        if (
            receipt.get("outcome") == "applied"
            and len(rows) == 1
            and isinstance(rows[0], dict)
            and rows[0].get("client_ref") == body["client_ref"]
            and rows[0].get("text") == body["text"]
            and self._sessions._safe_external_id(rows[0].get("id"))
            and rows[0]["id"] == receipt.get("external_id")
        ):
            return {"state": "succeeded", "external_id": rows[0]["id"]}
        return {"state": "unknown", "reason": "reconciliation_anomaly"}
