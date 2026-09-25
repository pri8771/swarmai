"""Durable Goal entity above missions (V1.8 lifecycle).

Mission completion is recorded as a contribution; it never implies goal
achievement. Terminal goals recover only through an explicit restart that
retains decision history.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now


class GoalStatus(StrEnum):
    ACTIVE = "active"
    WAITING = "waiting"
    BLOCKED = "blocked"
    PAUSED = "paused"
    ACHIEVED = "achieved"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class GoalKind(StrEnum):
    FINITE = "finite"
    ONGOING = "ongoing"


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

# Explicit restart is the only recovery path out of terminal/paused recovery.
_RESTARTABLE: set[GoalStatus] = {
    GoalStatus.PAUSED,
    GoalStatus.CANCELLED,
    GoalStatus.EXPIRED,
    GoalStatus.ACHIEVED,
}

_TRIGGERABLE: set[GoalStatus] = {
    GoalStatus.ACTIVE,
    GoalStatus.WAITING,
}


class GoalError(ValueError):
    """Domain error for illegal Goal lifecycle operations."""


class Goal(StrictModel):
    id: str = Field(default_factory=lambda: new_id("goal_"))
    project_id: str
    desired_outcome: str
    verification_criteria: list[str] = Field(default_factory=list)
    kind: GoalKind = GoalKind.FINITE
    scope: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    resource_envelope: dict[str, Any] = Field(default_factory=dict)
    authority_envelope: dict[str, Any] = Field(default_factory=dict)
    owner: str = "operator"
    permitted_agents: list[str] = Field(default_factory=list)
    strategy: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    mission_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    mission_outcomes: list[dict[str, Any]] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    review_cadence: str | None = None
    expires_at: str | None = None
    status: GoalStatus = GoalStatus.ACTIVE
    progress: list[dict[str, Any]] = Field(default_factory=list)
    decision_history: list[dict[str, Any]] = Field(default_factory=list)
    trigger_receipts: list[dict[str, Any]] = Field(default_factory=list)
    restart_count: int = 0
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())


def allowed_transitions(status: GoalStatus) -> set[GoalStatus]:
    return set(_ALLOWED_TRANSITIONS.get(status, set()))


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
        loaded: dict[str, Goal] = {}
        for row in raw.get("goals") or []:
            try:
                goal = Goal.model_validate(row)
                loaded[goal.id] = goal
            except (TypeError, ValueError):
                continue
        self.goals = loaded

    def _save(self) -> None:
        payload = {
            "schema_version": "1.8",
            "goals": [g.model_dump(mode="json") for g in self.goals.values()],
        }
        tmp = self._path().with_suffix(".partial")
        tmp.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        tmp.replace(self._path())

    def _reload(self) -> None:
        self._load()

    def _append_decision(
        self,
        goal: Goal,
        *,
        actor: str,
        action: str,
        reason: str,
        extra: dict[str, Any] | None = None,
        from_status: GoalStatus | None = None,
        to_status: GoalStatus | None = None,
    ) -> list[dict[str, Any]]:
        entry: dict[str, Any] = {
            "at": utc_now().isoformat(),
            "actor": actor,
            "action": action,
            "reason": reason,
        }
        if from_status is not None:
            entry["from"] = from_status.value
        if to_status is not None:
            entry["to"] = to_status.value
        if extra:
            entry.update(extra)
        history = list(goal.decision_history)
        history.append(entry)
        return history

    def _persist(self, goal: Goal) -> Goal:
        self.goals[goal.id] = goal
        self._save()
        return goal

    def create(self, goal: Goal) -> Goal:
        self._reload()
        if goal.id in self.goals:
            raise GoalError(f"goal_already_exists:{goal.id}")
        history = list(goal.decision_history)
        if not history:
            history = self._append_decision(
                goal,
                actor=goal.owner,
                action="create",
                reason="goal_created",
                from_status=None,
                to_status=goal.status,
                extra={"kind": goal.kind.value},
            )
            goal = goal.model_copy(update={"decision_history": history})
        return self._persist(goal)

    def get(self, goal_id: str) -> Goal:
        if goal_id not in self.goals:
            self._load()
        if goal_id not in self.goals:
            raise KeyError(goal_id)
        return self.goals[goal_id]

    def list_goals(self, *, project_id: str | None = None) -> list[Goal]:
        self._reload()
        rows = list(self.goals.values())
        if project_id:
            rows = [g for g in rows if g.project_id == project_id]
        return sorted(rows, key=lambda g: g.created_at)

    def transition(
        self,
        goal_id: str,
        new_status: GoalStatus,
        *,
        reason: str,
        actor: str,
        action: str = "transition",
    ) -> Goal:
        self._reload()
        goal = self.get(goal_id)
        allowed = _ALLOWED_TRANSITIONS.get(goal.status, set())
        if new_status not in allowed:
            raise GoalError(f"illegal_goal_transition:{goal.status.value}->{new_status.value}")
        if new_status == GoalStatus.ACHIEVED and goal.kind == GoalKind.ONGOING:
            # Ongoing goals record milestones via progress; they do not terminate as achieved.
            raise GoalError("ongoing_goal_cannot_achieve")
        history = self._append_decision(
            goal,
            actor=actor,
            action=action,
            reason=reason,
            from_status=goal.status,
            to_status=new_status,
        )
        updated = goal.model_copy(
            update={
                "status": new_status,
                "decision_history": history,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._persist(updated)

    def pause(self, goal_id: str, *, reason: str, actor: str) -> Goal:
        return self.transition(
            goal_id, GoalStatus.PAUSED, reason=reason, actor=actor, action="pause"
        )

    def resume(self, goal_id: str, *, reason: str, actor: str) -> Goal:
        self._reload()
        goal = self.get(goal_id)
        if goal.status != GoalStatus.PAUSED:
            raise GoalError(f"resume_requires_paused:{goal.status.value}")
        return self.transition(
            goal_id, GoalStatus.ACTIVE, reason=reason, actor=actor, action="resume"
        )

    def cancel(self, goal_id: str, *, reason: str, actor: str) -> Goal:
        return self.transition(
            goal_id, GoalStatus.CANCELLED, reason=reason, actor=actor, action="cancel"
        )

    def restart(self, goal_id: str, *, reason: str, actor: str) -> Goal:
        """Recover a paused/terminal goal to active without wiping history."""
        self._reload()
        goal = self.get(goal_id)
        if goal.status not in _RESTARTABLE:
            raise GoalError(f"restart_not_allowed:{goal.status.value}")
        history = self._append_decision(
            goal,
            actor=actor,
            action="restart",
            reason=reason,
            from_status=goal.status,
            to_status=GoalStatus.ACTIVE,
            extra={"restart_count": goal.restart_count + 1},
        )
        updated = goal.model_copy(
            update={
                "status": GoalStatus.ACTIVE,
                "decision_history": history,
                "restart_count": goal.restart_count + 1,
                "blockers": [],
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._persist(updated)

    def link_mission(self, goal_id: str, mission_id: str) -> Goal:
        self._reload()
        goal = self.get(goal_id)
        missions = list(goal.mission_ids)
        if mission_id not in missions:
            missions.append(mission_id)
        updated = goal.model_copy(
            update={"mission_ids": missions, "updated_at": utc_now().isoformat()}
        )
        return self._persist(updated)

    def record_mission_outcome(
        self,
        goal_id: str,
        *,
        mission_id: str,
        outcome: str,
        actor: str,
        notes: str = "",
        evidence_refs: list[str] | None = None,
    ) -> Goal:
        """Record a mission result. Never auto-achieves the goal."""
        self._reload()
        goal = self.get(goal_id)
        missions = list(goal.mission_ids)
        if mission_id not in missions:
            missions.append(mission_id)
        outcomes = list(goal.mission_outcomes)
        outcomes.append(
            {
                "at": utc_now().isoformat(),
                "mission_id": mission_id,
                "outcome": outcome,
                "actor": actor,
                "notes": notes,
                "evidence_refs": list(evidence_refs or []),
            }
        )
        evidence = list(goal.evidence_refs)
        for ref in list(evidence_refs or []):
            if ref not in evidence:
                evidence.append(ref)
        history = self._append_decision(
            goal,
            actor=actor,
            action="mission_outcome",
            reason=notes or outcome,
            extra={
                "mission_id": mission_id,
                "mission_outcome": outcome,
                "goal_status_unchanged": goal.status.value,
            },
        )
        updated = goal.model_copy(
            update={
                "mission_ids": missions,
                "mission_outcomes": outcomes,
                "evidence_refs": evidence,
                "decision_history": history,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._persist(updated)

    def record_progress(
        self,
        goal_id: str,
        *,
        summary: str,
        actor: str,
        metrics: dict[str, Any] | None = None,
    ) -> Goal:
        self._reload()
        goal = self.get(goal_id)
        progress = list(goal.progress)
        entry = {
            "at": utc_now().isoformat(),
            "actor": actor,
            "summary": summary,
            "metrics": dict(metrics or {}),
        }
        progress.append(entry)
        history = self._append_decision(
            goal,
            actor=actor,
            action="progress",
            reason=summary,
            extra={"metrics": dict(metrics or {})},
        )
        updated = goal.model_copy(
            update={
                "progress": progress,
                "decision_history": history,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._persist(updated)

    def apply_strategy(
        self,
        goal_id: str,
        *,
        strategy: str,
        actor: str,
        reason: str,
    ) -> Goal:
        """Update strategy text only — used by V1.9 pursuit lesson adopt/rollback."""
        self._reload()
        goal = self.get(goal_id)
        history = self._append_decision(
            goal,
            actor=actor,
            action="strategy",
            reason=reason,
            extra={"strategy": strategy},
        )
        updated = goal.model_copy(
            update={
                "strategy": strategy,
                "decision_history": history,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._persist(updated)

    def accept_trigger(
        self,
        goal_id: str,
        *,
        dedupe_key: str,
        trigger_kind: str,
        actor: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[Goal, dict[str, Any]]:
        """Admit a trigger receipt; duplicates return the prior receipt."""
        if not dedupe_key.strip():
            raise GoalError("dedupe_key_required")
        self._reload()
        goal = self.get(goal_id)
        if goal.status not in _TRIGGERABLE:
            raise GoalError(f"trigger_not_allowed:{goal.status.value}")
        self.evaluate_expiry(goal_id, actor=actor)
        goal = self.get(goal_id)
        if goal.status not in _TRIGGERABLE:
            raise GoalError(f"trigger_not_allowed:{goal.status.value}")

        for prior in goal.trigger_receipts:
            if prior.get("dedupe_key") == dedupe_key:
                dup = dict(prior)
                dup["duplicate"] = True
                return goal, dup

        receipt_id = new_id("gtr_")
        receipt: dict[str, Any] = {
            "receipt_id": receipt_id,
            "dedupe_key": dedupe_key,
            "trigger_kind": trigger_kind,
            "actor": actor,
            "at": utc_now().isoformat(),
            "payload": dict(payload or {}),
            "duplicate": False,
        }
        receipts = list(goal.trigger_receipts)
        receipts.append(receipt)
        history = self._append_decision(
            goal,
            actor=actor,
            action="trigger",
            reason=f"trigger:{trigger_kind}",
            extra={"receipt_id": receipt_id, "dedupe_key": dedupe_key},
        )
        updated = goal.model_copy(
            update={
                "trigger_receipts": receipts,
                "decision_history": history,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._persist(updated), receipt

    def evaluate_expiry(self, goal_id: str, *, actor: str = "system") -> Goal:
        """Expire an open goal whose expires_at has passed."""
        self._reload()
        goal = self.get(goal_id)
        if goal.expires_at is None:
            return goal
        if goal.status in {
            GoalStatus.ACHIEVED,
            GoalStatus.CANCELLED,
            GoalStatus.EXPIRED,
        }:
            return goal
        try:
            raw = goal.expires_at.replace("Z", "+00:00")
            expires = datetime.fromisoformat(raw)
            now = utc_now()
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            if now < expires:
                return goal
        except ValueError as exc:
            raise GoalError(f"invalid_expires_at:{goal.expires_at}") from exc
        return self.transition(
            goal_id,
            GoalStatus.EXPIRED,
            reason="expires_at_reached",
            actor=actor,
            action="expire",
        )
