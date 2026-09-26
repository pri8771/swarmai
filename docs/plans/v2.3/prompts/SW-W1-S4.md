# SW-W1-S4 — Scheduler epoch lease + singleton ticker (V20-E06 infra)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S4` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s4-scheduler-epoch` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | SW-W0-S2 |
| Handoff file | `docs/v2.3/sessions/SW-W1-S4.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v23-w1-s4-scheduler-epoch origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W0-S2. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/contracts/v23.py && echo "OK src/swarm/contracts/v23.py" || echo "MISSING src/swarm/contracts/v23.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:migrations/versions/a23opsplatform0001_v23_ops_platform.py && echo "OK migrations/versions/a23opsplatform0001_v23_ops_platform.py" || echo "MISSING migrations/versions/a23opsplatform0001_v23_ops_platform.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/scheduling/epoch.py` — create
- `src/swarm/scheduling/singleton.py` — create
- `tests/controller/test_v23_epoch.py` — create
- `tests/integration/db/test_v23_epoch_sql.py` — create
- `docs/v2.3/sessions/SW-W1-S4.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Only one scheduler (and one pursuit ticker) may act per site at a time. Implement a **scheduler epoch lease**: a fencing token stored in `v23_scheduler_epochs`. Acquiring bumps the epoch, so a stale scheduler (paused or partitioned) is rejected by `require_current`. Add `SingletonTicker`, which runs a callback only while holding the lease. SW-W2-S1 uses the lease for scheduler writes; SW-W3-S2 uses the ticker for the pursuit loop (V20-E06).

Unlike `SiteAuthorityService` (`src/swarm/recovery/authority.py`), which fences a whole *site*, this lease fences the *scheduler process* inside a site. SW-W2-S1 checks both.

The code below was compiled and run against `dev + SW-W0-S2` (4 offline passed and 1 PostgreSQL passed; ruff and mypy clean). Paste it **exactly**.

### Step 1 — `src/swarm/scheduling/epoch.py` (create, exactly)
```python
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
```

### Step 2 — `src/swarm/scheduling/singleton.py` (create, exactly)
```python
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
```

### Step 3 — tests (create, exactly)
`tests/controller/test_v23_epoch.py`:
```python
"""SW-W1-S4: scheduler epoch fencing and singleton ticker (in-memory)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from swarm.scheduling.epoch import (
    EpochHeldError,
    InMemorySchedulerEpochService,
    StaleSchedulerEpochError,
)
from swarm.scheduling.singleton import SingletonTicker


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)


def test_second_holder_blocked_until_expiry_then_epoch_increments() -> None:
    clock = Clock()
    svc = InMemorySchedulerEpochService(ttl_seconds=15, clock=clock)
    a = svc.acquire("sched_a")
    assert a.epoch == 1
    assert svc.acquire("sched_a").epoch == 1
    with pytest.raises(EpochHeldError):
        svc.acquire("sched_b")
    clock.advance(16)
    b = svc.acquire("sched_b")
    assert b.epoch == 2
    with pytest.raises(StaleSchedulerEpochError):
        svc.require_current(epoch=1, holder_id="sched_a")
    with pytest.raises(StaleSchedulerEpochError):
        svc.renew(a)


def test_renew_extends_and_release_allows_takeover() -> None:
    clock = Clock()
    svc = InMemorySchedulerEpochService(ttl_seconds=15, clock=clock)
    a = svc.acquire("sched_a")
    clock.advance(10)
    svc.renew(a)
    clock.advance(10)
    svc.require_current(epoch=1, holder_id="sched_a")
    svc.release(a)
    assert svc.current() is None
    assert svc.acquire("sched_b").epoch == 2


def test_singleton_ticker_runs_in_one_holder_only() -> None:
    clock = Clock()
    svc = InMemorySchedulerEpochService(ttl_seconds=15, clock=clock)
    calls: list[str] = []
    t1 = SingletonTicker(svc, holder_id="proc_1")
    t2 = SingletonTicker(svc, holder_id="proc_2")
    r1 = t1.run_once(lambda lease: calls.append(f"p1:{lease.epoch}"))
    r2 = t2.run_once(lambda lease: calls.append(f"p2:{lease.epoch}"))
    assert (r1.ran, r1.reason) == (True, "ok")
    assert (r2.ran, r2.reason) == (False, "epoch_held_by_other")
    assert calls == ["p1:1"]


def test_ticker_reports_fencing_during_tick() -> None:
    clock = Clock()
    svc = InMemorySchedulerEpochService(ttl_seconds=15, clock=clock)
    ticker = SingletonTicker(svc, holder_id="proc_1")

    def slow_tick(lease: object) -> str:
        clock.advance(20)
        svc.acquire("proc_2")
        return "work"

    result = ticker.run_once(slow_tick)
    assert result.ran is True
    assert result.reason == "fenced_after_tick"
```
`tests/integration/db/test_v23_epoch_sql.py`:
```python
"""SW-W1-S4: SqlSchedulerEpochService fencing across two service instances (PostgreSQL)."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.scheduling.epoch import (
    EpochHeldError,
    SqlSchedulerEpochService,
    StaleSchedulerEpochError,
)

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture()
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE v23_scheduler_epochs"))
    yield make_session_factory(eng)
    eng.dispose()


def test_two_processes_share_one_epoch_row(factory) -> None:
    clock = Clock()
    proc_a = SqlSchedulerEpochService(factory, ttl_seconds=15, clock=clock)
    proc_b = SqlSchedulerEpochService(factory, ttl_seconds=15, clock=clock)
    lease_a = proc_a.acquire("sched_a")
    assert lease_a.epoch == 1
    with pytest.raises(EpochHeldError):
        proc_b.acquire("sched_b")
    clock.now = clock.now + timedelta(seconds=16)
    lease_b = proc_b.acquire("sched_b")
    assert lease_b.epoch == 2
    with pytest.raises(StaleSchedulerEpochError):
        proc_a.require_current(epoch=1, holder_id="sched_a")
    with pytest.raises(StaleSchedulerEpochError):
        proc_a.renew(lease_a)
    proc_b.require_current(epoch=2, holder_id="sched_b")
    current = proc_a.current()
    assert current is not None and current.holder_id == "sched_b"
```

### Step 4 — run
```bash
uv run pytest tests/controller/test_v23_epoch.py -q     # 4 passed
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s4 OWNER swarm;" || true
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s4 uv run pytest tests/integration/db/test_v23_epoch_sql.py -q -m integration   # 1 passed
```

### Section-5 acceptance
- [ ] A second holder cannot acquire while the lease is valid; after expiry the epoch increments; the old holder is fenced (`StaleSchedulerEpochError`) on renew and `require_current`.
- [ ] `SingletonTicker` runs the tick in only one holder; fencing during a tick is reported as `fenced_after_tick`.
- [ ] The SQL service gives the same results across two service instances sharing one database.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s4 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s4
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/controller/test_v23_epoch.py -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/scheduling/epoch.py src/swarm/scheduling/singleton.py tests/controller/test_v23_epoch.py tests/integration/db/test_v23_epoch_sql.py docs/v2.3/sessions/SW-W1-S4.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): fenced scheduler epoch lease (memory + PostgreSQL) and singleton ticker" -m "Session: SW-W1-S4. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s4-scheduler-epoch
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s4-scheduler-epoch --title "[SW-W1-S4] Scheduler epoch lease + singleton ticker (V20-E06 infra)" --body-file docs/v2.3/sessions/SW-W1-S4.md
git ls-remote origin refs/heads/cursor/v23-w1-s4-scheduler-epoch   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S4.md` with exactly these headings:
```markdown
# SW-W1-S4 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S4.md` then `git commit -m "WIP(SW-W1-S4): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s4-scheduler-epoch` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s4-scheduler-epoch?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S4
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/scheduling/epoch.py`, `src/swarm/scheduling/singleton.py`, `tests/controller/test_v23_epoch.py`, `tests/integration/db/test_v23_epoch_sql.py`, `docs/v2.3/sessions/SW-W1-S4.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete").
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
