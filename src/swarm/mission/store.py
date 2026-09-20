"""File-backed mission persistence and live state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import utc_now


@dataclass
class MissionRecord:
    mission_id: str
    goal: str
    status: str
    created_at: str
    updated_at: str
    revision: int = 1
    plan: dict[str, Any] = field(default_factory=dict)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    agents: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    retries: list[dict[str, Any]] = field(default_factory=list)
    model_assignments: list[dict[str, Any]] = field(default_factory=list)
    cost: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "revision": self.revision,
            "plan": self.plan,
            "tasks": self.tasks,
            "timeline": self.timeline,
            "agents": self.agents,
            "artifacts": self.artifacts,
            "validation": self.validation,
            "retries": self.retries,
            "model_assignments": self.model_assignments,
            "cost": self.cost,
            "result": self.result,
        }


class MissionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        return self.root / f"{mission_id}.json"

    def save(self, record: MissionRecord) -> Path:
        record.updated_at = utc_now().isoformat()
        path = self._path(record.mission_id)
        path.write_text(json.dumps(record.to_dict(), indent=2, default=str) + "\n")
        return path

    def load(self, mission_id: str) -> MissionRecord:
        raw = json.loads(self._path(mission_id).read_text())
        known = set(MissionRecord.__dataclass_fields__.keys())
        clean = {k: v for k, v in raw.items() if k in known}
        return MissionRecord(**clean)

    def list_missions(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for path in sorted(self.root.glob("*.json")):
            try:
                data = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            mid = data.get("mission_id")
            if not mid or mid in seen:
                continue
            seen.add(str(mid))
            rows.append(
                {
                    "mission_id": mid,
                    "status": data.get("status"),
                    "goal": data.get("goal"),
                    "updated_at": data.get("updated_at"),
                    "path": str(path),
                }
            )
        return rows

    def append_timeline(self, record: MissionRecord, event: str, detail: dict[str, Any]) -> None:
        record.timeline.append(
            {"at": utc_now().isoformat(), "event": event, "detail": detail}
        )
