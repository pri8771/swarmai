"""R31a offline contract tests. Every HTTP request uses MockTransport."""

import hashlib
import json
from unittest.mock import patch

import httpx
import pytest

from swarm.tools.adapter_registry import AdapterRegistry, ToolAuthorizationError
from swarm.tools.adapters.base import AdapterDeniedError
from swarm.tools.adapters.http_session import HttpSessionAdapter, SessionJar
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.fences import ActorContext, StaticFenceProvider, StaticPolicyProvider
from swarm.tools.manifests import MANIFEST_DIR, load_manifest
from swarm.tools.v17_gateway import ConsequentialToolGateway

ORIGIN = "http://127.0.0.1:58763"
COOKIE = "offline-cookie-must-never-be-recorded"


def setup_adapter(handler):
    calls = []

    def recorded(request):
        calls.append(request)
        return handler(request)

    jar = SessionJar(ORIGIN, transport=httpx.MockTransport(recorded))
    jar.authenticate(
        "session_local",
        lambda client: client.cookies.set("fixture_session", COOKIE, domain="127.0.0.1", path="/"),
    )
    adapter = HttpSessionAdapter(load_manifest(MANIFEST_DIR / "http.session@1.json"), sessions=jar)
    return adapter, calls


def envelope(adapter, submit=True):
    value = adapter.normalize(
        dict(
            project_id="session-test",
            actor="worker",
            operation="form.submit" if submit else "page.open",
            destination=ORIGIN + ("/app/submit" if submit else "/app/form"),
            text="approved text",
            mission_id="mission-test",
            task_id="task-test",
            attempt_id="attempt-test",
            lease_generation=1,
            cancellation_generation=0,
        )
    )
    value.execution_attempt = 1
    return value


def identifiers(env):
    ref = hashlib.sha256(env.effect_key.encode()).hexdigest()[:32]
    request_id = hashlib.sha256(
        f"{env.effect_key}:attempt:{env.execution_attempt}".encode()
    ).hexdigest()[:32]
    body = {"client_ref": ref, "text": "approved text"}
    digest = hashlib.sha256(
        json.dumps({"body": body}, sort_keys=True, default=str).encode()
    ).hexdigest()
    return ref, request_id, digest


@pytest.mark.parametrize(
    "destination",
    [
        "http://localhost:58763/app/submit",
        "http://[::1]:58763/app/submit",
        ORIGIN + "/app/submit?x=1",
        ORIGIN + "/app/submit#x",
        ORIGIN + "/other",
        ORIGIN + "/app/../app/submit",
        ORIGIN + "/app%2fsubmit",
        ORIGIN + "/app/submit\\x",
        "http://user@127.0.0.1:58763/app/submit",
        ORIGIN + "/app/submit\n",
        "http://127.0.0.1:58764/app/submit",
        ORIGIN + "/app/submit?",
    ],
)
def test_exact_destination_before_transport(destination):
    adapter, calls = setup_adapter(lambda r: pytest.fail("transport must not run"))
    env = envelope(adapter)
    env.destination = destination
    with pytest.raises(AdapterDeniedError):
        adapter.execute(env)
    assert calls == []


@pytest.mark.parametrize("attempt", [None, 0, -1, True])
def test_missing_durable_attempt_never_dispatches(attempt):
    adapter, calls = setup_adapter(lambda r: pytest.fail("transport must not run"))
    env = envelope(adapter)
    env.execution_attempt = attempt
    with pytest.raises(AdapterDeniedError, match="durable_execution_attempt_required"):
        adapter.execute(env)
    assert calls == []


def test_attempt_identity_changes_wire_only_and_cookies_stay_private():
    def handler(request):
        body = json.loads(request.content)
        assert request.headers["cookie"] == "fixture_session=" + COOKIE
        assert "idempotency-key" not in request.headers
        return httpx.Response(
            201,
            json={"id": "sub_123456abcdef", **body},
            headers={"X-Fixture-Request-ID": request.headers["X-Fixture-Request-ID"]},
        )

    adapter, calls = setup_adapter(handler)
    env = envelope(adapter)
    before = env.model_dump_json()
    first = adapter.execute(env)
    env.execution_attempt = 2
    second = adapter.execute(env)
    assert first["outcome"] == second["outcome"] == "succeeded"
    assert calls[0].headers["X-Fixture-Request-ID"] != calls[1].headers["X-Fixture-Request-ID"]
    assert json.loads(calls[0].content) == json.loads(calls[1].content)
    assert env.model_dump_json() == before
    assert COOKIE not in json.dumps(
        [
            first,
            second,
            adapter.observe_pre_state(env),
            adapter.observe_post_state(env, first),
            before,
        ]
    )


@pytest.mark.parametrize("submit,expected", [(False, "denied"), (True, "unknown")])
def test_login_redirect_preserves_uncertainty_and_never_follows(submit, expected):
    adapter, calls = setup_adapter(
        lambda r: httpx.Response(302, headers={"location": "/login?next=%2Fapp%2Fform"})
    )
    result = adapter.execute(envelope(adapter, submit))
    assert result["outcome"] == expected and result["safe_destination"] == "/app/form"
    assert len(calls) == 1


@pytest.mark.parametrize(
    "location",
    [
        "http://127.0.0.1:1/login",
        "https://example.test/login",
        "//evil.test/login",
        "/login-extra",
        "/app/form",
        "/login\\x",
    ],
)
def test_unexpected_redirect_never_follows(location):
    adapter, calls = setup_adapter(lambda r: httpx.Response(302, headers={"location": location}))
    assert adapter.execute(envelope(adapter)) == {
        "outcome": "denied",
        "reason": "unexpected_redirect",
    }
    assert len(calls) == 1


def test_open_success_and_client_transport_policy():
    adapter, calls = setup_adapter(lambda r: httpx.Response(200, json={"form": "ready"}))
    with patch("swarm.tools.adapters.http_session.httpx.Client", wraps=httpx.Client) as client:
        assert adapter.execute(envelope(adapter, False)) == {
            "outcome": "succeeded",
            "navigated_to": "/app/form",
        }
    assert client.call_args.kwargs["follow_redirects"] is False
    assert client.call_args.kwargs["trust_env"] is False
    assert len(calls) == 1 and calls[0].method == "GET"


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("missing", "unknown"),
        ("in_flight", "unknown"),
        ("not_applied", "not_applied"),
        ("applied", "succeeded"),
        ("applied_no_rows", "unknown"),
        ("duplicate", "unknown"),
        ("wrong_id", "unknown"),
        ("wrong_digest", "unknown"),
        ("wrong_request", "unknown"),
        ("wrong_ref", "unknown"),
        ("not_applied_with_row", "unknown"),
        ("in_flight_with_row", "unknown"),
        ("login", "unknown"),
        ("malformed", "unknown"),
        ("unsafe_redirect", "unknown"),
    ],
)
def test_terminal_request_and_rows_must_agree(scenario, expected):
    def handler(request):
        ref, request_id, digest = identifiers(env)
        row = {"id": "sub_123456abcdef", "client_ref": ref, "text": "approved text"}
        if "/requests/" in request.url.path:
            assert request.url.path == "/app/requests/" + request_id
            if scenario == "missing":
                return httpx.Response(404, json={"error": "not_found"})
            if scenario == "login":
                return httpx.Response(302, headers={"location": "/login"})
            if scenario == "unsafe_redirect":
                return httpx.Response(302, headers={"location": "http://evil.test/"})
            if scenario == "malformed":
                return httpx.Response(200, content=b"{broken")
            return httpx.Response(
                200,
                json=dict(
                    request_id="wrong" if scenario == "wrong_request" else request_id,
                    client_ref="wrong" if scenario == "wrong_ref" else ref,
                    payload_digest="wrong" if scenario == "wrong_digest" else digest,
                    phase="in_flight" if scenario.startswith("in_flight") else "terminal",
                    outcome="not_applied" if scenario.startswith("not_applied") else "applied",
                    external_id=None if scenario.startswith("not_applied") else row["id"],
                ),
            )
        assert request.url.path == "/app/submissions" and request.url.params["client_ref"] == ref
        rows = [] if scenario in {"in_flight", "not_applied", "applied_no_rows"} else [row]
        if scenario == "duplicate":
            rows.append(dict(row, id="sub_abcdef123456"))
        if scenario == "wrong_id":
            row["id"] = "sub_abcdef123456"
        return httpx.Response(200, json={"submissions": rows})

    adapter, calls = setup_adapter(handler)
    env = envelope(adapter)
    result = adapter.reconcile(env, [])
    assert result["state"] == expected
    assert all(request.method == "GET" for request in calls)
    assert COOKIE not in json.dumps(result)
    if scenario == "login":
        assert result["reason"] == "reauth_required_to_reconcile"


@pytest.mark.parametrize("kind", ["timeout", "500", "invalid-success"])
def test_dispatch_failure_is_unknown(kind):
    def handler(request):
        if kind == "timeout":
            raise httpx.ReadTimeout("offline timeout")
        if kind == "500":
            return httpx.Response(500, json={"error": "fixture"})
        return httpx.Response(201, json={"id": "unbound"})

    adapter, calls = setup_adapter(handler)
    assert adapter.execute(envelope(adapter))["outcome"] == "unknown"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_submit_scope_alone_cannot_authorize_reconciliation_reads():
    adapter, calls = setup_adapter(lambda r: pytest.fail("transport must not run"))
    registry = AdapterRegistry()
    registry.register(adapter)
    gw = ConsequentialToolGateway(
        registry=registry,
        store=InMemoryEffectStore(),
        fences=StaticFenceProvider(1, 0),
        policy=StaticPolicyProvider({"web.submit"}, "v17-policy-1"),
    )
    env = envelope(adapter)
    env.requested_scopes = ["web.submit"]
    with pytest.raises(ToolAuthorizationError, match="denied_scopes.*web.read"):
        await gw.execute_envelope(
            env, context=ActorContext(actor="worker", project_id="session-test")
        )
    assert calls == []


@pytest.mark.parametrize("cookie", [COOKIE, "sub_123456abcdef"])
@pytest.mark.parametrize("phase", ["execute", "reconcile"])
def test_reflected_cookie_identifier_never_enters_output(cookie, phase):
    def handler(request):
        ref, request_id, digest = identifiers(env)
        row = {"id": cookie, "client_ref": ref, "text": "approved text"}
        if request.method == "POST":
            return httpx.Response(201, json=row, headers={"X-Fixture-Request-ID": request_id})
        if "/requests/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "request_id": request_id,
                    "client_ref": ref,
                    "payload_digest": digest,
                    "phase": "terminal",
                    "outcome": "applied",
                    "external_id": cookie,
                },
            )
        return httpx.Response(200, json={"submissions": [row]})

    adapter, _ = setup_adapter(handler)
    adapter._sessions.authenticate(
        "session_local",
        lambda client: client.cookies.set("fixture_session", cookie, domain="127.0.0.1", path="/"),
    )
    env = envelope(adapter)
    result = adapter.execute(env) if phase == "execute" else adapter.reconcile(env, [])
    assert result.get("outcome", result.get("state")) == "unknown"
    assert cookie not in json.dumps(result)


def test_intermediate_reconciliation_cookie_rotation_never_enters_output():
    intermediate = "sub_123456abcdef"

    def handler(request):
        ref, request_id, digest = identifiers(env)
        if "/requests/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "request_id": request_id,
                    "client_ref": ref,
                    "payload_digest": digest,
                    "phase": "terminal",
                    "outcome": "applied",
                    "external_id": intermediate,
                },
                headers={"set-cookie": f"fixture_session={intermediate}; Path=/"},
            )
        assert intermediate in request.headers["cookie"]
        return httpx.Response(
            200,
            json={
                "submissions": [{"id": intermediate, "client_ref": ref, "text": "approved text"}]
            },
            headers={"set-cookie": "fixture_session=final-rotated-cookie; Path=/"},
        )

    adapter, calls = setup_adapter(handler)
    env = envelope(adapter)
    result = adapter.reconcile(env, [])
    assert result["state"] == "unknown"
    assert intermediate not in json.dumps(result)
    assert len(calls) == 2
