# SW-W3-S2 — ProductStore durability wiring: E03 write-through, E04 holds/lessons restore, E06 singleton ticker

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W3-S2` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v20-w3-s2-durable-wiring` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 3 |
| Depends on | SW-W1-S4, SW-W1-S9, SW-W1-S10 |
| Handoff file | `docs/v2.3/sessions/SW-W3-S2.md` |
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
git checkout -b cursor/v20-w3-s2-durable-wiring origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W1-S4, SW-W1-S9, SW-W1-S10. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/singleton.py && echo "OK src/swarm/scheduling/singleton.py" || echo "MISSING src/swarm/scheduling/singleton.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/pursuit/pg_mirror.py && echo "OK src/swarm/pursuit/pg_mirror.py" || echo "MISSING src/swarm/pursuit/pg_mirror.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/pursuit/durable_accounting.py && echo "OK src/swarm/pursuit/durable_accounting.py" || echo "MISSING src/swarm/pursuit/durable_accounting.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/api/store.py` — modify
- `src/swarm/pursuit/loop.py` — modify
- `tests/product/test_v20_durable_wiring.py` — create
- `tests/integration/db/test_v20_durable_wiring_sql.py` — create
- `docs/v2.3/sessions/SW-W3-S2.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Wire the Wave-1 durability building blocks into the production path, `ProductStore.pursuit_engine()`, and give pursuit a site-wide singleton tick.
- **V20-E03:** `DurablePursuitStateStore(root, mirror=PursuitPgMirror(factory))` writes and reads PostgreSQL first (SW-W1-S9).
- **V20-E04:** `PursuitEngine(hold_store=SqlHoldStore(factory))` restores every goal ledger's holds through `bind_durable_ledger`, and `PursuitLessonStore(persistence=SqlLessonPersistence(factory))` restores lessons (SW-W1-S10).
- **V20-E06:**
  - `PursuitEngine.tick_all_due()` ticks every ACTIVE/WAITING goal that is due, in goal-id order.
  - `PursuitEngine.singleton_tick(ticker)` runs it only while holding the epoch (SW-W1-S4 `SingletonTicker`).
  - `ProductStore.run_pursuit_tick()` is the production entry point. It uses the epoch row `site_id="pursuit-ticker"`, separate from the scheduler's `local` row.

**Gating** (unchanged default behaviour): PostgreSQL is used only when `SWARM_V23_DURABLE=1` **and** `db_reachable is True`. Otherwise `pg_session_factory()` returns `None`, and file-backed state under `var/` stays authoritative exactly as today. This is the same flag SW-W3-S1 uses in `routes_v23.v23_session_factory`.

The change was compiled and run against `dev @ 8e1c0fde` plus SW-W1-S4, SW-W1-S9 and SW-W1-S10:
- `tests/product/test_v20_durable_wiring.py`: 6 passed.
- The integration test: 1 passed.
- `tests/product tests/pursuit tests/api`: 95 passed.
- ruff and mypy: clean.

### Step 1 — apply the source patch (exact)
Save the block below as `/tmp/SW-W3-S2.patch`, **byte for byte** (keep the leading spaces on context lines). Then run:
```bash
git apply --check /tmp/SW-W3-S2.patch && git apply /tmp/SW-W3-S2.patch
git diff --stat   # expect: src/swarm/api/store.py and src/swarm/pursuit/loop.py only
```
```diff
diff --git a/src/swarm/api/store.py b/src/swarm/api/store.py
index 6434ffca..02b87980 100644
--- a/src/swarm/api/store.py
+++ b/src/swarm/api/store.py
@@ -83,6 +83,8 @@ class ProductStore:
     _mission_store: MissionStore | None = field(default=None, repr=False)
     _goal_store: Any = field(default=None, repr=False)
     _pursuit_engine: Any = field(default=None, repr=False)
+    _pg_factory: Any = field(default=None, repr=False)
+    _pursuit_ticker: Any = field(default=None, repr=False)
     _durable_bootstrapped: bool = field(default=False, repr=False)
 
     def bootstrap_durable(self) -> None:
@@ -162,15 +164,67 @@ class ProductStore:
                 executor: Any = RecordingExecutor(default_success=True)
             else:
                 executor = NativeMissionDispatchExecutor(self)
+            factory = self.pg_session_factory()
+            mirror: Any = None
+            lessons: Any = None
+            hold_store: Any = None
+            if factory is not None:
+                from swarm.pursuit.durable_accounting import SqlHoldStore, SqlLessonPersistence
+                from swarm.pursuit.learning import PursuitLessonStore
+                from swarm.pursuit.pg_mirror import PursuitPgMirror
+
+                mirror = PursuitPgMirror(factory)
+                lessons = PursuitLessonStore(persistence=SqlLessonPersistence(factory))
+                hold_store = SqlHoldStore(factory)
             self._pursuit_engine = PursuitEngine(
                 self.goal_store(),
                 executor=executor,
+                lessons=lessons,
                 scheduler=PursuitScheduler(clock=time.time),
                 clock=time.time,
-                state_store=DurablePursuitStateStore(root),
+                state_store=DurablePursuitStateStore(root, mirror=mirror),
+                hold_store=hold_store,
             )
         return self._pursuit_engine
 
+    def pg_session_factory(self) -> Any:
+        """PostgreSQL session factory for durable pursuit state, or ``None``.
+
+        Only when ``SWARM_V23_DURABLE=1`` and the database was probed reachable;
+        otherwise file-backed state under ``var/`` stays authoritative, as before.
+        """
+        if self._pg_factory is None and self.db_reachable is True:
+            import os
+
+            if os.environ.get("SWARM_V23_DURABLE", "") == "1":
+                from swarm.db.engine import create_db_engine, make_session_factory
+
+                self._pg_factory = make_session_factory(create_db_engine())
+        return self._pg_factory
+
+    def pursuit_ticker(self) -> Any:
+        """Site-wide singleton ticker; the epoch row ``pursuit-ticker`` fences other processes."""
+        if self._pursuit_ticker is None:
+            from swarm.contracts.common import new_id
+            from swarm.scheduling.epoch import (
+                InMemorySchedulerEpochService,
+                SqlSchedulerEpochService,
+            )
+            from swarm.scheduling.singleton import SingletonTicker
+
+            factory = self.pg_session_factory()
+            epochs: Any = (
+                SqlSchedulerEpochService(factory, site_id="pursuit-ticker")
+                if factory is not None
+                else InMemorySchedulerEpochService(site_id="pursuit-ticker")
+            )
+            self._pursuit_ticker = SingletonTicker(epochs, holder_id=new_id("pursuit_"))
+        return self._pursuit_ticker
+
+    def run_pursuit_tick(self) -> Any:
+        """Tick all due goals once, only if this process holds the pursuit epoch."""
+        return self.pursuit_engine().singleton_tick(self.pursuit_ticker())
+
     def mission_store(self) -> MissionStore:
         """Durable mission identity shared by API / CLI / console reopen paths."""
         if self._mission_store is None:
diff --git a/src/swarm/pursuit/loop.py b/src/swarm/pursuit/loop.py
index 40a5fe1e..75abc59c 100644
--- a/src/swarm/pursuit/loop.py
+++ b/src/swarm/pursuit/loop.py
@@ -4,11 +4,12 @@ from __future__ import annotations
 
 from collections.abc import Callable
 from pathlib import Path
-from typing import Any, Protocol
+from typing import TYPE_CHECKING, Any, Protocol
 
 from swarm.contracts.common import new_id
 from swarm.goals.models import Goal, GoalError, GoalKind, GoalStatus, GoalStore
 from swarm.pursuit.accounting import AccountingError, GoalResourceLedger
+from swarm.pursuit.durable_accounting import HoldStore, bind_durable_ledger
 from swarm.pursuit.frontier import assess_gap, build_frontier, choose_contribution
 from swarm.pursuit.learning import PursuitLessonStore
 from swarm.pursuit.models import (
@@ -29,6 +30,9 @@ from swarm.pursuit.verification import (
     verify_execution_outcome,
 )
 
+if TYPE_CHECKING:
+    from swarm.scheduling.singleton import SingletonTicker, TickResult
+
 
 class MissionExecutor(Protocol):
     def execute(self, proposal: MissionProposalDraft) -> ExecutionOutcome: ...
@@ -115,8 +119,10 @@ class PursuitEngine:
         ledgers: dict[str, GoalResourceLedger] | None = None,
         state_store: DurablePursuitStateStore | None = None,
         state_root: Path | None = None,
+        hold_store: HoldStore | None = None,
     ) -> None:
         self.goals = goals
+        self.hold_store = hold_store
         if executor is None:
             # R20-01 defense in depth: never default to successful RecordingExecutor.
             from swarm.pursuit.native_dispatch import BlockedMissingImplementationExecutor
@@ -152,9 +158,28 @@ class PursuitEngine:
         ledger = self._ledgers.get(goal_id)
         if ledger is None:
             ledger = GoalResourceLedger.from_envelope(goal_id, goal.resource_envelope)
+            if self.hold_store is not None:
+                bind_durable_ledger(ledger, self.hold_store)
             self._ledgers[goal_id] = ledger
         return ledger
 
+    def tick_all_due(self) -> list[CycleRecord]:
+        """Tick every active/waiting goal whose schedule is due, in goal-id order."""
+        records: list[CycleRecord] = []
+        for goal_id in sorted(self.goals.goals):
+            goal = self.goals.goals[goal_id]
+            if goal.status not in {GoalStatus.ACTIVE, GoalStatus.WAITING}:
+                continue
+            if goal_id not in self._history:
+                self.observe(goal_id)
+            if self.scheduler.is_due(goal_id):
+                records.append(self.tick(goal_id))
+        return records
+
+    def singleton_tick(self, ticker: SingletonTicker) -> TickResult:
+        """Run ``tick_all_due`` only while holding the site-wide pursuit epoch."""
+        return ticker.run_once(lambda _lease: self.tick_all_due())
+
     def _hydrate_all(self) -> None:
         """Load on-disk pursuit snapshots for goals already known to GoalStore."""
         for goal in list(self.goals.goals.values()):
```
If `git apply --check` fails, `store.py` or `loop.py` moved on the integration branch. Apply the same hunks by hand; each hunk is small:
- **`loop.py`:**
  - `TYPE_CHECKING` import;
  - `from swarm.pursuit.durable_accounting import HoldStore, bind_durable_ledger`;
  - the `hold_store` kwarg and `self.hold_store`;
  - `bind_durable_ledger` inside `resource_ledger`;
  - the new methods `tick_all_due` and `singleton_tick`.
- **`store.py`:**
  - two new dataclass fields, `_pg_factory` and `_pursuit_ticker`;
  - the durable block inside `pursuit_engine`;
  - the new methods `pg_session_factory`, `pursuit_ticker` and `run_pursuit_tick`.

### Step 2 — `tests/product/test_v20_durable_wiring.py` (create, exactly)
```python
"""SW-W3-S2: E03 mirror, E04 holds and E06 singleton ticker are wired into ProductStore."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.api.store import ProductStore
from swarm.goals.models import Goal, GoalStore
from swarm.pursuit import PursuitEngine, PursuitScheduler, RecordingExecutor
from swarm.pursuit.durable_accounting import InMemoryHoldStore
from swarm.scheduling.epoch import InMemorySchedulerEpochService
from swarm.scheduling.singleton import SingletonTicker


def _goals(root: Path, *outcomes: str) -> tuple[GoalStore, list[str]]:
    goals = GoalStore(root / "var" / "goals")
    ids = [
        goals.create(
            Goal(
                project_id="proj_wire",
                desired_outcome=text,
                verification_criteria=["done"],
                resource_envelope={"spend_usd_ceiling": 1.0, "allow_paid": True},
                authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
            )
        ).id
        for text in outcomes
    ]
    return goals, ids


def _engine(goals: GoalStore, root: Path, **kw: object) -> PursuitEngine:
    return PursuitEngine(
        goals,
        executor=RecordingExecutor(default_success=True),
        scheduler=PursuitScheduler(clock=lambda: 1000.0),
        state_root=root / "var" / "pursuit",
        **kw,  # type: ignore[arg-type]
    )


def test_default_store_stays_file_backed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_V23_DURABLE", raising=False)
    store = ProductStore(repo_root=tmp_path, db_reachable=True)
    engine = store.pursuit_engine()
    assert store.pg_session_factory() is None
    assert engine.hold_store is None
    assert engine.state_store.mirror is None


def test_flag_without_reachable_db_stays_file_backed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SWARM_V23_DURABLE", "1")
    store = ProductStore(repo_root=tmp_path, db_reachable=False)
    assert store.pg_session_factory() is None


def test_engine_ledgers_restore_holds_from_store(tmp_path: Path) -> None:
    goals, (gid,) = _goals(tmp_path, "hold budget")
    holds = InMemoryHoldStore()
    first = _engine(goals, tmp_path, hold_store=holds)
    hold = first.resource_ledger(gid).reserve(mission_id="msn_1", spend_usd=0.4)
    cold = _engine(goals, tmp_path, hold_store=holds)
    restored = cold.resource_ledger(gid)
    assert hold.hold_id in restored.holds
    assert restored.remaining().spend_usd == pytest.approx(0.6)


def test_tick_all_due_skips_paused_goals(tmp_path: Path) -> None:
    goals, (active, paused) = _goals(tmp_path, "active goal", "paused goal")
    goals.pause(paused, reason="test", actor="tester")
    records = _engine(goals, tmp_path).tick_all_due()
    assert [r.goal_id for r in records] == [active]


def test_only_one_ticker_runs_per_site(tmp_path: Path) -> None:
    goals, (gid,) = _goals(tmp_path, "singleton")
    epochs = InMemorySchedulerEpochService(site_id="pursuit-ticker")
    engine = _engine(goals, tmp_path)
    first = engine.singleton_tick(SingletonTicker(epochs, holder_id="proc_a"))
    second = engine.singleton_tick(SingletonTicker(epochs, holder_id="proc_b"))
    assert first.ran and first.reason == "ok" and [r.goal_id for r in first.value] == [gid]
    assert not second.ran and second.reason == "epoch_held_by_other"


def test_product_store_run_pursuit_tick(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWARM_V23_DURABLE", raising=False)
    store = ProductStore(repo_root=tmp_path, db_reachable=None)
    store.fixture_mode = True
    result = store.run_pursuit_tick()
    assert result.ran and result.reason == "ok" and result.value == []
```

### Step 3 — `tests/integration/db/test_v20_durable_wiring_sql.py` (create, exactly)
```python
"""SW-W3-S2: with SWARM_V23_DURABLE=1 ProductStore persists pursuit state in PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import text

from swarm.api.store import ProductStore
from swarm.db.engine import create_db_engine, ping
from swarm.db.models import Base
from swarm.goals.models import Goal
from swarm.pursuit.pg_mirror import PursuitPgMirror

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
TABLES = (
    "pursuit_cycles",
    "pursuit_schedules",
    "pursuit_dedupe",
    "v20_goal_usage_holds",
    "v20_pursuit_lessons",
    "v23_scheduler_epochs",
)


@pytest.fixture()
def durable_env(monkeypatch: pytest.MonkeyPatch):
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE " + ", ".join(TABLES)))
    monkeypatch.setenv("SWARM_DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("SWARM_V23_DURABLE", "1")
    yield
    eng.dispose()


def _store(root: Path) -> ProductStore:
    store = ProductStore(repo_root=root, db_reachable=True)
    store.fixture_mode = True
    return store


def test_holds_restore_and_ticker_is_singleton(durable_env, tmp_path: Path) -> None:
    first = _store(tmp_path)
    goal = first.goal_store().create(
        Goal(
            project_id="proj_pg",
            desired_outcome="durable wiring",
            verification_criteria=["done"],
            resource_envelope={"spend_usd_ceiling": 1.0, "allow_paid": True},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )
    engine = first.pursuit_engine()
    assert isinstance(engine.state_store.mirror, PursuitPgMirror)
    hold = engine.resource_ledger(goal.id).reserve(mission_id="msn_pg", spend_usd=0.25)

    second = _store(tmp_path)
    assert hold.hold_id in second.pursuit_engine().resource_ledger(goal.id).holds

    ran = first.run_pursuit_tick()
    blocked = second.run_pursuit_tick()
    assert ran.ran and ran.reason == "ok"
    assert not blocked.ran and blocked.reason == "epoch_held_by_other"
```

### Step 4 — run
```bash
git clean -fdX -- var/
uv run pytest tests/product/test_v20_durable_wiring.py -q                   # 6 passed
uv run pytest tests/integration/db/test_v20_durable_wiring_sql.py -q        # 1 passed (skips without Postgres)
uv run pytest tests/product tests/pursuit tests/api -q
```
Do **not** turn `SWARM_V23_DURABLE` on by default, and do not change `.env.example` or compose files. Enabling it in an environment is an operator decision recorded by SW-W4-S1.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w3_s2 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w3_s2
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/product tests/pursuit tests/api -q
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
git add src/swarm/api/store.py src/swarm/pursuit/loop.py tests/product/test_v20_durable_wiring.py tests/integration/db/test_v20_durable_wiring_sql.py docs/v2.3/sessions/SW-W3-S2.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.0): wire E03 mirror, E04 durable holds/lessons and E06 singleton ticker into ProductStore" -m "Session: SW-W3-S2. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v20-w3-s2-durable-wiring
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v20-w3-s2-durable-wiring --title "[SW-W3-S2] ProductStore durability wiring: E03 write-through, E04 holds/lessons restore, E06 singleton ticker" --body-file docs/v2.3/sessions/SW-W3-S2.md
git ls-remote origin refs/heads/cursor/v20-w3-s2-durable-wiring   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W3-S2.md` with exactly these headings:
```markdown
# SW-W3-S2 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W3-S2.md` then `git commit -m "WIP(SW-W3-S2): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v20-w3-s2-durable-wiring` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v20-w3-s2-durable-wiring?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W3-S2
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/api/store.py`, `src/swarm/pursuit/loop.py`, `tests/product/test_v20_durable_wiring.py`, `tests/integration/db/test_v20_durable_wiring_sql.py`, `docs/v2.3/sessions/SW-W3-S2.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: singleton ticker per site; durable flag off by default; restore after restart.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
