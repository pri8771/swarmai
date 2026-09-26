"""Weighted deficit round-robin selector (ART-V23-SCHEDULER, policy v23-wdrr-1).

Pure and deterministic: no I/O, no clocks (``now`` is injected), inputs are never
mutated. Two levels: project first, then mission inside the chosen project, then
the task inside the chosen mission.

Credit accounting per decision (project level; mission level is identical inside
the chosen project):

* every *eligible* project accrues ``base_quantum * weight``, capped at
  ``max_credit_cap_multiplier * weight * base_quantum``;
* the chosen project is charged ``service_cost * base_quantum * total_eligible_weight``;
* ineligible projects (paused, at cap, blocked work only) neither accrue nor pay.

Long-run admitted share is therefore proportional to weight. Urgency, aging and
deadline bonuses change the *score* only (bounded by ``urgent_borrow_cap``), never
the credit, so they cannot amplify long-run share.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from swarm.contracts.common import payload_hash
from swarm.contracts.v23 import (
    SCHEDULABLE_MISSION_STATES,
    V23_POLICY_VERSION,
    MissionQueueLifecycle,
    MissionQueueState,
    PriorityClass,
    ProjectQueueState,
    ReasonCode,
    SchedulableTask,
    SchedulerDecision,
)

ResourceCheck = Callable[[SchedulableTask], bool]


@dataclass(frozen=True)
class WdrrConfig:
    policy_version: str = V23_POLICY_VERSION
    base_quantum: float = 1.0
    max_credit_cap_multiplier: float = 10.0
    urgent_borrow_cap: float = 2.0
    aging_floor_ms: int = 60_000
    aging_bonus: float = 0.5
    deadline_bonus_cap: float = 1.0
    deadline_slack_ms: int = 300_000
    restart_credit_cap_multiplier: float = 10.0

    @classmethod
    def from_policy_file(cls, path: Path) -> WdrrConfig:
        data = json.loads(path.read_text(encoding="utf-8"))
        wdrr: dict[str, Any] = data["wdrr"]
        return cls(
            policy_version=str(data["policy_version"]),
            base_quantum=float(wdrr["base_quantum"]),
            max_credit_cap_multiplier=float(wdrr["max_credit_cap_multiplier"]),
            urgent_borrow_cap=float(wdrr["urgent_borrow_cap"]),
            aging_floor_ms=int(wdrr["aging_floor_ms"]),
            aging_bonus=float(wdrr["aging_bonus"]),
            deadline_bonus_cap=float(wdrr["deadline_bonus_cap"]),
            deadline_slack_ms=int(wdrr["deadline_slack_ms"]),
            restart_credit_cap_multiplier=float(wdrr["restart_credit_cap_multiplier"]),
        )


@dataclass(frozen=True)
class Selection:
    decision: SchedulerDecision
    reason_code: ReasonCode
    project_id: str | None = None
    mission_id: str | None = None
    task: SchedulableTask | None = None
    scores: dict[str, float] = field(default_factory=dict)
    credits_before: dict[str, float] = field(default_factory=dict)
    credits_after: dict[str, float] = field(default_factory=dict)
    mission_credits_after: dict[str, float] = field(default_factory=dict)
    candidate_set_hash: str = ""
    blocked: dict[str, str] = field(default_factory=dict)


def _cap(weight: float, config: WdrrConfig) -> float:
    return config.max_credit_cap_multiplier * weight * config.base_quantum


def _eligible_tasks_by_mission(
    missions: Sequence[MissionQueueState],
    tasks: Sequence[SchedulableTask],
    resource_available: ResourceCheck | None,
    blocked: dict[str, str],
) -> dict[str, list[SchedulableTask]]:
    mission_by_id = {m.mission_id: m for m in missions}
    out: dict[str, list[SchedulableTask]] = {}
    for task in sorted(tasks, key=lambda t: t.task_id):
        mission = mission_by_id.get(task.mission_id)
        if mission is None or mission.project_id != task.project_id:
            blocked[task.task_id] = ReasonCode.ISOLATION_DENIED.value
            continue
        if mission.lifecycle not in SCHEDULABLE_MISSION_STATES:
            reason = (
                ReasonCode.DRAINING
                if mission.lifecycle == MissionQueueLifecycle.DRAINING
                else ReasonCode.NO_ELIGIBLE_WORK
            )
            blocked[task.task_id] = reason.value
            continue
        if task.cancellation_generation != mission.cancellation_generation:
            blocked[task.task_id] = ReasonCode.CANCELLED_GENERATION.value
            continue
        if not task.dependencies_ready:
            blocked[task.task_id] = ReasonCode.NO_ELIGIBLE_WORK.value
            continue
        if mission.running >= mission.max_parallelism:
            blocked[task.task_id] = ReasonCode.MISSION_PARALLELISM_CAP.value
            continue
        if resource_available is not None and not resource_available(task):
            blocked[task.task_id] = ReasonCode.DEFERRED_RESOURCE_UNAVAILABLE.value
            continue
        out.setdefault(task.mission_id, []).append(task)
    return out


def _bonus(
    missions: Sequence[MissionQueueState],
    tasks: Sequence[SchedulableTask],
    *,
    now: datetime,
    config: WdrrConfig,
) -> float:
    urgent = 1.0 if any(m.priority == PriorityClass.URGENT for m in missions) else 0.0
    aging = 0.0
    if tasks and config.aging_floor_ms > 0:
        oldest = min(t.enqueued_at for t in tasks)
        waited_ms = max(0.0, (now - oldest).total_seconds() * 1000.0)
        aging = config.aging_bonus * float(int(waited_ms // config.aging_floor_ms))
    deadline = 0.0
    for m in missions:
        if m.deadline_at is None:
            continue
        slack_ms = (m.deadline_at - now).total_seconds() * 1000.0
        if slack_ms <= config.deadline_slack_ms:
            deadline = config.deadline_bonus_cap
    return min(config.urgent_borrow_cap, urgent + aging + deadline) * config.base_quantum


def candidate_set_hash(
    projects: Sequence[ProjectQueueState],
    missions: Sequence[MissionQueueState],
    tasks: Sequence[SchedulableTask],
) -> str:
    body = {
        "projects": sorted(
            [p.project_id, p.version, round(p.credit, 9), p.paused, p.running] for p in projects
        ),
        "missions": sorted(
            [m.mission_id, m.version, round(m.credit, 9), m.lifecycle.value, m.running]
            for m in missions
        ),
        "tasks": sorted(
            [t.task_id, t.attempt_id, t.dependencies_ready, t.cancellation_generation]
            for t in tasks
        ),
    }
    return payload_hash(body)


def _pick(
    ids: list[str],
    *,
    credit_after_accrual: dict[str, float],
    bonus: dict[str, float],
    last_served: dict[str, int],
) -> tuple[str, dict[str, float]]:
    scores = {i: credit_after_accrual[i] + bonus[i] for i in ids}
    chosen = min(ids, key=lambda i: (-scores[i], last_served[i], i))
    return chosen, scores


def select_next(
    projects: Sequence[ProjectQueueState],
    missions: Sequence[MissionQueueState],
    tasks: Sequence[SchedulableTask],
    *,
    now: datetime,
    config: WdrrConfig | None = None,
    resource_available: ResourceCheck | None = None,
) -> Selection:
    cfg = config or WdrrConfig()
    cset = candidate_set_hash(projects, missions, tasks)
    credits_before = {p.project_id: p.credit for p in projects}
    blocked: dict[str, str] = {}

    by_mission = _eligible_tasks_by_mission(missions, tasks, resource_available, blocked)
    missions_by_project: dict[str, list[MissionQueueState]] = {}
    for m in missions:
        if m.mission_id in by_mission:
            missions_by_project.setdefault(m.project_id, []).append(m)

    eligible: list[ProjectQueueState] = []
    for p in sorted(projects, key=lambda x: x.project_id):
        if p.paused:
            blocked[p.project_id] = ReasonCode.DRAINING.value
            continue
        if p.running >= p.max_concurrency:
            blocked[p.project_id] = ReasonCode.PROJECT_CONCURRENCY_CAP.value
            continue
        if p.project_id not in missions_by_project:
            continue
        eligible.append(p)

    if not eligible:
        reason = ReasonCode.NO_ELIGIBLE_WORK
        decision = SchedulerDecision.IDLE
        priority = [
            ReasonCode.DEFERRED_RESOURCE_UNAVAILABLE,
            ReasonCode.PROJECT_CONCURRENCY_CAP,
            ReasonCode.MISSION_PARALLELISM_CAP,
        ]
        for code in priority:
            if code.value in blocked.values():
                reason = code
                decision = SchedulerDecision.DEFER
                break
        return Selection(
            decision=decision,
            reason_code=reason,
            credits_before=credits_before,
            credits_after=dict(credits_before),
            candidate_set_hash=cset,
            blocked=blocked,
        )

    q = cfg.base_quantum
    accrued = {
        p.project_id: min(p.credit + q * p.weight, _cap(p.weight, cfg)) for p in eligible
    }
    p_bonus = {
        p.project_id: _bonus(
            missions_by_project[p.project_id],
            [t for m in missions_by_project[p.project_id] for t in by_mission[m.mission_id]],
            now=now,
            config=cfg,
        )
        for p in eligible
    }
    project_id, scores = _pick(
        [p.project_id for p in eligible],
        credit_after_accrual=accrued,
        bonus=p_bonus,
        last_served={p.project_id: p.last_served_seq for p in eligible},
    )

    chosen_missions = sorted(missions_by_project[project_id], key=lambda m: m.mission_id)
    m_accrued = {
        m.mission_id: min(m.credit + q * m.weight, _cap(m.weight, cfg)) for m in chosen_missions
    }
    m_bonus = {
        m.mission_id: _bonus([m], by_mission[m.mission_id], now=now, config=cfg)
        for m in chosen_missions
    }
    mission_id, _m_scores = _pick(
        [m.mission_id for m in chosen_missions],
        credit_after_accrual=m_accrued,
        bonus=m_bonus,
        last_served={m.mission_id: m.last_served_seq for m in chosen_missions},
    )
    task = min(
        by_mission[mission_id], key=lambda t: (-t.priority, t.enqueued_at, t.task_id)
    )

    total_w = sum(p.weight for p in eligible)
    credits_after = dict(credits_before)
    credits_after.update(accrued)
    credits_after[project_id] = accrued[project_id] - task.service_cost * q * total_w

    total_mw = sum(m.weight for m in chosen_missions)
    mission_credits_after = {m.mission_id: m.credit for m in missions}
    mission_credits_after.update(m_accrued)
    mission_credits_after[mission_id] = m_accrued[mission_id] - task.service_cost * q * total_mw

    return Selection(
        decision=SchedulerDecision.ADMIT,
        reason_code=ReasonCode.ADMITTED,
        project_id=project_id,
        mission_id=mission_id,
        task=task,
        scores=scores,
        credits_before=credits_before,
        credits_after=credits_after,
        mission_credits_after=mission_credits_after,
        candidate_set_hash=cset,
        blocked=blocked,
    )


def apply_selection(
    projects: Sequence[ProjectQueueState],
    missions: Sequence[MissionQueueState],
    selection: Selection,
    *,
    sequence: int,
) -> tuple[list[ProjectQueueState], list[MissionQueueState]]:
    """Return updated copies (credits, running counts, last_served_seq). Inputs untouched."""
    if selection.decision != SchedulerDecision.ADMIT:
        return [p.model_copy() for p in projects], [m.model_copy() for m in missions]
    new_projects: list[ProjectQueueState] = []
    for p in projects:
        update: dict[str, Any] = {"credit": selection.credits_after.get(p.project_id, p.credit)}
        if p.project_id == selection.project_id:
            update["running"] = p.running + 1
            update["last_served_seq"] = sequence
        new_projects.append(p.model_copy(update=update))
    new_missions: list[MissionQueueState] = []
    for m in missions:
        update = {"credit": selection.mission_credits_after.get(m.mission_id, m.credit)}
        if m.mission_id == selection.mission_id:
            update["running"] = m.running + 1
            update["last_served_seq"] = sequence
            update["lifecycle"] = MissionQueueLifecycle.RUNNING
        new_missions.append(m.model_copy(update=update))
    return new_projects, new_missions


def clamp_restart_credit(
    projects: Sequence[ProjectQueueState], config: WdrrConfig | None = None
) -> list[ProjectQueueState]:
    """After restart, clamp only the positive side of credit (debt is preserved)."""
    cfg = config or WdrrConfig()
    out: list[ProjectQueueState] = []
    for p in projects:
        cap = cfg.restart_credit_cap_multiplier * p.weight * cfg.base_quantum
        out.append(p.model_copy(update={"credit": min(p.credit, cap)}))
    return out
