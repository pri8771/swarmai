"""Serializable session checkpoints — no clients or secrets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now
from swarm.contracts.enums import AttemptStatus, TaskStatus


class SessionCheckpoint(StrictModel):
    schema_version: str = "1.0"
    checkpoint_id: str = Field(default_factory=lambda: new_id("cp_"))
    session_id: str
    agent_profile_id: str
    task_id: str
    attempt_id: str
    route_id: str | None = None
    task_status: TaskStatus = TaskStatus.RUNNING
    attempt_status: AttemptStatus = AttemptStatus.RUNNING
    model_calls: int = 0
    tool_operation_ids: list[str] = Field(default_factory=list)
    artifact_refs: list[str] = Field(default_factory=list)
    finding_ids: list[str] = Field(default_factory=list)
    waiting_for_children: list[str] = Field(default_factory=list)
    cancel_requested: bool = False
    decision_trace: list[dict[str, Any]] = Field(default_factory=list)
    resource_usage: dict[str, int] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    def to_serializable(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        blob = json.dumps(data, sort_keys=True).lower()
        for banned in ("sk-", "api_key=", "secret=", "runtime_client", "bearer "):
            if banned in blob:
                raise RuntimeError(f"checkpoint_leak:{banned.strip()}")
        return data


class CheckpointStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        if root is not None:
            root.mkdir(parents=True, exist_ok=True)
        self._mem: dict[str, SessionCheckpoint] = {}

    def save(self, checkpoint: SessionCheckpoint) -> str:
        payload = checkpoint.to_serializable()
        self._mem[checkpoint.checkpoint_id] = checkpoint
        if self.root is not None:
            path = self.root / f"{checkpoint.checkpoint_id}.json"
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return checkpoint.checkpoint_id

    def load(self, checkpoint_id: str) -> SessionCheckpoint:
        if checkpoint_id in self._mem:
            return self._mem[checkpoint_id]
        if self.root is None:
            raise KeyError(checkpoint_id)
        path = self.root / f"{checkpoint_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        cp = SessionCheckpoint.model_validate(data)
        self._mem[checkpoint_id] = cp
        return cp
