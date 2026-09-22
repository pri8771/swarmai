"""R02a / ART-V14-REAL-E2E — red->green defect-proof gate (temporary git repos, no model)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from swarm.mission.acceptance import (
    is_defect_repair_goal,
    prove_defect,
    regression_tests_in_diff,
    review_attempt,
)

PRODUCTION_BUGGY = "def add(a, b):\n    return a - b\n"
PRODUCTION_FIXED = "def add(a, b):\n    return a + b\n"
REGRESSION = "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
ALWAYS_GREEN = "def test_tautology():\n    assert 1 + 1 == 2\n"
IMPORTS_NEW_SYMBOL = (
    "from calc import subtract\n\n\ndef test_subtract():\n    assert subtract(5, 3) == 2\n"
)
FIXED_WITH_SUBTRACT = PRODUCTION_FIXED + "\n\ndef subtract(a, b):\n    return a - b\n"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=True
    ).stdout.strip()


def _run(cwd: Path, argv: list[str]) -> dict[str, Any]:
    """The injectable runner: current interpreter's pytest, cwd on sys.path."""
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


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A committed repository with a buggy production module and no tests."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.test")
    _git(root, "config", "user.name", "t")
    (root / "calc.py").write_text(PRODUCTION_BUGGY, encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "buggy baseline")
    return root


def _patched_worktree(
    repo: Path, *, production: str | None, test_name: str | None, test_body: str | None
) -> tuple[Path, str]:
    """Create the worker's patched worktree from HEAD and apply the candidate patch."""
    wt = repo.parent / "patched"
    _git(repo, "worktree", "add", "-q", "--detach", str(wt), "HEAD")
    if production is not None:
        (wt / "calc.py").write_text(production, encoding="utf-8")
    if test_name and test_body is not None:
        (wt / "tests" / test_name).write_text(test_body, encoding="utf-8")
        _git(wt, "add", "-N", f"tests/{test_name}")  # intent-to-add so `git diff` shows it
    diff = subprocess.run(
        ["git", "diff", "--", "."], cwd=str(wt), capture_output=True, text=True, check=False
    ).stdout
    return wt, diff


def _prove(repo: Path, wt: Path, diff: str):
    return prove_defect(
        repo=repo,
        candidate_sha=_git(repo, "rev-parse", "HEAD"),
        worktree=wt,
        diff_text=diff,
        run=_run,
    )


def _clean_worktrees(repo: Path) -> list[str]:
    listing = _git(repo, "worktree", "list", "--porcelain")
    return [line for line in listing.splitlines() if "defect-proof" in line]


def test_patch_without_regression_test_is_unproven(repo: Path) -> None:
    wt, diff = _patched_worktree(repo, production=PRODUCTION_FIXED, test_name=None, test_body=None)
    decision = _prove(repo, wt, diff)
    assert decision.proven is False
    assert decision.reason == "no_regression_test_in_patch"
    assert regression_tests_in_diff(diff) == []
    assert _clean_worktrees(repo) == []


def test_regression_that_passes_pre_patch_is_unproven(repo: Path) -> None:
    """The v14-real-007 shape: a refactor plus a test that was already green."""
    wt, diff = _patched_worktree(
        repo, production=PRODUCTION_FIXED, test_name="test_tautology.py", test_body=ALWAYS_GREEN
    )
    decision = _prove(repo, wt, diff)
    assert decision.proven is False
    assert decision.reason == "regression_passes_without_patch"
    assert decision.pre_patch["exit_code"] == 0
    assert decision.regression_tests == ["tests/test_tautology.py"]
    assert _clean_worktrees(repo) == []


def test_pre_patch_collection_error_is_not_counted_as_red(repo: Path) -> None:
    """A test importing a symbol that exists only post-patch cannot be collected pre-patch."""
    wt, diff = _patched_worktree(
        repo,
        production=FIXED_WITH_SUBTRACT,
        test_name="test_subtract.py",
        test_body=IMPORTS_NEW_SYMBOL,
    )
    decision = _prove(repo, wt, diff)
    assert decision.proven is False
    assert decision.reason == "pre_patch_not_a_clean_failure"
    assert decision.pre_patch["exit_code"] == 2
    assert decision.post_patch == {}  # never reached
    assert _clean_worktrees(repo) == []


def test_regression_failing_post_patch_is_unproven(repo: Path) -> None:
    """Regression is red pre-patch but the patch does not actually fix it."""
    still_buggy = "def add(a, b):\n    return a * b\n"
    wt, diff = _patched_worktree(
        repo, production=still_buggy, test_name="test_add.py", test_body=REGRESSION
    )
    decision = _prove(repo, wt, diff)
    assert decision.proven is False
    assert decision.reason == "regression_fails_with_patch"
    assert decision.pre_patch["exit_code"] == 1
    assert decision.post_patch["exit_code"] == 1
    assert _clean_worktrees(repo) == []


def test_true_red_green_is_proven(repo: Path) -> None:
    wt, diff = _patched_worktree(
        repo, production=PRODUCTION_FIXED, test_name="test_add.py", test_body=REGRESSION
    )
    decision = _prove(repo, wt, diff)
    assert decision.proven is True
    assert decision.reason == "red_green_demonstrated"
    assert decision.pre_patch["exit_code"] == 1
    assert decision.post_patch["exit_code"] == 0
    assert decision.pre_patch["stdout_sha256"] != decision.post_patch["stdout_sha256"]
    # The clean worktree never saw the production fix and is gone afterwards.
    assert (repo / "calc.py").read_text(encoding="utf-8") == PRODUCTION_BUGGY
    assert _clean_worktrees(repo) == []
    assert decision.to_dict()["regression_tests"] == ["tests/test_add.py"]


def test_second_worktree_removed_on_exception(repo: Path) -> None:
    wt, diff = _patched_worktree(
        repo, production=PRODUCTION_FIXED, test_name="test_add.py", test_body=REGRESSION
    )

    def exploding_run(cwd: Path, argv: list[str]) -> dict[str, Any]:
        assert "defect-proof" in str(cwd)  # the clean worktree existed when run was called
        raise RuntimeError("runner exploded")

    with pytest.raises(RuntimeError, match="runner exploded"):
        prove_defect(
            repo=repo,
            candidate_sha=_git(repo, "rev-parse", "HEAD"),
            worktree=wt,
            diff_text=diff,
            run=exploding_run,
        )
    assert _clean_worktrees(repo) == []
    assert not (repo / "var" / "defect-proof").exists() or not any(
        (repo / "var" / "defect-proof").iterdir()
    )


def test_review_attempt_never_passes_unproven_defect_repair() -> None:
    produced = {
        "checks": {
            "verification_passed": True,
            "implementation_present": True,
            "diff_clean": True,
            "review_grounded": True,
        }
    }
    required = {k: True for k in produced["checks"]}
    green_only = review_attempt(produced=produced, required_checks=required, defect_repair=True)
    assert green_only.accepted is False
    assert "no_defect_demonstrated" in green_only.reasons
    assert green_only.checks["defect_proven"] is False
    unproven = review_attempt(
        produced=produced,
        required_checks=required,
        defect_repair=True,
        defect_proof={"proven": False, "reason": "regression_passes_without_patch"},
    )
    assert unproven.accepted is False
    assert "defect_proof:regression_passes_without_patch" in unproven.reasons
    proven = review_attempt(
        produced=produced,
        required_checks=required,
        defect_repair=True,
        defect_proof={"proven": True, "reason": "red_green_demonstrated"},
    )
    assert proven.accepted is True
    assert proven.checks["defect_proven"] is True
    # Non-defect missions are unaffected by the gate.
    plain = review_attempt(produced=produced, required_checks=required)
    assert plain.accepted is True and "defect_proven" not in plain.checks


def test_defect_repair_goal_detection() -> None:
    assert is_defect_repair_goal(
        "Audit src/swarm/runtime for one real correctness defect and add a regression test"
    )
    assert is_defect_repair_goal("Fix the off-by-one bug in the paginator")
    assert not is_defect_repair_goal("Add a CLI flag that prints the version")
    assert is_defect_repair_goal("anything", {"defect_repair": True})
