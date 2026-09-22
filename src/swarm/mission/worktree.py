"""Real git worktree isolation for mission workers."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from swarm.contracts.common import new_id


class WorktreeError(RuntimeError):
    pass


@dataclass
class WorktreeHandle:
    path: Path
    branch: str
    worker_id: str
    mission_id: str
    task_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "path": str(self.path),
            "branch": self.branch,
            "worker_id": self.worker_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
        }


def _run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=check,
    )


def create_worktree(
    repo: Path,
    *,
    mission_id: str,
    task_id: str,
    worker_id: str,
    base_dir: Path | None = None,
) -> WorktreeHandle:
    """Create an isolated git worktree for one worker/task."""
    repo = repo.resolve()
    if not (repo / ".git").exists() and not (repo / ".git").is_file():
        # Allow worktree from a linked gitdir (worktree itself).
        probe = _run_git(repo, "rev-parse", "--is-inside-work-tree", check=False)
        if probe.returncode != 0 or probe.stdout.strip() != "true":
            raise WorktreeError(f"not a git repository: {repo}")

    root = base_dir or (repo / "var" / "mission-worktrees" / mission_id)
    root.mkdir(parents=True, exist_ok=True)
    safe_task = task_id.replace("/", "_")[:48]
    branch = f"mission/{mission_id[:12]}/{safe_task}/{new_id('w')[:8]}"
    path = root / f"{safe_task}-{worker_id}"
    if path.exists():
        shutil.rmtree(path)

    # Detached worktree from HEAD keeps the parent index clean.
    add = _run_git(
        repo,
        "worktree",
        "add",
        "-b",
        branch,
        str(path),
        "HEAD",
        check=False,
    )
    if add.returncode != 0:
        raise WorktreeError(add.stderr.strip() or add.stdout.strip() or "worktree add failed")
    return WorktreeHandle(
        path=path,
        branch=branch,
        worker_id=worker_id,
        mission_id=mission_id,
        task_id=task_id,
    )


def remove_worktree(repo: Path, handle: WorktreeHandle, *, force: bool = True) -> None:
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(handle.path))
    result = _run_git(repo, *args, check=False)
    # Best-effort branch cleanup.
    _run_git(repo, "branch", "-D", handle.branch, check=False)
    if result.returncode != 0 and handle.path.exists():
        shutil.rmtree(handle.path, ignore_errors=True)
        _run_git(repo, "worktree", "prune", check=False)


def worktree_diff(handle: WorktreeHandle) -> str:
    result = _run_git(handle.path, "diff", "--", ".", check=False)
    return result.stdout


def intent_to_add(handle: WorktreeHandle, paths: list[str]) -> None:
    """Register new files so `git diff` (and therefore the diff-based gates) can see them."""
    if paths:
        _run_git(handle.path, "add", "-N", "--", *paths, check=False)
