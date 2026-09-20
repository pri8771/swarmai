"""P10 durable agent session runtime tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.broker.explain import build_mock_broker
from swarm.contracts.enums import AttemptStatus, TaskStatus
from swarm.contracts.fixtures import sample_route, sample_route_beta, sample_task
from swarm.contracts.mission import AgentProfile, TaskSpec
from swarm.contracts.workspace import ContextBundle, WorkerLease
from swarm.runtime.capacity import ResourceLimits
from swarm.runtime.checkpoint import CheckpointStore
from swarm.runtime.registry import SessionRegistry
from swarm.runtime.session import AgentSessionRuntime, HiddenCallDeniedError
from swarm.tools.builtins import register_builtin_tools
from swarm.tools.gateway import ToolGateway
from swarm.tools.registry import CapabilityRegistry
from swarm.workspace.service import SharedWorkspace


def _task(**updates: object) -> TaskSpec:
    data: dict[str, object] = {"required_capabilities": ["chat", "tools"]}
    data.update(updates)
    return sample_task().model_copy(update=data)


def _profile(role: str = "worker") -> AgentProfile:
    return AgentProfile(
        role=role,
        instructions_version="v1",
        context_policy="scoped",
        delegation_policy="propose_only",
        tool_scope=["calc"],
    )


def _lease() -> WorkerLease:
    return WorkerLease(
        node_identity="local-dev",
        architecture="arm64",
        runtime_version="0.1.0",
        capacity_units=1.0,
        lease_generation=1,
    )


def _context(task: TaskSpec) -> ContextBundle:
    return ContextBundle(
        mission_id=task.mission_id,
        task_id=task.id,
        graph_revision=1,
        policy_version="v1",
        token_estimate=40,
    )


def _runtime(tmp_path: Path) -> AgentSessionRuntime:
    broker = build_mock_broker()
    registry = CapabilityRegistry()
    register_builtin_tools(registry)
    gateway = ToolGateway(
        registry,
        allowed_scopes={"calc", "workspace.read", "scope_repo_demo"},
        current_lease_generation=1,
    )
    ws = SharedWorkspace(tmp_path / "arts", text_only=True)
    return AgentSessionRuntime(
        broker,
        tool_gateway=gateway,
        workspace=ws,
        limits=ResourceLimits(max_model_calls=10, max_concurrent_sessions=8),
        checkpoint_store=CheckpointStore(tmp_path / "cps"),
    )


@pytest.mark.asyncio
async def test_heterogeneous_multi_model_run(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()
    ctx = _context(task)
    lease = _lease()
    a = await rt.run_task(
        task, ctx, lease, profile=_profile("planner"), route=sample_route()
    )
    task_b = _task().model_copy(update={"id": "task_demo_002"})
    b = await rt.run_task(
        task_b, _context(task_b), lease, profile=_profile("worker"), route=sample_route_beta()
    )
    assert a.status == AttemptStatus.SUCCEEDED
    assert b.status == AttemptStatus.SUCCEEDED
    assert a.selected_route_id != b.selected_route_id
    assert rt.broker.request_count == 2
    rt.broker.assert_all_calls_accounted()


@pytest.mark.asyncio
async def test_broker_sees_every_call_and_replay_keeps_route(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()
    attempt = await rt.run_task(
        task, _context(task), _lease(), profile=_profile(), route=sample_route()
    )
    session = next(iter(rt.registry._sessions.values()))  # noqa: SLF001
    assert session.checkpoint_ref
    resumed = await rt.resume(session.checkpoint_ref)
    assert resumed.selected_route_id == attempt.selected_route_id
    assert rt.broker.request_count == 1
    rt.broker.assert_all_calls_accounted()


@pytest.mark.asyncio
async def test_hidden_summarization_denied(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()
    with pytest.raises(HiddenCallDeniedError):
        await rt.run_task(
            task,
            _context(task),
            _lease(),
            profile=_profile(),
            route=sample_route(),
            allow_hidden_summary=True,
        )


@pytest.mark.asyncio
async def test_task_cancellation(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()
    profile = _profile()

    class SpyDict(dict):  # type: ignore[type-arg]
        def __setitem__(self, key: str, value: object) -> None:
            dict.__setitem__(self, key, value)
            rt._cancel.add(key)

    rt._attempts = SpyDict()  # type: ignore[assignment]
    out = await rt.run_task(
        task, _context(task), _lease(), profile=profile, route=sample_route()
    )
    assert out.status == AttemptStatus.CANCELLED


@pytest.mark.asyncio
async def test_interrupted_model_response(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()

    class SpyDict(dict):  # type: ignore[type-arg]
        def __setitem__(self, key: str, value: object) -> None:
            dict.__setitem__(self, key, value)
            rt._interrupted.add(key)

    rt._attempts = SpyDict()  # type: ignore[assignment]
    out = await rt.run_task(
        task, _context(task), _lease(), profile=_profile(), route=sample_route()
    )
    assert out.status == AttemptStatus.UNKNOWN
    assert out.blocked_reason and "ambiguous" in out.blocked_reason


@pytest.mark.asyncio
async def test_tool_state_recovery(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()
    attempt = await rt.run_task(
        task, _context(task), _lease(), profile=_profile(), route=sample_route()
    )
    assert attempt.status == AttemptStatus.SUCCEEDED
    session = next(
        s for s in rt.registry._sessions.values() if s.assigned_task_id == task.id  # noqa: SLF001
    )
    cp = rt.checkpoints.load(session.checkpoint_ref or "")
    assert cp.tool_operation_ids
    for op in cp.tool_operation_ids:
        receipt = await rt.tools.receipt(op)  # type: ignore[union-attr]
        assert receipt.operation_id == op
    resumed = await rt.resume(session.checkpoint_ref or "")
    assert resumed.attempt_id == attempt.attempt_id


@pytest.mark.asyncio
async def test_blocked_child_releases_capacity(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task().model_copy(
        update={
            "dependency_ids": ["child_1", "child_2"],
            "status": TaskStatus.WAITING_CHILDREN,
        }
    )
    out = await rt.run_task(
        task,
        _context(task),
        _lease(),
        profile=_profile(),
        route=sample_route(),
        deterministic=True,
    )
    assert out.blocked_reason == "waiting_for_children"
    assert rt.capacity.runnable_count() == 0
    assert len(rt.capacity.waiting_sessions) == 1
    t2 = _task().model_copy(update={"id": "task_free"})
    out2 = await rt.run_task(
        t2, _context(t2), _lease(), profile=_profile(), deterministic=True
    )
    assert out2.status == AttemptStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_unsupported_provider_feature(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task().model_copy(update={"required_capabilities": ["vision.ocr"]})
    out = await rt.run_task(
        task, _context(task), _lease(), profile=_profile(), route=sample_route()
    )
    assert out.status == AttemptStatus.FAILED
    assert out.blocked_reason and "unsupported" in out.blocked_reason


def test_stable_registration_not_per_session() -> None:
    reg = SessionRegistry(max_registrations=8)
    profile = _profile("planner")
    for i in range(20):
        reg.open_session(profile, task_id=f"t{i}")
    assert reg.session_count() == 20
    assert reg.registration_count() == 1


@pytest.mark.asyncio
async def test_authorized_reroute_new_attempt(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()
    first = await rt.run_task(
        task, _context(task), _lease(), profile=_profile(), route=sample_route()
    )
    second = rt.safe_reroute_new_attempt(task, _profile(), sample_route_beta())
    assert second.attempt_id != first.attempt_id
    assert second.selected_route_id == sample_route_beta().route_id
    assert first.selected_route_id == sample_route().route_id


@pytest.mark.asyncio
async def test_checkpoint_excludes_secrets(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()
    await rt.run_task(task, _context(task), _lease(), profile=_profile(), route=sample_route())
    session = next(iter(rt.registry._sessions.values()))  # noqa: SLF001
    cp = rt.checkpoints.load(session.checkpoint_ref or "")
    serial = cp.to_serializable()
    assert "runtime_client" not in serial
    blob = str(serial).lower()
    assert "sk-" not in blob
    assert "secret=" not in blob


@pytest.mark.asyncio
async def test_deterministic_and_model_workers(tmp_path: Path) -> None:
    rt = _runtime(tmp_path)
    task = _task()
    det = await rt.run_task(
        task,
        _context(task),
        _lease(),
        profile=_profile("deterministic"),
        deterministic=True,
    )
    assert det.status == AttemptStatus.SUCCEEDED
    assert rt.broker.request_count == 0
