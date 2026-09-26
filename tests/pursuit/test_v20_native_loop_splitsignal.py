from __future__ import annotations

from swarm.contracts.router_capabilities import RouteBilling, RouterCallReceipt
from swarm.evals.synthetic_harness import LiveGrant
from swarm.providers.router_client import ChatResult
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


def test_live_grant_ceilings_are_applied_to_native_loop(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    requests: list[dict[str, object]] = []

    class StubClient:
        def __init__(self, _base_url: str, **_kwargs: object) -> None:
            pass

        def close(self) -> None:
            pass

        def chat(self, body: dict[str, object]) -> ChatResult:
            requests.append(body)
            return ChatResult(
                body={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "function": {
                                            "name": "workspace.read",
                                            "arguments": "{}",
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
                receipt=RouterCallReceipt(
                    billing=RouteBilling.FREE,
                    usage_known=True,
                    prompt_tokens=1,
                    completion_tokens=1,
                ),
            )

    monkeypatch.setattr(native_loop, "SplitSignalClient", StubClient)
    grant = LiveGrant(
        grant_id="grant-bounded",
        routes=("mock/ok",),
        budget_usd=0.0,
        purpose="pursuit_native_loop",
        approved=True,
        free_routes_only=True,
        max_calls=1,
        max_tokens=7,
        max_wall_seconds=2,
    )
    loop, reason = native_loop_from_env(
        {"workspace.read": lambda _args: "ok"},
        grant=grant,
        env={"SPLITSIGNAL_BASE_URL": "http://s.test/v1", "SPLITSIGNAL_MODEL": "mock/ok"},
    )
    assert reason == "ready" and loop is not None
    result = loop.run("bounded")
    assert result.model_calls == 1
    assert result.status == "budget_exhausted"
    assert result.error_code == "max_model_calls"
    assert requests == [
        {
            "model": "mock/ok",
            "messages": [{"role": "user", "content": "bounded"}],
            "tools": [
                {
                    "type": "function",
                    "function": {"name": "workspace.read", "parameters": {"type": "object"}},
                }
            ],
            "max_tokens": 7,
        }
    ]
