"""Scheduler epoch lease — at most one active scheduler per site (fencing token).

Every scheduler write carries the epoch it holds. A new holder can only acquire
after the previous lease expires or is released, and acquiring always increments
the epoch, so a paused/partitioned old scheduler is fenced by ``require_current``.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import SchedulerEpochLease
from swarm.db.engine import session_scope
from swarm.db.models import V23SchedulerEpochRow

Clock = Callable[[], datetime]


class EpochHeldError(RuntimeError):
    """Another holder owns an unexpired lease."""


class StaleSchedulerEpochError(RuntimeError):
    """The caller's epoch/holder is no longer current."""


class SchedulerEpochService(Protocol):
    def acquire(self, holder_id: str) -> SchedulerEpochLease: ...

    def renew(self, lease: SchedulerEpochLease) -> SchedulerEpochLease: ...

    def release(self, lease: SchedulerEpochLease) -> None: ...

    def current(self) -> SchedulerEpochLease | None: ...

    def require_current(self, *, epoch: int, holder_id: str) -> None: ...


def _valid(lease: SchedulerEpochLease | None, now: datetime) -> bool:
    return lease is not None and now < lease.expires_at


class InMemorySchedulerEpochService:
    def __init__(
        self, *, site_id: str = "local", ttl_seconds: float = 15.0, clock: Clock | None = None
    ) -> None:
        self.site_id = site_id
        self.ttl = timedelta(seconds=ttl_seconds)
        self._clock: Clock = clock or utc_now
        self._lock = threading.RLock()
        self._lease: SchedulerEpochLease | None = None

    def acquire(self, holder_id: str) -> SchedulerEpochLease:
        with self._lock:
            now = self._clock()
            cur = self._lease
            if _valid(cur, now) and cur is not None:
                if cur.holder_id == holder_id:
                    return cur
                raise EpochHeldError(f"epoch_held:{cur.holder_id}:{cur.epoch}")
            epoch = (cur.epoch if cur else 0) + 1
            self._lease = SchedulerEpochLease(
                site_id=self.site_id,
                epoch=epoch,
                holder_id=holder_id,
                acquired_at=now,
                expires_at=now + self.ttl,
                version=(cur.version if cur else 0) + 1,
            )
            return self._lease

    def renew(self, lease: SchedulerEpochLease) -> SchedulerEpochLease:
        with self._lock:
            self.require_current(epoch=lease.epoch, holder_id=lease.holder_id)
            assert self._lease is not None
            self._lease = self._lease.model_copy(
                update={"expires_at": self._clock() + self.ttl, "version": self._lease.version + 1}
            )
            return self._lease

    def release(self, lease: SchedulerEpochLease) -> None:
        with self._lock:
            cur = self._lease
            if cur and cur.epoch == lease.epoch and cur.holder_id == lease.holder_id:
                self._lease = cur.model_copy(
                    update={"expires_at": self._clock(), "version": cur.version + 1}
                )

    def current(self) -> SchedulerEpochLease | None:
        with self._lock:
            return self._lease if _valid(self._lease, self._clock()) else None

    def require_current(self, *, epoch: int, holder_id: str) -> None:
        with self._lock:
            cur = self._lease
            if not _valid(cur, self._clock()) or cur is None:
                raise StaleSchedulerEpochError(f"no_current_epoch:{epoch}")
            if cur.epoch != epoch or cur.holder_id != holder_id:
                raise StaleSchedulerEpochError(
                    f"stale_scheduler_epoch:held={cur.epoch}:{cur.holder_id}:given={epoch}"
                )


class SqlSchedulerEpochService:
    """Same semantics, stored in ``v23_scheduler_epochs`` with row locks."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        site_id: str = "local",
        ttl_seconds: float = 15.0,
        clock: Clock | None = None,
    ) -> None:
        self._factory = session_factory
        self.site_id = site_id
        self.ttl = timedelta(seconds=ttl_seconds)
        self._clock: Clock = clock or utc_now

    def _lock_row(self, s: Session) -> V23SchedulerEpochRow | None:
        return s.scalar(
            select(V23SchedulerEpochRow)
            .where(V23SchedulerEpochRow.site_id == self.site_id)
            .with_for_update()
        )

    @staticmethod
    def _lease(row: V23SchedulerEpochRow) -> SchedulerEpochLease:
        return SchedulerEpochLease(
            site_id=row.site_id,
            epoch=row.epoch,
            holder_id=row.holder_id,
            expires_at=row.expires_at,
            version=row.version,
        )

    def acquire(self, holder_id: str) -> SchedulerEpochLease:
        now = self._clock()
        with session_scope(self._factory) as s:
            row = self._lock_row(s)
            if row is not None and now < row.expires_at:
                if row.holder_id == holder_id:
                    return self._lease(row)
                raise EpochHeldError(f"epoch_held:{row.holder_id}:{row.epoch}")
            if row is None:
                row = V23SchedulerEpochRow(
                    site_id=self.site_id,
                    epoch=1,
                    holder_id=holder_id,
                    expires_at=now + self.ttl,
                    version=1,
                )
                s.add(row)
            else:
                row.epoch = row.epoch + 1
                row.holder_id = holder_id
                row.expires_at = now + self.ttl
                row.version = row.version + 1
            s.flush()
            return self._lease(row)

    def renew(self, lease: SchedulerEpochLease) -> SchedulerEpochLease:
        now = self._clock()
        with session_scope(self._factory) as s:
            row = self._lock_row(s)
            self._check(row, now, epoch=lease.epoch, holder_id=lease.holder_id)
            assert row is not None
            row.expires_at = now + self.ttl
            row.version = row.version + 1
            s.flush()
            return self._lease(row)

    def release(self, lease: SchedulerEpochLease) -> None:
        with session_scope(self._factory) as s:
            row = self._lock_row(s)
            if row and row.epoch == lease.epoch and row.holder_id == lease.holder_id:
                row.expires_at = self._clock()
                row.version = row.version + 1

    def current(self) -> SchedulerEpochLease | None:
        with session_scope(self._factory) as s:
            row = s.get(V23SchedulerEpochRow, self.site_id)
            if row is None or self._clock() >= row.expires_at:
                return None
            return self._lease(row)

    def require_current(self, *, epoch: int, holder_id: str) -> None:
        with session_scope(self._factory) as s:
            row = s.get(V23SchedulerEpochRow, self.site_id)
            self._check(row, self._clock(), epoch=epoch, holder_id=holder_id)

    @staticmethod
    def _check(
        row: V23SchedulerEpochRow | None, now: datetime, *, epoch: int, holder_id: str
    ) -> None:
        if row is None or now >= row.expires_at:
            raise StaleSchedulerEpochError(f"no_current_epoch:{epoch}")
        if row.epoch != epoch or row.holder_id != holder_id:
            raise StaleSchedulerEpochError(
                f"stale_scheduler_epoch:held={row.epoch}:{row.holder_id}:given={epoch}"
            )
