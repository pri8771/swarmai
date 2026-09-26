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
