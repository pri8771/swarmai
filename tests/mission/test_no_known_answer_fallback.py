"""FIX-005: operational mission path must not substitute GOOD_FIX."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from swarm.contracts.fixtures import sample_task
from swarm.mission.inference import InferenceResult
from swarm.mission.worker import GOOD_FIX, RepoWorker


def test_implement_does_not_apply_good_fix_on_model_failure(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    worker = RepoWorker(
        repo=repo, worktree_root=tmp_path / "wt", parser_dogfood_fixture=True
    )
    task = sample_task().model_copy(
        update={"task_family": "implement", "id": "tsk_no_goodfix"}
    )
    bogus = InferenceResult(
        ok=True,
        text="definitely not a python fix",
        model="test",
        route_id="rt_test",
    )
    with patch("swarm.mission.worker.local_chat", return_value=bogus):
        result, _handle = worker._implement(task, mission_id="mission_x", shared=None)
    assert result.ok is False
    assert result.summary == "implement_failed_no_known_answer_fallback"
    assert result.artifacts.get("known_answer_forbidden") is True
    # GOOD_FIX must not appear as applied content.
    assert GOOD_FIX not in str(result.artifacts.get("model_output_excerpt") or "")
