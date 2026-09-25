"""Bounded workspace grant helpers — imports cleaned for ruff."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now


class WorkspaceGrant(StrictModel):
    """Server-issued grant for a bounded filesystem root."""

    grant_id: str = Field(default_factory=lambda: new_id("wsg_"))
    worker_id: str
    project_id: str
    root_path: str
    task_id: str | None = None
    read_only: bool = False
    max_bytes: int | None = 256 * 1024 * 1024
    created_at: datetime = Field(default_factory=utc_now)
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.revoked_at is None


class WorkspaceBoundError(PermissionError):
    """Path escapes the granted root or grant is inactive."""


@dataclass
class BoundedWorkspace:
    """Enforce all FS access under an authorized grant root."""

    grant: WorkspaceGrant
    _root: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._root = Path(self.grant.root_path).resolve()

    def ensure_root(self) -> Path:
        if not self.grant.active:
            raise WorkspaceBoundError("workspace_grant_revoked")
        self._root.mkdir(parents=True, exist_ok=True)
        return self._root

    def resolve(self, relative: str | os.PathLike[str]) -> Path:
        if not self.grant.active:
            raise WorkspaceBoundError("workspace_grant_revoked")
        root = self._root
        candidate = (root / Path(relative)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise WorkspaceBoundError(f"path_escapes_workspace:{candidate}") from exc
        return candidate

    def reject_unbounded_mount(self, mount_path: str | os.PathLike[str]) -> None:
        """Reject whole-checkout / unbounded roots on the normal path."""
        path = Path(mount_path).resolve()
        if (path / ".git").is_dir() and (path / "src").is_dir() and path == self._root:
            raise WorkspaceBoundError("whole_repo_workspace_forbidden")

    def write_text(self, relative: str, content: str, *, encoding: str = "utf-8") -> Path:
        if self.grant.read_only:
            raise WorkspaceBoundError("workspace_read_only")
        path = self.resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode(encoding)
        if self.grant.max_bytes is not None and len(data) > self.grant.max_bytes:
            raise WorkspaceBoundError("workspace_max_bytes_exceeded")
        path.write_bytes(data)
        return path

    def to_dict(self) -> dict[str, Any]:
        return {
            "grant_id": self.grant.grant_id,
            "worker_id": self.grant.worker_id,
            "project_id": self.grant.project_id,
            "root_path": str(self._root),
            "task_id": self.grant.task_id,
            "read_only": self.grant.read_only,
            "max_bytes": self.grant.max_bytes,
            "active": self.grant.active,
        }


@dataclass
class WorkspaceGrantRegistry:
    """In-memory grant issuer used by the product API / connector."""

    _grants: dict[str, WorkspaceGrant] = field(default_factory=dict)

    def issue(
        self,
        *,
        worker_id: str,
        project_id: str,
        root_path: str | Path,
        task_id: str | None = None,
        read_only: bool = False,
        max_bytes: int | None = 256 * 1024 * 1024,
    ) -> WorkspaceGrant:
        root = Path(root_path).resolve()
        if (root / ".git").is_dir() and (root / "src").is_dir():
            raise WorkspaceBoundError("whole_repo_workspace_forbidden")
        grant = WorkspaceGrant(
            worker_id=worker_id,
            project_id=project_id,
            root_path=str(root),
            task_id=task_id,
            read_only=read_only,
            max_bytes=max_bytes,
        )
        root.mkdir(parents=True, exist_ok=True)
        self._grants[grant.grant_id] = grant
        return grant

    def get(self, grant_id: str) -> WorkspaceGrant | None:
        return self._grants.get(grant_id)

    def revoke(self, grant_id: str) -> WorkspaceGrant:
        grant = self._grants.get(grant_id)
        if grant is None:
            raise WorkspaceBoundError("workspace_grant_not_found")
        updated = grant.model_copy(update={"revoked_at": utc_now()})
        self._grants[grant_id] = updated
        return updated

    def bind(self, grant_id: str) -> BoundedWorkspace:
        grant = self.get(grant_id)
        if grant is None or not grant.active:
            raise WorkspaceBoundError("workspace_grant_inactive")
        return BoundedWorkspace(grant=grant)

    def for_worker(self, worker_id: str) -> list[WorkspaceGrant]:
        return [g for g in self._grants.values() if g.worker_id == worker_id and g.active]
