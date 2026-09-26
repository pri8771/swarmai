"""SW-W2-S2 / V20-E05 + E07: bounded native loop over the fake router; honest live blocker."""

from __future__ import annotations

from pathlib import Path

from swarm.api.store import ProductStore
from swarm.providers.router_client import RouterClient
from swarm.pursuit.models import ContributionKind, MissionProposalDraft
from swarm.pursuit.native_dispatch import NativeMissionDispatchExecutor
from swarm.pursuit.native_loop import BoundedNativeLoop, native_loop_from_env
from tests.fixtures.router_http.fake_router import FakeRouter

BASE = "http://router.invalid"


def _loop(scenario: str, tools: dict | None = None, **kw: int) -> tuple[BoundedNativeLoop, list]:
    calls: list[dict] = []

    def read(args: dict) -> str:
        calls.append(args)
        return "readme contents"

    fake = FakeRouter(scenario)
    router = RouterClient(BASE, transport=fake.transport)
    tool_map = {"workspace.read": read} if tools is None else tools
    return BoundedNativeLoop(router, tool_map, model="fake-free", **kw), calls


def test_tool_roundtrip_completes_within_bounds() -> None:
    loop, calls = _loop("tools")
    res = loop.run("summarize README")
    assert res.status == "completed" and res.final_text == "done after tool"
    assert (res.model_calls, res.tool_calls, res.turns) == (2, 1, 2)
    assert calls == [{"path": "README.md"}]
    assert res.usage_known and res.transcript_digest


def test_disallowed_tool_is_never_executed() -> None:
    loop, calls = _loop("tools", tools={})
    res = loop.run("x")
    assert res.status == "tool_denied" and res.error_code == "tool_not_allowed:workspace.read"
    assert calls == []


def test_model_call_budget_is_hard() -> None:
    loop, _ = _loop("tools", max_model_calls=1)
    res = loop.run("x")
    assert res.status == "budget_exhausted" and res.model_calls == 1


def test_router_errors_stop_the_loop() -> None:
    loop, _ = _loop("rate_limited")
    res = loop.run("x")
    assert (res.status, res.error_class) == ("router_error", "rate_limit")
    paid, _ = _loop("paid")
    res = paid.run("x")
    assert (res.error_class, res.error_code) == ("policy_denied", "paid_route_forbidden")


def test_missing_usage_is_reported_unknown() -> None:
    loop, _ = _loop("missing_usage")
    res = loop.run("x")
    assert res.status == "completed" and res.usage_known is False


def test_live_loop_requires_grant() -> None:
    assert native_loop_from_env({}, grant=None, env={}) == (None, "router_not_configured")
    env = {"SWARM_ROUTER_BASE_URL": BASE, "SWARM_ROUTER_MODEL": "fake-free"}
    loop, reason = native_loop_from_env({}, grant=None, env=env)
    assert loop is None and reason == "missing_live_grant"


def _proposal(goal_id: str = "goal_nl") -> MissionProposalDraft:
    return MissionProposalDraft(
        goal_id=goal_id,
        title="t",
        objective="summarize README",
        kind=ContributionKind.ACT,
        dedupe_key=f"{goal_id}:act:1",
        addresses_criteria=["c1"],
    )


def test_executor_records_loop_but_never_invents_success(tmp_path: Path) -> None:
    store = ProductStore(repo_root=tmp_path, db_reachable=None)
    loop, _ = _loop("tools")
    executor = NativeMissionDispatchExecutor(store, enqueue_worker_task=False, native_loop=loop)
    out = executor.execute(_proposal())
    assert out.success is False and out.failure_class == "submitted_pending"
    assert (out.model_calls, out.tool_calls, out.route_id) == (2, 1, "fake-free")
    plan = store.mission_store().load(out.mission_id).plan
    assert plan["native_loop"]["status"] == "completed"
    assert "readme contents" not in str(plan)


def test_executor_without_loop_records_honest_blocker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SWARM_ROUTER_BASE_URL", raising=False)
    store = ProductStore(repo_root=tmp_path, db_reachable=None)
    out = NativeMissionDispatchExecutor(store, enqueue_worker_task=False).execute(_proposal())
    plan = store.mission_store().load(out.mission_id).plan
    assert plan["native_loop"] == {"status": "blocked", "reason": "router_not_configured"}
    assert out.model_calls == 0 and out.success is False
