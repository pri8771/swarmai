"""V0.3 P33 — dependency queue, concurrency limits, quotas, backpressure."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.enums import TaskStatus
from swarm.contracts.mission import Mission, TaskSpec
from swarm.controller.scheduler import AdaptiveScheduler, SchedulerConfig


@dataclass
class ProviderQuota:
    provider_id: str
    max_in_flight: int = 4
    max_per_minute: int = 60
    in_flight: int = 0
    window_started: float = field(default_factory=time.monotonic)
    window_count: int = 0

    def try_acquire(self) -> bool:
        now = time.monotonic()
        if now - self.window_started >= 60.0:
            self.window_started = now
            self.window_count = 0
        if self.in_flight >= self.max_in_flight:
            return False
        if self.window_count >= self.max_per_minute:
            return False
        self.in_flight += 1
        self.window_count += 1
        return True

    def release(self) -> None:
        self.in_flight = max(0, self.in_flight - 1)


@dataclass
class QueuedWork:
    task: TaskSpec
    enqueued_at: float
    deadline_at: float | None = None
    cancelled: bool = False
    provider_id: str = "ollama"


@dataclass
class BackpressureScheduler:
    """Queue + concurrency + quota + timeout/cancel wrapper over AdaptiveScheduler."""

    inner: AdaptiveScheduler = field(default_factory=AdaptiveScheduler)
    queue: deque[QueuedWork] = field(default_factory=deque)
    quotas: dict[str, ProviderQuota] = field(default_factory=dict)
    default_timeout_s: float = 120.0
    max_queue: int = 500
    rejected_backpressure: int = 0
    timed_out: int = 0
    cancelled: int = 0
    completed: int = 0

    def __post_init__(self) -> None:
        if "ollama" not in self.quotas:
            self.quotas["ollama"] = ProviderQuota("ollama", max_in_flight=4, max_per_minute=120)

    def enqueue(
        self,
        task: TaskSpec,
        *,
        provider_id: str = "ollama",
        timeout_s: float | None = None,
    ) -> bool:
        if len(self.queue) >= self.max_queue:
            self.rejected_backpressure += 1
            return False
        timeout = self.default_timeout_s if timeout_s is None else timeout_s
        now = time.monotonic()
        self.queue.append(
            QueuedWork(
                task=task,
                enqueued_at=now,
                deadline_at=now + timeout if timeout > 0 else None,
                provider_id=provider_id,
            )
        )
        return True

    def cancel(self, task_id: str) -> bool:
        found = False
        for item in self.queue:
            if item.task.id == task_id and not item.cancelled:
                item.cancelled = True
                self.cancelled += 1
                found = True
        return found

    def _purge_expired(self) -> None:
        kept: deque[QueuedWork] = deque()
        now = time.monotonic()
        while self.queue:
            item = self.queue.popleft()
            if item.cancelled:
                continue
            if item.deadline_at is not None and now > item.deadline_at:
                self.timed_out += 1
                continue
            kept.append(item)
        self.queue = kept

    def dispatch(
        self,
        mission: Mission,
        *,
        inference_slots: int,
        worker_slots: int,
    ) -> tuple[list[QueuedWork], dict[str, Any]]:
        self._purge_expired()
        ready_tasks = [
            q.task.model_copy(update={"status": TaskStatus.READY})
            for q in self.queue
            if not q.cancelled
        ]
        selected, explanation = self.inner.choose_ready(
            mission,
            ready_tasks,
            inference_slots=inference_slots,
            worker_slots=worker_slots,
        )
        # Scale path: if qualification gates starve the queue, fall back to FIFO
        # under the same concurrency / reserve limits.
        if not selected and ready_tasks:
            slots = min(
                inference_slots,
                worker_slots,
                self.inner.config.max_concurrency,
            )
            usable = max(0, slots - self.inner.config.control_reserve_slots)
            if self.inner.state.cooldown_remaining > 0:
                usable = max(1, usable // 2) if usable else 0
            selected = ready_tasks[:usable]
            explanation = {
                **explanation,
                "fallback": "fifo_without_qualification_profiles",
                "selected": len(selected),
            }
        selected_ids = {t.id for t in selected}
        dispatched: list[QueuedWork] = []
        remaining: deque[QueuedWork] = deque()
        while self.queue:
            item = self.queue.popleft()
            if item.cancelled or item.task.id not in selected_ids:
                if not item.cancelled:
                    remaining.append(item)
                continue
            quota = self.quotas.setdefault(
                item.provider_id, ProviderQuota(item.provider_id)
            )
            if not quota.try_acquire():
                remaining.append(item)
                self.rejected_backpressure += 1
                continue
            dispatched.append(item)
        self.queue = remaining
        explanation = {
            **explanation,
            "dispatched": len(dispatched),
            "queue_depth": len(self.queue),
            "rejected_backpressure": self.rejected_backpressure,
            "timed_out": self.timed_out,
            "cancelled": self.cancelled,
            "quotas": {
                k: {"in_flight": v.in_flight, "window_count": v.window_count}
                for k, v in self.quotas.items()
            },
        }
        return dispatched, explanation

    def complete(self, provider_id: str = "ollama") -> None:
        if provider_id in self.quotas:
            self.quotas[provider_id].release()
        self.completed += 1

    def stats(self) -> dict[str, Any]:
        return {
            "queue_depth": len(self.queue),
            "rejected_backpressure": self.rejected_backpressure,
            "timed_out": self.timed_out,
            "cancelled": self.cancelled,
            "completed": self.completed,
            "max_queue": self.max_queue,
            "default_timeout_s": self.default_timeout_s,
            "inner_max_concurrency": self.inner.config.max_concurrency,
        }


def make_scale_scheduler(
    *,
    max_concurrency: int = 8,
    max_queue: int = 500,
    ollama_in_flight: int = 4,
) -> BackpressureScheduler:
    inner = AdaptiveScheduler(
        config=SchedulerConfig(max_concurrency=max_concurrency, control_reserve_slots=1)
    )
    sched = BackpressureScheduler(inner=inner, max_queue=max_queue)
    sched.quotas["ollama"] = ProviderQuota(
        "ollama", max_in_flight=ollama_in_flight, max_per_minute=180
    )
    return sched
