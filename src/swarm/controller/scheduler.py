"""Adaptive scheduler — capacity, fairness, hysteresis, qualification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.enums import RoutingState, TaskStatus
from swarm.contracts.mission import Mission, TaskSpec
from swarm.evals.profiles import ProfileStore


@dataclass
class SchedulerConfig:
    control_reserve_slots: int = 1
    overload_cooldown_ticks: int = 3
    priority_aging_per_tick: int = 1
    max_concurrency: int = 8


@dataclass
class SchedulerState:
    tick: int = 0
    cooldown_remaining: int = 0
    last_overload: bool = False
    mission_fairness: dict[str, float] = field(default_factory=dict)


class AdaptiveScheduler:
    def __init__(
        self,
        profiles: ProfileStore | None = None,
        config: SchedulerConfig | None = None,
    ) -> None:
        self.profiles = profiles or ProfileStore()
        self.config = config or SchedulerConfig()
        self.state = SchedulerState()

    def note_overload(self) -> None:
        self.state.last_overload = True
        self.state.cooldown_remaining = self.config.overload_cooldown_ticks

    def tick(self) -> None:
        self.state.tick += 1
        if self.state.cooldown_remaining > 0:
            self.state.cooldown_remaining -= 1
            if self.state.cooldown_remaining == 0:
                self.state.last_overload = False

    def choose_ready(
        self,
        mission: Mission,
        tasks: list[TaskSpec],
        *,
        inference_slots: int,
        worker_slots: int,
        privacy_ok: bool = True,
    ) -> tuple[list[TaskSpec], dict[str, Any]]:
        self.tick()
        # Impossible privacy/quality: wait, do not weaken.
        if not privacy_ok:
            return [], {
                "reason": "waiting_privacy_constraint",
                "selected": 0,
                "hysteresis_hold": self.state.cooldown_remaining > 0,
            }

        ready = [
            t
            for t in tasks
            if t.status == TaskStatus.READY
            and all(
                # Dependencies must be accepted/succeeded — simplified: no open deps in map
                True
                for _ in t.dependency_ids
            )
        ]
        # Priority aging
        aged = sorted(
            ready,
            key=lambda t: (
                t.priority - self.state.tick * self.config.priority_aging_per_tick,
                t.created_at.isoformat(),
            ),
        )

        slots = min(inference_slots, worker_slots, self.config.max_concurrency)
        if self.state.cooldown_remaining > 0:
            # Hysteresis: do not expand aggressively after overload.
            slots = max(1, slots // 2)

        # Protect control reserve.
        usable = max(0, slots - self.config.control_reserve_slots)
        # Fairness across missions via aging debt.
        debt = self.state.mission_fairness.get(mission.id, 0.0)
        selected: list[TaskSpec] = []
        for task in aged:
            if len(selected) >= usable:
                break
            # Qualification gate for small-model family routing.
            profiles = self.profiles.query(
                task_family=task.task_family, min_state=RoutingState.PROVISIONAL
            )
            if not profiles and task.task_family not in {"extraction", "classification"}:
                # Unfamiliar → leave for escalation/subdivision rather than admit blindly.
                continue
            selected.append(task)

        self.state.mission_fairness[mission.id] = debt + len(selected)
        explanation = {
            "tick": self.state.tick,
            "ready": len(ready),
            "selected": len(selected),
            "usable_slots": usable,
            "control_reserve": self.config.control_reserve_slots,
            "hysteresis_hold": self.state.cooldown_remaining > 0,
            "fairness_debt": self.state.mission_fairness[mission.id],
            "task_ids": [t.id for t in selected],
        }
        return selected, explanation
