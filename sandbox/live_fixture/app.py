"""R30a — live local fixture service (real HTTP, separate process, in-memory state).

Test infrastructure only: nothing under ``src/`` may import this package. It
exists so V1.7 adapters can be exercised against a *real* HTTP server whose
faults (response loss, pre-commit failure, delayed commit, session expiry,
unsafe redirects) are controlled by request headers.

Credentials come from the environment at run time (``FIXTURE_USER`` /
``FIXTURE_PASSWORD``); nothing is committed.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

FAULT_HEADER = "X-Fixture-Fault"
REQUEST_ID_HEADER = "X-Fixture-Request-ID"
IDEMPOTENCY_HEADER = "Idempotency-Key"
# How long a "dropped" response is held; longer than any client timeout used in tests.
DROP_HOLD_SECONDS = float(os.environ.get("FIXTURE_DROP_HOLD_S", "5"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


class FixtureState:
    """All state is in memory and empty at start."""

    def __init__(self) -> None:
        self.notes: dict[str, dict[str, Any]] = {}
        self.notes_by_idempotency_key: dict[str, str] = {}
        self.submissions: list[dict[str, Any]] = []
        self.logins: int = 0
        self.submit_posts_received: int = 0
        self.sessions: dict[str, float] = {}  # sid -> expires_at (monotonic)
        # request_id -> receipt (see REQUEST_ID_HEADER semantics in the R30a spec)
        self.requests: dict[str, dict[str, Any]] = {}

    def session_ttl(self) -> float:
        return float(os.environ.get("FIXTURE_SESSION_TTL_S", "2"))

    def session_alive(self, sid: str | None) -> bool:
        if not sid or sid not in self.sessions:
            return False
        if self.sessions[sid] <= time.monotonic():
            del self.sessions[sid]
            return False
        return True

    def snapshot(self) -> dict[str, Any]:
        return {
            "notes": list(self.notes.values()),
            "submissions": list(self.submissions),
            "logins": self.logins,
            "submit_posts_received": self.submit_posts_received,
            "requests": dict(self.requests),
        }


class Fault:
    def __init__(self, raw: str | None) -> None:
        self.kind = None
        self.delay_ms = 0
        self.delay_before_commit_ms = 0
        for part in (raw or "").split(";"):
            part = part.strip()
            if not part:
                continue
            if part.startswith("delay_ms="):
                self.delay_ms = int(part.split("=", 1)[1])
            elif part.startswith("delay_before_commit_ms="):
                self.delay_before_commit_ms = int(part.split("=", 1)[1])
            else:
                self.kind = part


def _safe_next(next_path: str | None) -> str | None:
    """Same-origin relative path only: starts with '/', not '//', no scheme, no backslash."""
    if not next_path or not next_path.startswith("/") or next_path.startswith("//"):
        return None
    if "\\" in next_path or ":" in next_path.split("?", 1)[0]:
        return None
    return next_path


def create_app() -> FastAPI:
    app = FastAPI(title="swarm-live-fixture")
    state = FixtureState()
    app.state.fixture = state

    def begin_request(
        request_id: str | None, payload: Any, client_ref: str | None
    ) -> tuple[dict[str, Any] | None, Response | None]:
        if not request_id:
            return None, JSONResponse({"error": "missing_request_id"}, status_code=400)
        digest = _digest(payload)
        existing = state.requests.get(request_id)
        if existing is not None:
            if existing["payload_digest"] != digest:
                return None, JSONResponse(
                    {"error": "request_id_payload_conflict", "receipt": existing},
                    status_code=409,
                )
            # Never run a second handler for the same request id, in flight or terminal.
            return None, JSONResponse(
                {"error": "duplicate_request_id", "receipt": existing}, status_code=409
            )
        receipt = {
            "request_id": request_id,
            "payload_digest": digest,
            "client_ref": client_ref,
            "phase": "in_flight",
            "outcome": None,
            "external_id": None,
        }
        state.requests[request_id] = receipt
        return receipt, None

    def finish(receipt: dict[str, Any], *, outcome: str, external_id: str | None) -> None:
        receipt["outcome"] = outcome
        receipt["external_id"] = external_id
        receipt["phase"] = "terminal"

    async def apply_fault_and_commit(
        fault: Fault, receipt: dict[str, Any], commit
    ) -> tuple[Any | None, Response | None]:
        """Run the fault plan around a commit callable. Terminal receipts are written
        only after all work for the request has stopped."""
        if fault.kind == "reject_403":
            finish(receipt, outcome="not_applied", external_id=None)
            return None, JSONResponse({"error": "forbidden"}, status_code=403)
        if fault.kind == "redirect":
            finish(receipt, outcome="not_applied", external_id=None)
            return None, RedirectResponse("http://127.0.0.1:1/", status_code=302)
        if fault.kind == "fail_before_commit":
            finish(receipt, outcome="not_applied", external_id=None)
            return None, JSONResponse({"error": "internal"}, status_code=500)
        if fault.delay_before_commit_ms:
            await asyncio.sleep(fault.delay_before_commit_ms / 1000)  # still in_flight
        stored = commit()
        if fault.delay_ms:
            await asyncio.sleep(fault.delay_ms / 1000)
        if fault.kind == "drop_response_after_commit":
            # The work is committed; the client never gets the response. Hold longer
            # than any client timeout, then stop; the receipt turns terminal only then.
            await asyncio.sleep(DROP_HOLD_SECONDS)
            finish(receipt, outcome="applied", external_id=stored.get("id"))
            return stored, None
        finish(receipt, outcome="applied", external_id=stored.get("id"))
        return stored, None

    # ---------------- API-style endpoints
    @app.post("/api/notes")
    async def create_note(
        request: Request,
        idempotency_key: str | None = Header(default=None, alias=IDEMPOTENCY_HEADER),
        request_id: str | None = Header(default=None, alias=REQUEST_ID_HEADER),
        fault: str | None = Header(default=None, alias=FAULT_HEADER),
    ) -> Response:
        body = await request.json()
        if not idempotency_key:
            return JSONResponse({"error": "missing_idempotency_key"}, status_code=400)
        receipt, err = begin_request(
            request_id, {"body": body, "key": idempotency_key}, body.get("client_ref")
        )
        if err is not None:
            return err
        assert receipt is not None
        plan = Fault(fault)
        existing_id = state.notes_by_idempotency_key.get(idempotency_key)
        if existing_id is not None:
            finish(receipt, outcome="applied", external_id=existing_id)
            return JSONResponse(
                {**state.notes[existing_id], "replayed": True},
                status_code=200,
                headers={REQUEST_ID_HEADER: request_id or ""},
            )

        def commit() -> dict[str, Any]:
            note_id = f"note_{secrets.token_hex(6)}"
            note = {"id": note_id, "client_ref": body.get("client_ref"), "text": body.get("text")}
            state.notes[note_id] = note
            state.notes_by_idempotency_key[idempotency_key] = note_id
            return note

        stored, err = await apply_fault_and_commit(plan, receipt, commit)
        if err is not None:
            return err
        assert stored is not None
        return JSONResponse(
            {**stored, "replayed": False},
            status_code=201,
            headers={REQUEST_ID_HEADER: request_id or ""},
        )

    @app.get("/api/notes")
    async def list_notes(client_ref: str | None = None) -> dict[str, Any]:
        notes = [
            n for n in state.notes.values() if client_ref is None or n["client_ref"] == client_ref
        ]
        return {"notes": notes}

    @app.get("/api/notes/{note_id}")
    async def get_note(note_id: str) -> Response:
        note = state.notes.get(note_id)
        if note is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return JSONResponse(note)

    @app.get("/api/requests/{request_id}")
    async def api_request_receipt(request_id: str) -> Response:
        receipt = state.requests.get(request_id)
        if receipt is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return JSONResponse(receipt)

    # ---------------- session-style endpoints
    @app.post("/login")
    async def login(request: Request) -> Response:
        form = await request.form()
        user = str(form.get("user") or "")
        password = str(form.get("password") or "")
        expected_user = os.environ.get("FIXTURE_USER") or ""
        expected_password = os.environ.get("FIXTURE_PASSWORD") or ""
        if not expected_password or not (
            secrets.compare_digest(user, expected_user)
            and secrets.compare_digest(password, expected_password)
        ):
            return JSONResponse({"error": "invalid_credentials"}, status_code=401)
        sid = secrets.token_hex(16)
        state.sessions[sid] = time.monotonic() + state.session_ttl()
        state.logins += 1
        response = JSONResponse({"ok": True})
        response.set_cookie("sid", sid, httponly=True, samesite="lax")
        return response

    @app.get("/login")
    async def login_page(next: str | None = None) -> Response:
        if next is not None and _safe_next(next) is None:
            return JSONResponse({"error": "unsafe_next"}, status_code=400)
        return JSONResponse({"login": "form", "next": next})

    @app.post("/logout")
    async def logout(request: Request) -> Response:
        sid = request.cookies.get("sid")
        state.sessions.pop(sid or "", None)
        response = JSONResponse({"ok": True})
        response.delete_cookie("sid")
        return response

    def require_session(request: Request, original: str) -> Response | None:
        if state.session_alive(request.cookies.get("sid")):
            return None
        return RedirectResponse("/login?" + urlencode({"next": original}), status_code=302)

    @app.get("/app/form")
    async def app_form(request: Request) -> Response:
        denied = require_session(request, "/app/form")
        if denied is not None:
            return denied
        return JSONResponse({"form": "ready"})

    @app.get("/app/submissions")
    async def app_submissions(request: Request, client_ref: str | None = None) -> Response:
        original = "/app/submissions" + (f"?client_ref={client_ref}" if client_ref else "")
        denied = require_session(request, original)
        if denied is not None:
            return denied
        rows = [s for s in state.submissions if client_ref is None or s["client_ref"] == client_ref]
        return JSONResponse({"submissions": rows})

    @app.post("/app/submit")
    async def app_submit(
        request: Request,
        request_id: str | None = Header(default=None, alias=REQUEST_ID_HEADER),
        fault: str | None = Header(default=None, alias=FAULT_HEADER),
    ) -> Response:
        state.submit_posts_received += 1
        body = await request.json()
        receipt, err = begin_request(request_id, {"body": body}, body.get("client_ref"))
        if err is not None:
            return err
        assert receipt is not None
        if not state.session_alive(request.cookies.get("sid")):
            # Expired/signed-out: nothing stored; terminal non-application.
            finish(receipt, outcome="not_applied", external_id=None)
            return RedirectResponse("/login?" + urlencode({"next": "/app/form"}), status_code=302)

        def commit() -> dict[str, Any]:
            row = {
                "id": f"sub_{secrets.token_hex(6)}",
                "client_ref": body.get("client_ref"),
                "text": body.get("text"),
            }
            state.submissions.append(row)  # deliberately no de-duplication
            return row

        stored, err = await apply_fault_and_commit(Fault(fault), receipt, commit)
        if err is not None:
            return err
        assert stored is not None
        return JSONResponse(stored, status_code=201, headers={REQUEST_ID_HEADER: request_id or ""})

    @app.get("/app/requests/{request_id}")
    async def app_request_receipt(request: Request, request_id: str) -> Response:
        denied = require_session(request, f"/app/requests/{request_id}")
        if denied is not None:
            return denied
        receipt = state.requests.get(request_id)
        if receipt is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return JSONResponse(receipt)

    @app.get("/redirect")
    async def unsafe_redirect(to: str) -> Response:
        return RedirectResponse(to, status_code=302)

    # ---------------- introspection
    @app.get("/_fixture/state")
    async def fixture_state() -> dict[str, Any]:
        return state.snapshot()

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
