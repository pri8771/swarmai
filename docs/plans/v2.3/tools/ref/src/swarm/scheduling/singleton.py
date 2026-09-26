"""Run a periodic tick in at most one process per site (V20-E06 / V23 singleton)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from swarm.contracts.v23 import SchedulerEpochLease
from swarm.scheduling.epoch import (
    EpochHeldError,
    SchedulerEpochService,
    StaleSchedulerEpochError,
)


@dataclass(frozen=True)
class TickResult:
    ran: bool
    epoch: int | None
    reason: str
    value: Any = None


class SingletonTicker:
    def __init__(self, epochs: SchedulerEpochService, *, holder_id: str) -> None:
        self.epochs = epochs
        self.holder_id = holder_id

    def run_once(self, tick: Callable[[SchedulerEpochLease], Any]) -> TickResult:
        try:
            lease = self.epochs.acquire(self.holder_id)
        except EpochHeldError:
            return TickResult(ran=False, epoch=None, reason="epoch_held_by_other")
        try:
            lease = self.epochs.renew(lease)
        except StaleSchedulerEpochError:
            return TickResult(ran=False, epoch=lease.epoch, reason="fenced_before_tick")
        value = tick(lease)
        try:
            self.epochs.require_current(epoch=lease.epoch, holder_id=self.holder_id)
        except StaleSchedulerEpochError:
            return TickResult(ran=True, epoch=lease.epoch, reason="fenced_after_tick", value=value)
        return TickResult(ran=True, epoch=lease.epoch, reason="ok", value=value)
