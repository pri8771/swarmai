"""G11: MissionRuntime must not auto-promote worktree changes into primary checkout."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.mission.runtime import MissionRuntime
from swarm.mission.worktree import WorktreeHandle, create_worktree, remove_worktree

ROOT = Path(__file__).resolve().parents[2]


def test_apply_worktree_changes_requires_explicit_approval(tmp_path: Path) -> None:
    runtime = MissionRuntime(repo=tmp_path, store_dir=tmp_path / "missions")
    handle = WorktreeHandle(
        path=tmp_path / "wt",
        mission_id="msn_x",
        task_id="tsk_x",
        worker_id="wrk_x",
        branch="swarm/msn_x",
    )
    (tmp_path / "wt").mkdir()
    (tmp_path / "wt" / "note.txt").write_text("from-worktree\n", encoding="utf-8")
    with pytest.raises(PermissionError, match="explicit_apply_requires_approved_true"):
        runtime.apply_worktree_changes(handle, ["note.txt"], approved=False)
    applied = runtime.apply_worktree_changes(handle, ["note.txt"], approved=True)
    assert applied == ["note.txt"]
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "from-worktree\n"


def test_no_auto_promote_method_on_normal_path() -> None:
    """_promote_changes must be removed from MissionRuntime (G11 safety)."""
    assert not hasattr(MissionRuntime, "_promote_changes")


def test_worktree_isolation_still_holds() -> None:
    handle = create_worktree(
        ROOT,
        mission_id="msn_g11_nopromo",
        task_id="tsk_g11",
        worker_id="wrk_g11",
        base_dir=ROOT / "var" / "mission-worktrees" / "g11-nopromo",
    )
    try:
        marker = handle.path / "README.md"
        original_parent = (ROOT / "README.md").read_text(encoding="utf-8")
        marker.write_text(original_parent + "\n# g11-no-auto-promote\n", encoding="utf-8")
        # Parent must remain unchanged until explicit apply.
        assert "# g11-no-auto-promote" not in (ROOT / "README.md").read_text(encoding="utf-8")
    finally:
        remove_worktree(ROOT, handle, force=True)
