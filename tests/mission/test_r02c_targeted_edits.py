"""R02c / ART-V14-REAL-E2E — targeted edit blocks, echo detection, re-prompt, new tests.

No model, no network: inference is faked per call. Temporary git repositories only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from swarm.contracts.fixtures import sample_task
from swarm.mission.inference import InferenceResult
from swarm.mission.worker import (
    RepoWorker,
    _apply_edit_blocks,
    _is_echo,
    _parse_targeted_change,
    _valid_new_test_path,
)

ORIGINAL = (
    '"""Held-out widget counter used only by targeted-edit regressions."""\n'
    "\n"
    "def bump(value: int) -> int:\n"
    "    return value\n"
)
EDIT_RESPONSE = (
    "### EDIT widgets/counter.py\n"
    "<<<<<<< SEARCH\n"
    "def bump(value: int) -> int:\n"
    "    return value\n"
    "=======\n"
    "def bump(value: int) -> int:\n"
    "    return value + 1\n"
    ">>>>>>> REPLACE\n"
    "\n"
    "### NEW tests/widgets/test_bump_regression.py\n"
    "```python\n"
    "from widgets.counter import bump\n"
    "\n"
    "\n"
    "def test_bump_increments():\n"
    "    assert bump(1) == 2\n"
    "```\n"
)


def _init_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for argv in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.email", "r02c@example.test"],
        ["git", "config", "user.name", "r02c"],
    ):
        subprocess.run(argv, cwd=root, check=True, capture_output=True)
    (root / "widgets").mkdir()
    (root / "widgets" / "__init__.py").write_text("", encoding="utf-8")
    (root / "widgets" / "counter.py").write_text(ORIGINAL, encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "baseline"], cwd=root, check=True, capture_output=True
    )
    return root


def _task(task_id: str):
    return sample_task().model_copy(
        update={
            "task_family": "implement",
            "id": task_id,
            "inputs": {
                "goal": "Fix the bug that bump does not increment; add a regression test",
                "target_file": "widgets/counter.py",
            },
        }
    )


def _inf(text: str) -> InferenceResult:
    return InferenceResult(
        ok=True,
        text=text,
        model="test-local",
        route_id="rt_test",
        prompt_tokens=10,
        completion_tokens=5,
    )


def test_parse_and_apply_edit_blocks() -> None:
    change = _parse_targeted_change(EDIT_RESPONSE)
    assert len(change.edits) == 1 and change.edits[0][0] == "widgets/counter.py"
    assert list(change.new_files) == ["tests/widgets/test_bump_regression.py"]
    patched, unmatched = _apply_edit_blocks(ORIGINAL, change.edits)
    assert unmatched == []
    assert "return value + 1" in patched and patched.count("def bump") == 1
    # A SEARCH that does not occur verbatim is reported, never guessed.
    _, missing = _apply_edit_blocks(ORIGINAL, [("widgets/counter.py", "def nope():\n", "x")])
    assert missing == ["def nope():\n"]


def test_echo_detection_and_new_test_path_rules() -> None:
    assert _is_echo(ORIGINAL, ORIGINAL)
    assert _is_echo(ORIGINAL, f"```python\n{ORIGINAL}```")
    assert _is_echo(ORIGINAL, ORIGINAL + "\n")
    assert not _is_echo(ORIGINAL, ORIGINAL.replace("return value", "return value + 1"))
    assert not _is_echo(ORIGINAL, None)
    assert _valid_new_test_path("tests/widgets/test_x.py")
    for bad in (
        "widgets/test_x.py",
        "tests/../evil.py",
        "tests/x.py",
        "/tmp/test_x.py",
        "tests/test_x.txt",
    ):
        assert not _valid_new_test_path(bad), bad


def test_echo_is_reprompted_then_targeted_edit_and_new_test_land_in_diff(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    prompts: list[str] = []
    responses = iter([_inf(ORIGINAL), _inf(EDIT_RESPONSE)])

    def fake_chat(**kwargs):
        prompts.append(kwargs["messages"][-1]["content"])
        return next(responses)

    with patch("swarm.mission.worker.local_chat", side_effect=fake_chat):
        result, handle = worker._implement(_task("tsk_r02c_echo"), mission_id="m_echo", shared=None)
    assert result.ok is True and result.summary == "implement_applied"
    art = result.artifacts
    assert art["echo_detected"] is True and art["reprompted"] is True
    assert art["inference_calls"] == 2 and art["edit_blocks_applied"] == 1
    assert art["new_test_files"] == ["tests/widgets/test_bump_regression.py"]
    assert set(art["changed_files"]) == {
        "widgets/counter.py",
        "tests/widgets/test_bump_regression.py",
    }
    # The new test is visible in the git diff (intent-to-add), which is what the gate reads.
    assert "tests/widgets/test_bump_regression.py" in art["diff"]
    assert "return value + 1" in art["diff"]
    assert "repeated the file unchanged" in prompts[1]
    assert "### EDIT" in prompts[0]  # first prompt already asks for edit blocks
    # Token accounting covers both calls.
    assert result.inference["calls"] == 2 and result.inference["prompt_tokens"] == 20
    # Primary checkout untouched.
    assert (repo / "widgets" / "counter.py").read_text(encoding="utf-8") == ORIGINAL
    assert not (repo / "tests" / "widgets").exists()
    assert (handle.path / "tests" / "widgets" / "test_bump_regression.py").is_file()


def test_double_echo_is_no_material_diff_without_writing(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    with patch("swarm.mission.worker.local_chat", return_value=_inf(ORIGINAL)):
        result, handle = worker._implement(
            _task("tsk_r02c_echo2"), mission_id="m_echo2", shared=None
        )
    assert result.ok is False and result.summary == "implement_no_material_diff"
    assert result.artifacts["echo_detected"] is True
    assert result.artifacts["reprompted"] is True
    assert result.artifacts["inference_calls"] == 2
    assert result.artifacts["diff"] == ""
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=handle.path, capture_output=True, text=True
    ).stdout
    assert status.strip() == ""  # nothing written into the worktree


def test_unmatched_edit_block_is_reprompted_and_then_fails_honestly(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    bad = EDIT_RESPONSE.replace("    return value\n=======", "    return valu\n=======")
    with patch("swarm.mission.worker.local_chat", return_value=_inf(bad)):
        result, _ = worker._implement(_task("tsk_r02c_unmatched"), mission_id="m_um", shared=None)
    assert result.ok is False
    assert result.summary == "implement_failed_no_known_answer_fallback"
    assert result.artifacts["diff"] == "" and result.artifacts["changed_files"] == []
    assert result.inference["calls"] == 2


def test_rejected_new_test_path_is_not_written(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    evil = EDIT_RESPONSE.replace(
        "### NEW tests/widgets/test_bump_regression.py", "### NEW tests/../widgets/evil.py"
    )
    with patch("swarm.mission.worker.local_chat", return_value=_inf(evil)):
        result, handle = worker._implement(_task("tsk_r02c_evil"), mission_id="m_evil", shared=None)
    assert result.ok is True  # the edit itself is fine
    assert result.artifacts["rejected_new_files"] == ["tests/../widgets/evil.py"]
    assert result.artifacts["new_test_files"] == []
    assert not (handle.path / "widgets" / "evil.py").exists()
    assert not (repo / "widgets" / "evil.py").exists()


def test_targeted_fix_passes_the_defect_proof_gate_end_to_end(tmp_path: Path) -> None:
    """The regression written by the model fails pre-patch and passes post-patch."""
    import sys

    from swarm.mission.acceptance import prove_defect

    repo = _init_repo(tmp_path / "repo")
    worker = RepoWorker(repo=repo, worktree_root=tmp_path / "wt")
    with patch("swarm.mission.worker.local_chat", return_value=_inf(EDIT_RESPONSE)):
        result, handle = worker._implement(_task("tsk_r02c_gate"), mission_id="m_gate", shared=None)
    assert result.ok is True

    def run(cwd: Path, argv: list[str]) -> dict:
        cmd = [sys.executable, "-m", *argv, "-p", "no:cacheprovider", "--rootdir", str(cwd)]
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            env={"PYTHONPATH": str(cwd), "PATH": "/usr/bin:/bin"},
        )
        return {
            "cmd": cmd,
            "exit_code": proc.returncode,
            "ok": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    decision = prove_defect(
        repo=repo,
        candidate_sha=head,
        worktree=handle.path,
        diff_text=result.artifacts["diff"],
        run=run,
    )
    assert decision.proven is True, decision.to_dict()
    assert decision.reason == "red_green_demonstrated"
