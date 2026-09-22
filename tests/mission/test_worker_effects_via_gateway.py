"""R28d-2: worker commands and writes cross the versioned action boundary."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.mission._worker_support import make_worker

from swarm.mission.action_boundary import local_worktree_gateway
from swarm.mission.worker import RepoWorker, WorkerResult
from swarm.tools.adapters.base import AdapterDeniedError
from swarm.tools.fences import ActorContext


def _active_worker(tmp_path: Path) -> RepoWorker:
    worker = make_worker(tmp_path, worktree_root=tmp_path)
    worker._begin_task_effects(mission_id="msn_effects", task_id="tsk_effects")
    return worker


@pytest.mark.parametrize("path", [Path("../outside.txt"), Path("/tmp/outside.txt")])
def test_write_outside_worktree_denied_and_file_absent(tmp_path: Path, path: Path) -> None:
    worker = _active_worker(tmp_path)
    with pytest.raises(AdapterDeniedError, match="path_outside_root"):
        worker._write_effect(path, "blocked")
    assert not (tmp_path / "outside.txt").exists()


def test_symlink_escape_write_denied_and_file_absent(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "escape").symlink_to(outside, target_is_directory=True)
    worker = _active_worker(tmp_path)
    with pytest.raises(AdapterDeniedError, match="path_outside_root"):
        worker._write_effect(Path("escape/blocked.txt"), "blocked")
    assert not (outside / "blocked.txt").exists()


def test_command_not_allowlisted_denied_and_not_run(tmp_path: Path) -> None:
    worker = _active_worker(tmp_path)
    with pytest.raises(AdapterDeniedError, match="command_not_allowlisted"):
        worker._run_effect(["git", "push"], timeout=5)


def test_repo_worker_requires_gateway_and_explicit_project_id(tmp_path: Path) -> None:
    context = ActorContext(actor="test", project_id="proj_test")
    with pytest.raises(RuntimeError, match="action_gateway_required"):
        RepoWorker(tmp_path, project_id="proj_test", actor_context=context)
    gateway = local_worktree_gateway(tmp_path)
    with pytest.raises(TypeError):
        RepoWorker(tmp_path, action_gateway=gateway, actor_context=context)  # type: ignore[call-arg]


def test_worker_module_has_no_direct_effects() -> None:
    source = Path(__file__).resolve().parents[2] / "src/swarm/mission/worker.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr == "write_text":
            pytest.fail(f"direct write_text at line {node.lineno}")
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "subprocess":
                pytest.fail(f"direct subprocess call at line {node.lineno}")
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            if any(
                isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "w" in arg.value
                for arg in node.args[1:]
            ):
                pytest.fail(f"direct writable open at line {node.lineno}")


def test_receipts_are_distinct_for_repeated_writes_and_propagate(tmp_path: Path) -> None:
    worker = _active_worker(tmp_path)
    worker._write_effect(Path("same.txt"), "first")
    worker._write_effect(Path("same.txt"), "second")
    result = worker._end_task_effects(
        WorkerResult(
            worker_id=worker.worker_id,
            task_id="tsk_effects",
            task_family="implement",
            ok=True,
            summary="test",
        )
    )
    assert len(result.action_receipt_ids) == 2
    assert len(set(result.action_receipt_ids)) == 2
    assert (tmp_path / "same.txt").read_text(encoding="utf-8") == "second"


def test_nonzero_exit_is_recorded_not_raised(tmp_path: Path) -> None:
    worker = _active_worker(tmp_path)
    command = worker._run_effect(
        ["python", "-m", "pytest", "does-not-exist", "-q"], timeout=30
    )
    assert command["ok"] is False
    assert command["exit_code"] != 0
    assert command["action_receipt_id"] in worker._effect_receipt_ids
