"""Durable Goal entity above missions (V1.8 foundation; used by V1.7 linkage)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from swarm.contracts.common import StrictModel, new_id, utc_now
from pydantic import Field


class GoalStatus(StrEnum):
    ACTIVE = "active"
    WAITING = "waiting"
    BLOCKED = "blocked"
    PAUSED = "paused"
    ACHIEVED = "achieved"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


_ALLOWED_TRANSITIONS: dict[GoalStatus, set[GoalStatus]] = {
    GoalStatus.ACTIVE: {
        GoalStatus.WAITING,
        GoalStatus.BLOCKED,
        GoalStatus.PAUSED,
        GoalStatus.ACHIEVED,
        GoalStatus.CANCELLED,
        GoalStatus.EXPIRED,
    },
    GoalStatus.WAITING: {
        GoalStatus.ACTIVE,
        GoalStatus.BLOCKED,
        GoalStatus.PAUSED,
        GoalStatus.CANCELLED,
        GoalStatus.EXPIRED,
    },
    GoalStatus.BLOCKED: {
        GoalStatus.ACTIVE,
        GoalStatus.WAITING,
        GoalStatus.PAUSED,
        GoalStatus.CANCELLED,
        GoalStatus.EXPIRED,
    },
    GoalStatus.PAUSED: {
        GoalStatus.ACTIVE,
        GoalStatus.WAITING,
        GoalStatus.CANCELLED,
        GoalStatus.EXPIRED,
    },
    GoalStatus.ACHIEVED: set(),
    GoalStatus.CANCELLED: set(),
    GoalStatus.EXPIRED: set(),
}


class Goal(StrictModel):
    id: str = Field(default_factory=lambda: new_id("goal_"))
    project_id: str
    desired_outcome: str
    verification_criteria: list[str] = Field(default_factory=list)
    scope: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    resource_envelope: dict[str, Any] = Field(default_factory=dict)
    authority_envelope: dict[str, Any] = Field(default_factory=dict)
    owner: str = "operator"
    permitted_agents: list[str] = Field(default_factory=list)
    strategy: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    mission_ids: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    review_cadence: str | None = None
    status: GoalStatus = GoalStatus.ACTIVE
    decision_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class GoalStore:
    root: Path
    goals: dict[str, Goal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._load()

    def _path(self) -> Path:
        return self.root / "goals.json"

    def _load(self) -> None:
        path = self._path()
        if not path.is_file():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return
        for row in raw.get("goals") or []:
            try:
                goal = Goal.model_validate(row)
                self.goals[goal.id] = goal
            except (TypeError, ValueError):
                continue

    def _save(self) -> None:
        payload = {
            "schema_version": "1.0",
            "goals": [g.model_dump(mode="json") for g in self.goals.values()],
        }
        tmp = self._path().with_suffix(".partial")
        tmp.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        tmp.replace(self._path())

    def create(self, goal: Goal) -> Goal:
        self.goals[goal.id] = goal
        self._save()
        return goal

    def get(self, goal_id: str) -> Goal:
        if goal_id not in self.goals:
            self._load()
        if goal_id not in self.goals:
            raise KeyError(goal_id)
        return self.goals[goal_id]

    def list(self, *, project_id: str | None = None) -> list[Goal]:
        rows = list(self.goals.values())
        if project_id:
            rows = [g for g in rows if g.project_id == project_id]
        return sorted(rows, key=lambda g: g.created_at)

    def transition(self, goal_id: str, new_status: GoalStatus, *, reason: str, actor: str) -> Goal:
        goal = self.get(goal_id)
        allowed = _ALLOWED_TRANSITIONS.get(goal.status, set())
        if new_status not in allowed:
            raise ValueError(f"illegal_goal_transition:{goal.status.value}->{new_status.value}")
        history = list(goal.decision_history)
        history.append(
            {
                "at": utc_now().isoformat(),
                "actor": actor,
                "from": goal.status.value,
                "to": new_status.value,
                "reason": reason,
            }
        )
        updated = goal.model_copy(
            update={
                "status": new_status,
                "decision_history": history,
                "updated_at": utc_now().isoformat(),
            }
        )
        self.goals[goal_id] = updated
        self._save()
        return updated

    def link_mission(self, goal_id: str, mission_id: str) -> Goal:
        goal = self.get(goal_id)
        missions = list(goal.mission_ids)
        if mission_id not in missions:
            missions.append(mission_id)
        updated = goal.model_copy(
            update={"mission_ids": missions, "updated_at": utc_now().isoformat()}
        )
        self.goals[goal_id] = updated
        self._save()
        return updated
