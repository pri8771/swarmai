"""Explicit R28d local-action test construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from swarm.mission.action_boundary import local_worktree_gateway
from swarm.mission.worker import RepoWorker
from swarm.tools.fences import ActorContext


def make_worker(repo: Path, **kwargs: Any) -> RepoWorker:
    project_id = str(kwargs.pop("project_id", "proj_test"))
    root = Path(kwargs.get("worktree_root") or repo)
    return RepoWorker(
        repo=repo,
        project_id=project_id,
        action_gateway=local_worktree_gateway(root),
        action_gateway_factory=local_worktree_gateway,
        actor_context=ActorContext(actor="test", project_id=project_id),
        **kwargs,
    )
