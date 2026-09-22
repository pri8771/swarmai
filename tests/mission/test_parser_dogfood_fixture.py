"""LEAD-009 #6: parser dogfood is fixture-only; default mission path is generic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from swarm.contracts.fixtures import sample_task
from swarm.mission.action_boundary import local_worktree_gateway
from swarm.mission.inference import InferenceResult
from swarm.mission.worker import RepoWorker
from swarm.tools.fences import ActorContext


def _worker(repo: Path, worktree_root: Path, *, fixture: bool = False) -> RepoWorker:
    return RepoWorker(
        repo=repo,
        worktree_root=worktree_root,
        project_id="proj_test",
        action_gateway=local_worktree_gateway(repo),
        action_gateway_factory=local_worktree_gateway,
        actor_context=ActorContext(actor="test", project_id="proj_test"),
        parser_dogfood_fixture=fixture,
    )


def test_default_worker_does_not_hardwire_parser_dogfood(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    worker = _worker(repo, tmp_path / "wt")
    assert worker.parser_dogfood_fixture is False
    task = sample_task().model_copy(
        update={
            "task_family": "implement",
            "id": "tsk_generic",
            "inputs": {"goal": "refactor unrelated module"},
        }
    )
    result, _handle = worker._implement(
        task, mission_id="mission_generic", shared=None, prior={}
    )
    assert result.ok is False
    assert result.summary == "implement_requires_target_or_fixture_parser_dogfood"
    assert result.artifacts.get("parser_dogfood_fixture") is False


def test_fixture_flag_enables_parser_dogfood_path(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    worker = _worker(repo, tmp_path / "wt", fixture=True)
    task = sample_task().model_copy(
        update={"task_family": "implement", "id": "tsk_fixture"}
    )
    bogus = InferenceResult(
        ok=True,
        text="definitely not a python fix",
        model="test",
        route_id="rt_test",
    )
    with patch("swarm.mission.worker.local_chat", return_value=bogus):
        result, _handle = worker._implement(
            task, mission_id="mission_fixture", shared=None, prior={}
        )
    assert result.summary == "implement_failed_no_known_answer_fallback"
    assert result.artifacts.get("parser_dogfood_fixture") is True
    assert result.artifacts.get("target_file") == "sandbox/selfdev_issue/parser_helper.py"


def test_inspect_without_fixture_does_not_auto_select_parser(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    worker = _worker(repo, tmp_path / "wt")
    task = sample_task().model_copy(
        update={
            "task_family": "inspect",
            "id": "tsk_inspect",
            "inputs": {"goal": "improve documentation"},
        }
    )
    result = worker._inspect(task, mission_id="mission_inspect")
    findings = result.artifacts.get("findings") or {}
    assert findings.get("parser_dogfood_fixture") is False
    assert "sandbox/selfdev_issue/parser_helper.py" not in findings.get(
        "candidate_files", []
    )
