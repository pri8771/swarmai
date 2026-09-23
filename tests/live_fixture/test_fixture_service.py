"""R30a — live local fixture service semantics (real subprocess, real HTTP via httpx)."""

from __future__ import annotations

import secrets
import socket
import threading
import time

import httpx
import pytest

pytestmark = pytest.mark.live_local

RID = "X-Fixture-Request-ID"
FAULT = "X-Fixture-Fault"


def _rid() -> str:
    return f"req_{secrets.token_hex(6)}"


def _state(url: str) -> dict:
    return httpx.get(f"{url}/_fixture/state", timeout=5).json()


def _login(url: str, creds: dict[str, str]) -> httpx.Client:
    client = httpx.Client(base_url=url, timeout=5, follow_redirects=False)
    response = client.post("/login", data={"user": creds["user"], "password": creds["password"]})
    assert response.status_code == 200, response.text
    assert "sid" in client.cookies
    return client


def test_idempotency_key_replay_creates_one_note(live_fixture_url: str) -> None:
    key = f"idem-{secrets.token_hex(4)}"
    body = {"client_ref": "c1", "text": "hello"}
    first = httpx.post(
        f"{live_fixture_url}/api/notes",
        json=body,
        headers={"Idempotency-Key": key, RID: _rid()},
        timeout=5,
    )
    assert first.status_code == 201 and first.json()["replayed"] is False
    second = httpx.post(
        f"{live_fixture_url}/api/notes",
        json=body,
        headers={"Idempotency-Key": key, RID: _rid()},
        timeout=5,
    )
    assert second.status_code == 200 and second.json()["replayed"] is True
    assert second.json()["id"] == first.json()["id"]
    assert len(_state(live_fixture_url)["notes"]) == 1
    missing = httpx.post(
        f"{live_fixture_url}/api/notes", json=body, headers={RID: _rid()}, timeout=5
    )
    assert missing.status_code == 400


def test_drop_response_after_commit_stores_note_and_client_sees_transport_error(
    live_fixture_url: str,
) -> None:
    rid = _rid()
    with pytest.raises(httpx.TimeoutException):
        httpx.post(
            f"{live_fixture_url}/api/notes",
            json={"client_ref": "drop", "text": "x"},
            headers={"Idempotency-Key": f"k-{rid}", RID: rid, FAULT: "drop_response_after_commit"},
            timeout=1.0,
        )
    notes = httpx.get(f"{live_fixture_url}/api/notes", params={"client_ref": "drop"}, timeout=5)
    assert len(notes.json()["notes"]) == 1  # committed although the client never saw it
    # The handler is still holding the dropped response: receipt is in_flight, not terminal.
    receipt = httpx.get(f"{live_fixture_url}/api/requests/{rid}", timeout=5).json()
    assert receipt["phase"] == "in_flight" and receipt["outcome"] is None


def test_fail_before_commit_stores_nothing(live_fixture_url: str) -> None:
    rid = _rid()
    response = httpx.post(
        f"{live_fixture_url}/api/notes",
        json={"client_ref": "fail", "text": "x"},
        headers={"Idempotency-Key": f"k-{rid}", RID: rid, FAULT: "fail_before_commit"},
        timeout=5,
    )
    assert response.status_code == 500
    assert (
        httpx.get(f"{live_fixture_url}/api/notes", params={"client_ref": "fail"}, timeout=5).json()[
            "notes"
        ]
        == []
    )
    receipt = httpx.get(f"{live_fixture_url}/api/requests/{rid}", timeout=5).json()
    assert receipt == {
        **receipt,
        "phase": "terminal",
        "outcome": "not_applied",
        "external_id": None,
    }


def test_submit_without_session_redirects_and_stores_nothing(live_fixture_url: str) -> None:
    rid = _rid()
    response = httpx.post(
        f"{live_fixture_url}/app/submit",
        json={"client_ref": "nosess", "text": "x"},
        headers={RID: rid},
        timeout=5,
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"].startswith("/login?next=%2Fapp%2Fform")
    state = _state(live_fixture_url)
    assert state["submissions"] == []
    assert state["submit_posts_received"] == 1
    assert state["requests"][rid]["outcome"] == "not_applied"


def test_session_expires_after_ttl(live_fixture_url: str, live_fixture_credentials) -> None:
    client = _login(live_fixture_url, live_fixture_credentials)
    assert client.get("/app/form").status_code == 200
    time.sleep(2.3)  # FIXTURE_SESSION_TTL_S default 2
    expired = client.get("/app/form")
    assert expired.status_code == 302 and "/login?next=%2Fapp%2Fform" in expired.headers["location"]


def test_submit_does_not_dedupe(live_fixture_url: str, live_fixture_credentials) -> None:
    client = _login(live_fixture_url, live_fixture_credentials)
    for _ in range(2):
        response = client.post(
            "/app/submit", json={"client_ref": "twice", "text": "same"}, headers={RID: _rid()}
        )
        assert response.status_code == 201
    rows = client.get("/app/submissions", params={"client_ref": "twice"}).json()["submissions"]
    assert len(rows) == 2  # a browser-like site gives no idempotency help


def test_login_next_rejects_absolute_and_scheme_relative_urls(live_fixture_url: str) -> None:
    for bad in ("http://evil.test/", "//evil.test/", "/\\evil", "javascript:alert(1)"):
        response = httpx.get(f"{live_fixture_url}/login", params={"next": bad}, timeout=5)
        assert response.status_code == 400, bad
    assert (
        httpx.get(f"{live_fixture_url}/login", params={"next": "/app/form"}, timeout=5).status_code
        == 200
    )
    trap = httpx.get(
        f"{live_fixture_url}/redirect",
        params={"to": "http://127.0.0.1:1/"},
        timeout=5,
        follow_redirects=False,
    )
    assert trap.status_code == 302 and trap.headers["location"] == "http://127.0.0.1:1/"


def test_service_binds_loopback_only(live_fixture_url: str) -> None:
    port = int(live_fixture_url.rsplit(":", 1)[1])
    hostname_ip = socket.gethostbyname(socket.gethostname())
    if hostname_ip.startswith("127."):
        pytest.skip("no non-loopback address to probe on this host")
    with pytest.raises(OSError):
        with socket.create_connection((hostname_ip, port), timeout=1):
            pass


def test_terminal_non_application_receipt_requires_stopped_handler(
    live_fixture_url: str, live_fixture_credentials
) -> None:
    client = _login(live_fixture_url, live_fixture_credentials)
    rid = _rid()
    rejected = client.post(
        "/app/submit",
        json={"client_ref": "rej", "text": "x"},
        headers={RID: rid, FAULT: "reject_403"},
    )
    assert rejected.status_code == 403
    receipt = client.get(f"/app/requests/{rid}").json()
    assert receipt["phase"] == "terminal" and receipt["outcome"] == "not_applied"
    assert client.get("/app/submissions", params={"client_ref": "rej"}).json()["submissions"] == []
    # Unknown ids are 404, never not_applied.
    assert client.get(f"/app/requests/{_rid()}").status_code == 404
    assert httpx.get(f"{live_fixture_url}/api/requests/{_rid()}", timeout=5).status_code == 404


def test_delayed_commit_is_in_flight_not_negative_proof(
    live_fixture_url: str, live_fixture_credentials
) -> None:
    client = _login(live_fixture_url, live_fixture_credentials)
    rid = _rid()
    done: list[int] = []

    def slow_post() -> None:
        r = client.post(
            "/app/submit",
            json={"client_ref": "slow", "text": "x"},
            headers={RID: rid, FAULT: "delay_before_commit_ms=1500"},
            timeout=10,
        )
        done.append(r.status_code)

    thread = threading.Thread(target=slow_post)
    thread.start()
    time.sleep(0.4)
    probe = httpx.Client(base_url=live_fixture_url, timeout=5, cookies=client.cookies)
    mid = probe.get(f"/app/requests/{rid}").json()
    assert mid["phase"] == "in_flight" and mid["outcome"] is None
    # Zero search results while in flight prove nothing about application.
    assert probe.get("/app/submissions", params={"client_ref": "slow"}).json()["submissions"] == []
    thread.join(timeout=10)
    assert done == [201]
    final = probe.get(f"/app/requests/{rid}").json()
    assert final["phase"] == "terminal" and final["outcome"] == "applied"
    assert (
        len(probe.get("/app/submissions", params={"client_ref": "slow"}).json()["submissions"]) == 1
    )


def test_request_id_payload_conflict_and_duplicate_handler_rejected(live_fixture_url: str) -> None:
    rid = _rid()
    first = httpx.post(
        f"{live_fixture_url}/api/notes",
        json={"client_ref": "dupid", "text": "a"},
        headers={"Idempotency-Key": f"k-{rid}", RID: rid},
        timeout=5,
    )
    assert first.status_code == 201
    conflict = httpx.post(
        f"{live_fixture_url}/api/notes",
        json={"client_ref": "dupid", "text": "DIFFERENT"},
        headers={"Idempotency-Key": f"k-{rid}", RID: rid},
        timeout=5,
    )
    assert conflict.status_code == 409 and conflict.json()["error"] == "request_id_payload_conflict"
    duplicate = httpx.post(
        f"{live_fixture_url}/api/notes",
        json={"client_ref": "dupid", "text": "a"},
        headers={"Idempotency-Key": f"k-{rid}", RID: rid},
        timeout=5,
    )
    assert duplicate.status_code == 409 and duplicate.json()["error"] == "duplicate_request_id"
    receipt = httpx.get(f"{live_fixture_url}/api/requests/{rid}", timeout=5).json()
    assert receipt["outcome"] == "applied" and receipt["external_id"] == first.json()["id"]
    assert (
        len(
            httpx.get(
                f"{live_fixture_url}/api/notes", params={"client_ref": "dupid"}, timeout=5
            ).json()["notes"]
        )
        == 1
    )
