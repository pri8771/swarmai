"""R28d: the async mission runtime must dispatch sync gateway work off-loop."""

from __future__ import annotations

import asyncio
import os
import subprocess
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import swarm.mission.worker as worker_module
from swarm.db.engine import create_db_engine
from swarm.db.models import Base
from swarm.mission.action_boundary import local_worktree_gateway
from swarm.mission.inference import InferenceResult
from swarm.mission.runtime import MissionRuntime
from swarm.mission.worker import RepoWorker, WorkerResult
from swarm.mission.worktree import WorktreeHandle, create_worktree, remove_worktree
from swarm.tools.adapters.local_sandbox import LocalSandboxAdapter
from swarm.tools.fences import ActorContext, RevocableFenceProvider
from swarm.tools.v17_gateway import CancellationFenceError


@pytest.fixture(autouse=True)
def runtime_effect_schema() -> Iterator[None]:
    """Exercise durable runtime effects when the test harness supplies PostgreSQL."""
    if not (os.environ.get("SWARM_DATABASE_URL") or "").strip():
        yield
        return
    engine = create_db_engine()
    Base.metadata.create_all(engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def _init_fixture_repo(repo: Path) -> None:
    """Create a tiny committed fixture repository for worktree-cleanup coverage."""

    (repo / "sandbox" / "selfdev_issue").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = 'runtime-probe'\nversion = '0'\n")
    (repo / "sandbox" / "selfdev_issue" / "parser_helper.py").write_text(
        "def inclusive_range_count(start: int, end: int) -> int:\n    return end - start\n",
        encoding="utf-8",
    )
    (repo / "sandbox" / "selfdev_issue" / "parser_helper_test.py").write_text(
        "from parser_helper import inclusive_range_count\n\n"
        "def test_inclusive_range_count() -> None:\n"
        "    assert inclusive_range_count(2, 4) == 3\n",
        encoding="utf-8",
    )
    for args in (
        ("init",),
        ("config", "user.email", "runtime-probe@example.invalid"),
        ("config", "user.name", "Runtime Probe"),
        ("add", "."),
        ("commit", "-m", "fixture"),
    ):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.mark.asyncio
async def test_runtime_runs_gateway_backed_sync_worker_off_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The production runtime reaches the real sync gateway from a worker thread."""

    observed_without_loop: list[str] = []

    class ProbeWorker:
        def __init__(
            self,
            _repo: Path,
            *,
            project_id: str,
            action_gateway: Any,
            actor_context: Any,
            **_kwargs: Any,
        ) -> None:
            self.project_id = project_id
            self.action_gateway = action_gateway
            self.actor_context = actor_context
            self.active_worktree = None

        def run_task(
            self,
            task: Any,
            *,
            mission_id: str,
            prior: dict[str, WorkerResult],
            shared_worktree: Any,
        ) -> tuple[WorkerResult, Any]:
            del prior
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                observed_without_loop.append(str(task.task_family))
            else:
                pytest.fail("sync_worker_ran_inside_mission_event_loop")

            adapter = self.action_gateway.registry.resolve("local.sandbox", "1")
            fence = self.action_gateway.fences.current(
                project_id=self.project_id,
                mission_id=mission_id,
                task_id=task.id,
                attempt_id=f"att_{task.id}",
            )
            request = {
                "operation": "fs.write_text",
                "path": f"runtime-bridge-{task.task_family}.txt",
                "text": f"{task.task_family}\n",
                "project_id": self.project_id,
                "actor": self.actor_context.actor,
                "mission_id": mission_id,
                "task_id": task.id,
                "attempt_id": f"att_{task.id}",
                "lease_generation": fence.lease_generation,
                "cancellation_generation": fence.cancellation_generation,
                "policy_version": self.action_gateway.policy.current_policy_version(
                    project_id=self.project_id
                ),
            }
            envelope = adapter.normalize(request)
            effect_key = f"{self.project_id}:{mission_id}:{task.id}:runtime-probe"
            envelope = envelope.model_copy(
                update={"effect_key": effect_key, "idempotency_key": effect_key}
            ).ensure_hashes()
            receipt = self.action_gateway.execute_envelope_sync(
                envelope, context=self.actor_context
            )
            return (
                WorkerResult(
                    worker_id="wrk_runtime_probe",
                    task_id=task.id,
                    task_family=task.task_family,
                    ok=True,
                    summary="runtime_probe_complete",
                    action_receipt_ids=[receipt.receipt_id],
                ),
                shared_worktree,
            )

    monkeypatch.setattr("swarm.mission.runtime.RepoWorker", ProbeWorker)
    runtime = MissionRuntime(
        repo=tmp_path,
        store_dir=tmp_path / "missions",
        use_evidence_router=False,
        max_repair_rounds=0,
    )
    monkeypatch.setattr(runtime, "_mission_broker", lambda **_kwargs: object())

    record = await runtime.run("run the R28d runtime bridge probe")

    assert record.status == "completed"
    assert observed_without_loop == ["inspect", "implement", "verify", "review"]
    assert len(record.result["action_receipt_ids"]) == 4
    for task_family in observed_without_loop:
        assert (tmp_path / f"runtime-bridge-{task_family}.txt").read_text(
            encoding="utf-8"
        ) == f"{task_family}\n"


@pytest.mark.asyncio
async def test_runtime_removes_worktree_when_gateway_binding_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A created worktree cannot leak when gateway binding fails."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_fixture_repo(repo)
    bound: list[WorktreeHandle] = []

    def fail_bind(self: RepoWorker, handle: WorktreeHandle) -> None:
        del self
        bound.append(handle)
        raise RuntimeError("injected_gateway_binding_failure")

    monkeypatch.setattr(RepoWorker, "_bind_worktree_effects", fail_bind)
    runtime = MissionRuntime(
        repo=repo,
        store_dir=tmp_path / "missions",
        use_evidence_router=False,
        max_repair_rounds=0,
    )
    monkeypatch.setattr(runtime, "_mission_broker", lambda **_kwargs: object())

    with pytest.raises(RuntimeError, match="injected_gateway_binding_failure"):
        await runtime.run("exercise worktree cleanup after an effect error")

    assert len(bound) == 1
    assert not bound[0].path.exists()
    branches = subprocess.run(
        ["git", "branch", "--list", bound[0].branch],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    assert not branches.stdout.strip()


def _fixture_runtime(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MissionRuntime:
    """Construct a real local runtime without model or network use."""

    runtime = MissionRuntime(
        repo=repo,
        store_dir=tmp_path / "missions",
        use_evidence_router=False,
        max_repair_rounds=0,
        parser_dogfood_fixture=True,
    )
    monkeypatch.setattr(runtime, "_mission_broker", lambda **_kwargs: object())
    monkeypatch.setattr(
        RepoWorker,
        "_chat",
        lambda self, *, messages, model, max_tokens=800: InferenceResult(
            ok=True,
            text=(
                "def inclusive_range_count(start: int, end: int) -> int:\n"
                "    return end - start + 1\n"
            ),
            model=model,
            route_id="rt_test",
        ),
    )
    return runtime


def _assert_worktree_removed(repo: Path, handle: WorktreeHandle) -> None:
    assert not handle.path.exists()
    branches = subprocess.run(
        ["git", "branch", "--list", handle.branch],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    assert not branches.stdout.strip()


@pytest.mark.asyncio
async def test_accepted_mission_retains_worktree_for_explicit_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A normal accepted mission keeps its isolated artifact until reviewed apply."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_fixture_repo(repo)
    target_rel = Path("sandbox/selfdev_issue/parser_helper.py")
    parent_before = (repo / target_rel).read_text(encoding="utf-8")

    class AcceptedWorktreeWorker:
        def __init__(self, worker_repo: Path, **_kwargs: Any) -> None:
            self.repo = worker_repo
            self.active_worktree: WorktreeHandle | None = None
            self.active_action_receipt_ids: list[str] = []

        def run_task(
            self,
            task: Any,
            *,
            mission_id: str,
            prior: dict[str, WorkerResult],
            shared_worktree: WorktreeHandle | None,
        ) -> tuple[WorkerResult, WorktreeHandle | None]:
            del prior
            handle = shared_worktree
            artifacts: dict[str, Any] = {}
            if task.task_family == "implement":
                handle = create_worktree(
                    self.repo,
                    mission_id=mission_id,
                    task_id=task.id,
                    worker_id="wrk_pending_apply",
                )
                self.active_worktree = handle
                (handle.path / target_rel).write_text(
                    "def inclusive_range_count(start: int, end: int) -> int:\n"
                    "    return end - start + 1\n",
                    encoding="utf-8",
                )
                artifacts["changed_files"] = [str(target_rel)]
            return (
                WorkerResult(
                    worker_id="wrk_pending_apply",
                    task_id=task.id,
                    task_family=task.task_family,
                    ok=True,
                    summary=f"{task.task_family}_complete",
                    artifacts=artifacts,
                ),
                handle,
            )

    monkeypatch.setattr("swarm.mission.runtime.RepoWorker", AcceptedWorktreeWorker)
    runtime = MissionRuntime(
        repo=repo,
        store_dir=tmp_path / "missions",
        use_evidence_router=False,
        max_repair_rounds=0,
    )
    monkeypatch.setattr(runtime, "_mission_broker", lambda **_kwargs: object())

    record = await runtime.run("exercise explicit apply retention")

    assert record.status == "completed"
    pending_apply = record.artifacts["pending_apply"]
    assert pending_apply["status"] == "pending_explicit_apply"
    serialized = pending_apply["worktree"]
    handle = WorktreeHandle(
        path=Path(serialized["path"]),
        branch=serialized["branch"],
        worker_id=serialized["worker_id"],
        mission_id=serialized["mission_id"],
        task_id=serialized["task_id"],
    )
    try:
        assert handle.path.exists()
        assert (repo / target_rel).read_text(encoding="utf-8") == parent_before
        with pytest.raises(PermissionError, match="explicit_apply_requires_approved_true"):
            runtime.apply_worktree_changes(handle, [str(target_rel)], approved=False)
        assert runtime.apply_worktree_changes(handle, [str(target_rel)], approved=True) == [
            str(target_rel)
        ]
        assert "end - start + 1" in (repo / target_rel).read_text(encoding="utf-8")
    finally:
        remove_worktree(repo, handle, force=True)
    _assert_worktree_removed(repo, handle)


@pytest.mark.asyncio
async def test_runtime_cancellation_drains_before_unpublished_worktree_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cancellation cannot leak a worktree created before RepoWorker publishes it."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_fixture_repo(repo)
    runtime = _fixture_runtime(repo, tmp_path, monkeypatch)
    created: list[WorktreeHandle] = []
    created_event = threading.Event()
    release = threading.Event()
    original_create = worker_module.create_worktree

    def pause_after_create(*args: Any, **kwargs: Any) -> WorktreeHandle:
        handle = original_create(*args, **kwargs)
        created.append(handle)
        created_event.set()
        assert release.wait(timeout=5)
        return handle

    monkeypatch.setattr(worker_module, "create_worktree", pause_after_create)
    run = asyncio.create_task(runtime.run("fix the parser fixture"))
    assert await asyncio.to_thread(created_event.wait, 5)
    assert created and created[0].path.exists()

    run.cancel()
    await asyncio.sleep(0)
    assert not run.done()
    assert created[0].path.exists()

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await run

    _assert_worktree_removed(repo, created[0])
    persisted = runtime.store.load(runtime.store.list_missions()[0]["mission_id"])
    assert persisted.status == "cancelled"
    assert persisted.result["cleanup"]["completed"] is True
    assert any(event["event"] == "mission_worker_quiesced" for event in persisted.timeline)


@pytest.mark.asyncio
async def test_runtime_cancellation_after_bind_blocks_late_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cancelled bound worker cannot recreate its worktree with a late effect."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_fixture_repo(repo)
    runtime = _fixture_runtime(repo, tmp_path, monkeypatch)
    bound: list[WorktreeHandle] = []
    bound_event = threading.Event()
    release = threading.Event()
    executed_operations: list[str] = []
    original_bind = RepoWorker._bind_worktree_effects
    original_execute = LocalSandboxAdapter.execute

    def pause_after_bind(self: RepoWorker, handle: WorktreeHandle) -> None:
        original_bind(self, handle)
        bound.append(handle)
        bound_event.set()
        assert release.wait(timeout=5)

    def capture_execute(self: LocalSandboxAdapter, envelope: Any) -> dict[str, Any]:
        executed_operations.append(envelope.operation)
        return original_execute(self, envelope)

    monkeypatch.setattr(RepoWorker, "_bind_worktree_effects", pause_after_bind)
    monkeypatch.setattr(LocalSandboxAdapter, "execute", capture_execute)
    run = asyncio.create_task(runtime.run("fix the parser fixture"))
    assert await asyncio.to_thread(bound_event.wait, 5)
    assert bound and bound[0].path.exists()

    run.cancel()
    await asyncio.sleep(0)
    assert not run.done()
    assert bound[0].path.exists()

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await run

    _assert_worktree_removed(repo, bound[0])
    assert executed_operations == []
    persisted = runtime.store.load(runtime.store.list_missions()[0]["mission_id"])
    assert persisted.status == "cancelled"
    assert persisted.result["action_receipt_ids"] == []


@pytest.mark.asyncio
async def test_runtime_cancellation_records_an_already_admitted_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A synchronous effect already inside its adapter is drained and accounted for."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_fixture_repo(repo)
    runtime = _fixture_runtime(repo, tmp_path, monkeypatch)
    bound: list[WorktreeHandle] = []
    effect_started = threading.Event()
    release = threading.Event()
    original_bind = RepoWorker._bind_worktree_effects
    original_execute = LocalSandboxAdapter.execute

    def record_bind(self: RepoWorker, handle: WorktreeHandle) -> None:
        original_bind(self, handle)
        bound.append(handle)

    def pause_execute(self: LocalSandboxAdapter, envelope: Any) -> dict[str, Any]:
        if envelope.operation == "fs.write_text":
            effect_started.set()
            assert release.wait(timeout=5)
        return original_execute(self, envelope)

    monkeypatch.setattr(RepoWorker, "_bind_worktree_effects", record_bind)
    monkeypatch.setattr(LocalSandboxAdapter, "execute", pause_execute)
    run = asyncio.create_task(runtime.run("fix the parser fixture"))
    assert await asyncio.to_thread(effect_started.wait, 5)
    assert bound and bound[0].path.exists()

    run.cancel()
    await asyncio.sleep(0)
    assert not run.done()
    assert bound[0].path.exists()

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await run

    _assert_worktree_removed(repo, bound[0])
    persisted = runtime.store.load(runtime.store.list_missions()[0]["mission_id"])
    assert persisted.status == "cancelled"
    assert len(persisted.result["action_receipt_ids"]) == 1
    assert persisted.result["cost_accounting"] == "partial_or_unknown"


@pytest.mark.asyncio
async def test_runtime_invalidates_fence_before_signalling_worker_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gateway fence closes before a worker can observe cancellation and race admission."""

    repo = tmp_path / "repo"
    repo.mkdir()
    started = threading.Event()
    release = threading.Event()
    observed_stop_state: list[bool] = []
    captured_stop_event: list[threading.Event] = []
    original_cancel = RevocableFenceProvider.cancel

    class BlockingWorker:
        def __init__(
            self, _repo: Path, *, cancellation_event: threading.Event, **_kwargs: Any
        ) -> None:
            self.cancellation_event = cancellation_event
            self.active_worktree = None
            self.active_action_receipt_ids: list[str] = []
            captured_stop_event.append(cancellation_event)

        def request_cancellation(self) -> None:
            self.cancellation_event.set()

        def run_task(
            self,
            task: Any,
            *,
            mission_id: str,
            prior: dict[str, WorkerResult],
            shared_worktree: Any,
        ) -> tuple[WorkerResult, Any]:
            del mission_id, prior
            started.set()
            assert release.wait(timeout=5)
            return (
                WorkerResult(
                    worker_id="wrk_cancel_order",
                    task_id=task.id,
                    task_family=task.task_family,
                    ok=False,
                    summary="cancelled_probe",
                ),
                shared_worktree,
            )

    def observe_cancel(self: RevocableFenceProvider) -> Any:
        observed_stop_state.append(captured_stop_event[0].is_set())
        return original_cancel(self)

    monkeypatch.setattr("swarm.mission.runtime.RepoWorker", BlockingWorker)
    monkeypatch.setattr(RevocableFenceProvider, "cancel", observe_cancel)
    runtime = MissionRuntime(
        repo=repo,
        store_dir=tmp_path / "missions",
        use_evidence_router=False,
        max_repair_rounds=0,
    )
    monkeypatch.setattr(runtime, "_mission_broker", lambda **_kwargs: object())
    run = asyncio.create_task(runtime.run("exercise cancellation ordering"))
    assert await asyncio.to_thread(started.wait, 5)

    run.cancel()
    await asyncio.sleep(0)
    assert observed_stop_state == [False]
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await run


def test_worker_uses_frozen_pre_cancel_fence_for_effect_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fence bump after worker precheck rejects the stale effect before adapter execution."""

    fences = RevocableFenceProvider()
    gateway = local_worktree_gateway(tmp_path, fences=fences)
    worker = RepoWorker(
        tmp_path,
        broker=None,
        project_id="proj_runtime_cancel",
        action_gateway=gateway,
        actor_context=ActorContext(actor="test", project_id="proj_runtime_cancel"),
        require_broker=False,
    )
    worker._begin_task_effects(mission_id="msn_runtime_cancel", task_id="tsk_runtime_cancel")
    original_execute = gateway.execute_envelope_sync

    def cancel_before_admission(envelope: Any, *, context: ActorContext) -> Any:
        fences.cancel()
        return original_execute(envelope, context=context)

    monkeypatch.setattr(gateway, "execute_envelope_sync", cancel_before_admission)
    with pytest.raises(CancellationFenceError, match="cancellation_generation_mismatch"):
        worker._action_effect("fs.write_text", {"path": "late.txt", "text": "late"})
    assert not (tmp_path / "late.txt").exists()
