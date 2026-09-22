"""V2A-001 / ART-V12-BROKER-CONTRACT — operational ProductStore broker gating.

Proves:
- generic execute_mission wires the governed project-scoped broker;
- broker denial / missing broker prevents direct local_chat model execution;
- an admitted local route yields exact route/usage evidence.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from swarm.api.store import ProductStore
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.mission import Mission, SizeFeatures, TaskSpec
from swarm.mission.action_boundary import local_worktree_gateway
from swarm.mission.brokered_inference import build_local_mission_broker
from swarm.mission.worker import RepoWorker
from swarm.tools.fences import ActorContext


def _seed_extract_mission(store: ProductStore, *, project_id: str = "proj_a") -> str:
    mission = Mission(
        project_id=project_id,
        objective="extract fields from unfamiliar note: alpha=1 beta=two",
        acceptance_criteria=["operator review"],
        allowed_capabilities=["code.read"],
        data_scope_ids=["scope_local"],
        resource_policy_id="policy_default",
        max_wall_time_seconds=600,
        max_graph_nodes=20,
        max_active_sessions=2,
        max_model_calls=10,
        status=MissionStatus.RUNNING,
    )
    store.controller.missions[mission.id] = mission
    record = store._persist_mission_record(mission, source="test")
    record.plan = {
        "task_family": "extract",
        "support": {"supported": True},
        "required_checks": {
            "inference_ok": True,
            "nonempty_output": True,
            "no_known_answer_path": True,
        },
    }
    store.mission_store().save(record)
    return mission.id


@pytest.mark.asyncio
async def test_execute_mission_uses_broker_not_direct_local_chat(tmp_path: Path) -> None:
    store = ProductStore(repo_root=tmp_path, execution_mode="operational")
    mid = _seed_extract_mission(store)

    broker = build_local_mission_broker(repo_root=tmp_path, models=["gemma3:4b"])
    calls: list[str] = []

    async def _stub(request, ticket):  # type: ignore[no-untyped-def]
        from swarm.contracts.common import new_id, utc_now
        from swarm.contracts.enums import ReservationPhase, SettlementState
        from swarm.contracts.provider import AttemptReceipt, NormalizedUsage

        calls.append(ticket.route_id)
        broker.adapter.calls.append({"route_id": ticket.route_id})
        return AttemptReceipt(
            logical_call_id=ticket.logical_call_id,
            send_phase=ReservationPhase.SETTLED,
            finished_at=utc_now(),
            provider_request_id=new_id("prv_"),
            normalized_usage=NormalizedUsage(
                requests=1,
                input_tokens=11,
                output_tokens=7,
                extras={
                    "text": '{"alpha":"1","beta":"two","source":"note"}',
                    "ok": True,
                    "error": None,
                    "cost_usd": 0.0,
                },
            ),
            actual_route=ticket.route_id,
            settlement_state=SettlementState.SETTLED,
        )

    broker.adapter.execute_one = _stub  # type: ignore[method-assign]
    store._mission_broker = broker
    store._mission_broker_models = ("gemma3:4b",)

    def _boom(*_a, **_k):  # type: ignore[no-untyped-def]
        raise AssertionError("direct local_chat bypass is forbidden on operational path")

    with patch("swarm.mission.worker.local_chat", side_effect=_boom):
        body = await store.execute_mission(mid, actor="tester", model="gemma3:4b")

    assert calls == ["rt_ollama_gemma3:4b"]
    assert body["broker"]["governed"] is True
    assert body["broker"]["project_id"] == "proj_a"
    assert body["broker"]["route_id"] == "rt_ollama_gemma3:4b"
    assert body["broker"]["prompt_tokens"] == 11
    assert body["broker"]["completion_tokens"] == 7
    assert body["broker"]["cost_usd"] == 0.0
    assert body["cost"]["total_usd"] == 0.0
    assert body["worker_ok"] is True
    broker.assert_all_calls_accounted()


@pytest.mark.asyncio
async def test_broker_denial_prevents_model_execution(tmp_path: Path) -> None:
    store = ProductStore(repo_root=tmp_path, execution_mode="operational")
    mid = _seed_extract_mission(store, project_id="proj_deny")

    # Zero remaining quota → QuotaExhaustedError mapped to broker_denied.
    deny_broker = build_local_mission_broker(
        repo_root=tmp_path, models=["gemma3:4b"], request_limit=0
    )
    store._mission_broker = deny_broker
    store._mission_broker_models = ("gemma3:4b",)

    adapter_calls_before = len(deny_broker.adapter.calls)

    def _boom(*_a, **_k):  # type: ignore[no-untyped-def]
        raise AssertionError("denied broker must not fall back to local_chat")

    with patch("swarm.mission.worker.local_chat", side_effect=_boom):
        body = await store.execute_mission(mid, actor="tester", model="gemma3:4b")

    assert body["worker_ok"] is False
    assert body["accepted"] is False
    assert body["status"] == MissionStatus.FAILED.value
    err = str(body["broker"]["error"] or "")
    assert "broker_denied" in err or "QuotaExhausted" in err
    assert len(deny_broker.adapter.calls) == adapter_calls_before
    assert body["cost"]["total_usd"] == 0.0


def test_require_broker_blocks_direct_local_chat_fallback(tmp_path: Path) -> None:
    task = TaskSpec(
        mission_id="msn_x",
        project_id="proj_x",
        objective="extract fields: a=1",
        task_family="extract",
        size_features=SizeFeatures(),
        inputs={"goal": "extract fields: a=1"},
        output_schema_id="generic_json",
        quality_policy_id="policy_default",
        status=TaskStatus.READY,
    )
    worker = RepoWorker(
        tmp_path,
        model="gemma3:4b",
        broker=None,
        project_id="proj_x",
        action_gateway=local_worktree_gateway(tmp_path),
        actor_context=ActorContext(actor="test", project_id="proj_x"),
        require_broker=True,
    )

    def _boom(*_a, **_k):  # type: ignore[no-untyped-def]
        raise AssertionError("require_broker must not call local_chat")

    with patch("swarm.mission.worker.local_chat", side_effect=_boom):
        result, _ = worker.run_task(task, mission_id="msn_x", prior={})

    assert result.ok is False
    assert result.inference is not None
    assert result.inference.get("error") == "broker_required_but_missing"


def test_unregistered_route_is_broker_denial_without_local_chat(tmp_path: Path) -> None:
    broker = build_local_mission_broker(repo_root=tmp_path, models=["other-only"])
    worker = RepoWorker(
        tmp_path,
        model="gemma3:4b",
        broker=broker,
        project_id="proj_x",
        action_gateway=local_worktree_gateway(tmp_path),
        actor_context=ActorContext(actor="test", project_id="proj_x"),
        require_broker=True,
    )
    task = TaskSpec(
        mission_id="msn_y",
        project_id="proj_x",
        objective="extract fields: a=1",
        task_family="extract",
        size_features=SizeFeatures(),
        inputs={"goal": "extract fields: a=1"},
        output_schema_id="generic_json",
        quality_policy_id="policy_default",
        status=TaskStatus.READY,
    )

    def _boom(*_a, **_k):  # type: ignore[no-untyped-def]
        raise AssertionError("unregistered route must not fall back to local_chat")

    with patch("swarm.mission.worker.local_chat", side_effect=_boom):
        # Also patch adapter local path used only after admission.
        with patch.object(
            broker.adapter,
            "execute_one",
            side_effect=AssertionError("adapter must not run without admission"),
        ):
            result, _ = worker.run_task(task, mission_id="msn_y", prior={})

    assert result.ok is False
    assert result.inference is not None
    assert result.inference.get("error") == "route_not_registered_for_broker"
