"""R28d: the async mission runtime must dispatch sync gateway work off-loop."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

import pytest

from swarm.mission.runtime import MissionRuntime
from swarm.mission.worker import RepoWorker, WorkerResult
from swarm.mission.worktree import WorktreeHandle


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
