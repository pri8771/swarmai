"""V14-REAL-001-R: generic materialization accepts raw/fenced Python; empty diff fail-closed."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from swarm.contracts.fixtures import sample_task
from swarm.mission.inference import InferenceResult
from swarm.mission.worker import (
    GOOD_FIX,
    RepoWorker,
    _extract_python_file,
)


def _init_temp_repo(root: Path) -> Path:
    """Unrelated held-out fixture repo — not token_hash / inclusive_range_count."""
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "v14-repair@example.test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "v14-repair"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    target = root / "widgets" / "counter.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        '"""Held-out widget counter used only by materialization regressions."""\n'
        "\n"
        "def bump(value: int) -> int:\n"
        "    return value\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "seed unrelated counter"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return root


FIXED_COUNTER = (
    '"""Held-out widget counter used only by materialization regressions."""\n'
    "\n"
    "def bump(value: int) -> int:\n"
    "    return value + 1\n"
)


def test_extract_accepts_raw_and_fenced_python() -> None:
    raw = _extract_python_file(FIXED_COUNTER)
    assert raw == FIXED_COUNTER
    fenced = _extract_python_file(f"```python\n{FIXED_COUNTER}```\n")
    assert fenced == FIXED_COUNTER
    truncated = _extract_python_file(f"```python\n{FIXED_COUNTER}")
    assert truncated == FIXED_COUNTER
    assert _extract_python_file("definitely not a python fix") is None
    assert _extract_python_file("") is None


def test_generic_raw_source_materializes_nonempty_diff(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path / "heldout_repo")
    primary_before = (repo / "widgets" / "counter.py").read_text(encoding="utf-8")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    task = sample_task().model_copy(
        update={
            "task_family": "implement",
            "id": "tsk_mat_raw",
            "inputs": {
                "goal": "Make bump increment by one",
                "target_file": "widgets/counter.py",
            },
        }
    )
    inference = InferenceResult(
        ok=True,
        text=FIXED_COUNTER,
        model="test-local",
        route_id="rt_test",
    )
    with patch("swarm.mission.worker.local_chat", return_value=inference):
        result, handle = worker._implement(task, mission_id="mission_mat_raw", shared=None)
    assert result.ok is True
    assert result.summary == "implement_applied"
    assert result.artifacts.get("diff", "").strip()
    assert "value + 1" in result.artifacts["diff"]
    assert GOOD_FIX not in (result.artifacts.get("diff") or "")
    assert (repo / "widgets" / "counter.py").read_text(encoding="utf-8") == primary_before
    assert handle.path.exists()


def test_generic_fenced_source_materializes(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path / "heldout_repo")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    task = sample_task().model_copy(
        update={
            "task_family": "implement",
            "id": "tsk_mat_fence",
            "inputs": {
                "goal": "Make bump increment by one",
                "target_file": "widgets/counter.py",
            },
        }
    )
    inference = InferenceResult(
        ok=True,
        text=f"Here is the file:\n```python\n{FIXED_COUNTER}```\nThanks.",
        model="test-local",
        route_id="rt_test",
    )
    with patch("swarm.mission.worker.local_chat", return_value=inference):
        result, _handle = worker._implement(
            task, mission_id="mission_mat_fence", shared=None
        )
    assert result.ok is True
    assert result.summary == "implement_applied"
    assert "value + 1" in result.artifacts.get("diff", "")


def test_malformed_output_rejected_without_write(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path / "heldout_repo")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    task = sample_task().model_copy(
        update={
            "task_family": "implement",
            "id": "tsk_mat_bad",
            "inputs": {
                "goal": "Make bump increment by one",
                "target_file": "widgets/counter.py",
            },
        }
    )
    inference = InferenceResult(
        ok=True,
        text="I think you should increment the value somehow.",
        model="test-local",
        route_id="rt_test",
    )
    with patch("swarm.mission.worker.local_chat", return_value=inference):
        result, handle = worker._implement(task, mission_id="mission_mat_bad", shared=None)
    assert result.ok is False
    assert result.summary == "implement_failed_no_known_answer_fallback"
    assert result.artifacts.get("known_answer_forbidden") is True
    assert GOOD_FIX not in str(result.artifacts)
    wt_target = handle.path / "widgets" / "counter.py"
    assert "value + 1" not in wt_target.read_text(encoding="utf-8")


def test_truncated_rewrite_rejected_without_write(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path / "heldout_repo")
    # Expand fixture with several top-level defs so truncation is detectable.
    target = repo / "widgets" / "counter.py"
    full = (
        '"""Held-out widget counter used only by materialization regressions."""\n'
        "\n"
        "def bump(value: int) -> int:\n"
        "    return value\n"
        "\n"
        "def reset() -> int:\n"
        "    return 0\n"
        "\n"
        "def twice(value: int) -> int:\n"
        "    return value * 2\n"
        "\n"
        "def label() -> str:\n"
        "    return 'counter'\n"
    )
    target.write_text(full, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "expand counter"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    task = sample_task().model_copy(
        update={
            "task_family": "implement",
            "id": "tsk_mat_trunc",
            "inputs": {
                "goal": "Make bump increment by one",
                "target_file": "widgets/counter.py",
            },
        }
    )
    truncated = (
        '"""Held-out widget counter used only by materialization regressions."""\n'
        "\n"
        "def bump(value: int) -> int:\n"
        "    return value + 1\n"
    )
    inference = InferenceResult(
        ok=True,
        text=truncated,
        model="test-local",
        route_id="rt_test",
    )
    with patch("swarm.mission.worker.local_chat", return_value=inference):
        result, handle = worker._implement(
            task, mission_id="mission_mat_trunc", shared=None
        )
    assert result.ok is False
    assert result.summary == "implement_truncated_rewrite"
    assert (handle.path / "widgets" / "counter.py").read_text(encoding="utf-8") == full


def test_invalid_syntax_rejected_without_write(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path / "heldout_repo")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    task = sample_task().model_copy(
        update={
            "task_family": "implement",
            "id": "tsk_mat_syntax",
            "inputs": {
                "goal": "Make bump increment by one",
                "target_file": "widgets/counter.py",
            },
        }
    )
    bad = (
        '"""broken"""\n'
        "\n"
        "def bump(value: int) -> int:\n"
        '    """unterminated\n'
    )
    inference = InferenceResult(
        ok=True,
        text=f"```python\n{bad}",
        model="test-local",
        route_id="rt_test",
    )
    with patch("swarm.mission.worker.local_chat", return_value=inference):
        result, handle = worker._implement(
            task, mission_id="mission_mat_syntax", shared=None
        )
    assert result.ok is False
    assert result.summary == "implement_invalid_python_syntax"
    assert not (result.artifacts.get("diff") or "").strip()
    assert (handle.path / "widgets" / "counter.py").read_text(encoding="utf-8") == (
        '"""Held-out widget counter used only by materialization regressions."""\n'
        "\n"
        "def bump(value: int) -> int:\n"
        "    return value\n"
    )


def test_noop_candidate_not_summarized_as_implement_applied(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path / "heldout_repo")
    original = (repo / "widgets" / "counter.py").read_text(encoding="utf-8")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    task = sample_task().model_copy(
        update={
            "task_family": "implement",
            "id": "tsk_mat_noop",
            "inputs": {
                "goal": "Make bump increment by one",
                "target_file": "widgets/counter.py",
            },
        }
    )
    inference = InferenceResult(
        ok=True,
        text=original,
        model="test-local",
        route_id="rt_test",
    )
    with patch("swarm.mission.worker.local_chat", return_value=inference):
        result, _handle = worker._implement(
            task, mission_id="mission_mat_noop", shared=None
        )
    assert result.ok is False
    assert result.summary == "implement_no_material_diff"
    assert result.summary != "implement_applied"
    assert not (result.artifacts.get("diff") or "").strip()
