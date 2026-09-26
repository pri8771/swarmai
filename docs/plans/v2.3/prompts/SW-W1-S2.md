# SW-W1-S2 — Durable SchedulingStore on PostgreSQL (SqlSchedulingStore)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S2` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s2-sql-store` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | SW-W0-S2 |
| Handoff file | `docs/v2.3/sessions/SW-W1-S2.md` |
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
git checkout -b cursor/v23-w1-s2-sql-store origin/cursor/sw-v23-integration-460c
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
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/memory_store.py && echo "OK src/swarm/scheduling/memory_store.py" || echo "MISSING src/swarm/scheduling/memory_store.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:migrations/versions/a23opsplatform0001_v23_ops_platform.py && echo "OK migrations/versions/a23opsplatform0001_v23_ops_platform.py" || echo "MISSING migrations/versions/a23opsplatform0001_v23_ops_platform.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/scheduling/store.py` — create
- `tests/integration/db/test_v23_store_sql.py` — create
- `docs/v2.3/sessions/SW-W1-S2.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Make scheduler state durable: a PostgreSQL implementation of the `SchedulingStore` protocol (in `src/swarm/contracts/v23.py`) that behaves exactly like `InMemorySchedulingStore` (`src/swarm/scheduling/memory_store.py`, from SW-W0-S2). Tables `v23_project_queue_state`, `v23_mission_queue_state`, `v23_scheduler_receipts` and `v23_dispatch_intents` already exist (migration `a23opsplatform0001`).

**Versioning rule (must match memory store):** `expected_version=None` inserts (stored version 1) and raises `StaleVersionError` if the key exists. Otherwise the stored version must equal `expected_version`, and the new stored version is `expected_version + 1`. Updates lock the row (`SELECT … FOR UPDATE`) before comparing. DB unique-constraint violations become `StaleVersionError`.

The code below was compiled and run against Postgres 16 on `dev + SW-W0-S2` (9 passed, including a 4-thread race with exactly one winner). Paste it **exactly**.

### Step 1 — `src/swarm/scheduling/store.py` (create, exactly)
```python
"""PostgreSQL SchedulingStore — same semantics as InMemorySchedulingStore.

Each call is its own transaction (``session_scope``). Updates lock the row with
``SELECT … FOR UPDATE`` and compare ``version`` before writing, so two schedulers
racing on the same row get exactly one winner and one StaleVersionError.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentState,
    MissionQueueState,
    ProjectQueueState,
    SchedulingDecisionReceipt,
    StaleVersionError,
)
from swarm.db.engine import session_scope
from swarm.db.models import (
    V23DispatchIntentRow,
    V23MissionQueueStateRow,
    V23ProjectQueueStateRow,
    V23SchedulerReceiptRow,
)


def _dump(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")  # type: ignore[no-any-return]


class SqlSchedulingStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    # -- projects -----------------------------------------------------------
    def get_project(self, project_id: str) -> ProjectQueueState | None:
        with session_scope(self._factory) as s:
            row = s.get(V23ProjectQueueStateRow, project_id)
            return ProjectQueueState.model_validate(row.payload) if row else None

    def list_projects(self) -> list[ProjectQueueState]:
        with session_scope(self._factory) as s:
            rows = s.scalars(
                select(V23ProjectQueueStateRow).order_by(V23ProjectQueueStateRow.project_id)
            )
            return [ProjectQueueState.model_validate(r.payload) for r in rows]

    def put_project(
        self, state: ProjectQueueState, *, expected_version: int | None
    ) -> ProjectQueueState:
        with session_scope(self._factory) as s:
            row = s.scalar(
                select(V23ProjectQueueStateRow)
                .where(V23ProjectQueueStateRow.project_id == state.project_id)
                .with_for_update()
            )
            current = row.version if row else None
            new_version = _next_version(current, expected_version, state.project_id)
            stored = state.model_copy(update={"version": new_version})
            if row is None:
                s.add(
                    V23ProjectQueueStateRow(
                        project_id=stored.project_id,
                        tenant_id=stored.tenant_id,
                        version=new_version,
                        payload=_dump(stored),
                    )
                )
            else:
                row.tenant_id = stored.tenant_id
                row.version = new_version
                row.payload = _dump(stored)
            _flush_or_stale(s, state.project_id)
            return stored

    # -- missions -----------------------------------------------------------
    def get_mission(self, mission_id: str) -> MissionQueueState | None:
        with session_scope(self._factory) as s:
            row = s.get(V23MissionQueueStateRow, mission_id)
            return MissionQueueState.model_validate(row.payload) if row else None

    def list_missions(self, project_id: str | None = None) -> list[MissionQueueState]:
        with session_scope(self._factory) as s:
            stmt = select(V23MissionQueueStateRow).order_by(V23MissionQueueStateRow.mission_id)
            if project_id is not None:
                stmt = stmt.where(V23MissionQueueStateRow.project_id == project_id)
            return [MissionQueueState.model_validate(r.payload) for r in s.scalars(stmt)]

    def put_mission(
        self, state: MissionQueueState, *, expected_version: int | None
    ) -> MissionQueueState:
        with session_scope(self._factory) as s:
            row = s.scalar(
                select(V23MissionQueueStateRow)
                .where(V23MissionQueueStateRow.mission_id == state.mission_id)
                .with_for_update()
            )
            current = row.version if row else None
            new_version = _next_version(current, expected_version, state.mission_id)
            stored = state.model_copy(update={"version": new_version})
            if row is None:
                s.add(
                    V23MissionQueueStateRow(
                        mission_id=stored.mission_id,
                        project_id=stored.project_id,
                        lifecycle=stored.lifecycle.value,
                        version=new_version,
                        payload=_dump(stored),
                    )
                )
            else:
                row.project_id = stored.project_id
                row.lifecycle = stored.lifecycle.value
                row.version = new_version
                row.payload = _dump(stored)
            _flush_or_stale(s, state.mission_id)
            return stored

    # -- receipts -----------------------------------------------------------
    def next_sequence(self) -> int:
        """Max stored sequence + 1. Uniqueness is enforced by the DB constraint;
        callers hold the scheduler epoch, so collisions mean a fencing bug."""
        with session_scope(self._factory) as s:
            current = s.scalar(select(func.coalesce(func.max(V23SchedulerReceiptRow.sequence), 0)))
            return int(current or 0) + 1

    def append_receipt(self, receipt: SchedulingDecisionReceipt) -> None:
        with session_scope(self._factory) as s:
            s.add(
                V23SchedulerReceiptRow(
                    receipt_id=receipt.receipt_id,
                    sequence=receipt.sequence,
                    project_id=receipt.project_id,
                    decision=receipt.decision.value,
                    reason_code=receipt.reason_code.value,
                    digest=receipt.digest(),
                    payload=_dump(receipt),
                )
            )
            _flush_or_stale(s, f"receipt_sequence:{receipt.sequence}")

    def list_receipts(
        self, *, project_id: str | None = None, limit: int = 100
    ) -> list[SchedulingDecisionReceipt]:
        with session_scope(self._factory) as s:
            stmt = select(V23SchedulerReceiptRow).order_by(V23SchedulerReceiptRow.sequence.desc())
            if project_id is not None:
                stmt = stmt.where(V23SchedulerReceiptRow.project_id == project_id)
            rows = list(s.scalars(stmt.limit(limit)))
            rows.reverse()
            return [SchedulingDecisionReceipt.model_validate(r.payload) for r in rows]

    # -- intents ------------------------------------------------------------
    def get_intent(self, intent_id: str) -> DispatchIntent | None:
        with session_scope(self._factory) as s:
            row = s.get(V23DispatchIntentRow, intent_id)
            return DispatchIntent.model_validate(row.payload) if row else None

    def get_intent_by_attempt(self, attempt_id: str) -> DispatchIntent | None:
        with session_scope(self._factory) as s:
            row = s.scalar(
                select(V23DispatchIntentRow).where(V23DispatchIntentRow.attempt_id == attempt_id)
            )
            return DispatchIntent.model_validate(row.payload) if row else None

    def put_intent(
        self, intent: DispatchIntent, *, expected_version: int | None
    ) -> DispatchIntent:
        with session_scope(self._factory) as s:
            row = s.scalar(
                select(V23DispatchIntentRow)
                .where(V23DispatchIntentRow.intent_id == intent.intent_id)
                .with_for_update()
            )
            current = row.version if row else None
            new_version = _next_version(current, expected_version, intent.intent_id)
            stored = intent.model_copy(update={"version": new_version})
            if row is None:
                s.add(
                    V23DispatchIntentRow(
                        intent_id=stored.intent_id,
                        attempt_id=stored.attempt_id,
                        project_id=stored.project_id,
                        state=stored.state.value,
                        expires_at=stored.expires_at,
                        version=new_version,
                        payload=_dump(stored),
                    )
                )
            else:
                row.state = stored.state.value
                row.expires_at = stored.expires_at
                row.version = new_version
                row.payload = _dump(stored)
            _flush_or_stale(s, f"attempt:{intent.attempt_id}")
            return stored

    def list_intents(
        self, *, states: frozenset[DispatchIntentState] | None = None
    ) -> list[DispatchIntent]:
        with session_scope(self._factory) as s:
            stmt = select(V23DispatchIntentRow).order_by(V23DispatchIntentRow.intent_id)
            if states is not None:
                stmt = stmt.where(V23DispatchIntentRow.state.in_([x.value for x in states]))
            return [DispatchIntent.model_validate(r.payload) for r in s.scalars(stmt)]


def _next_version(current: int | None, expected: int | None, key: str) -> int:
    if expected is None:
        if current is not None:
            raise StaleVersionError(f"already_exists:{key}")
        return 1
    if current != expected:
        raise StaleVersionError(f"stale_version:{key}:expected={expected}:actual={current}")
    return expected + 1


def _flush_or_stale(session: Session, key: str) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        raise StaleVersionError(f"conflict:{key}") from exc
```

### Step 2 — `tests/integration/db/test_v23_store_sql.py` (create, exactly)
Each behavior test runs against **both** stores (parametrized), which proves they are equivalent.
```python
"""SW-W1-S2: SqlSchedulingStore matches InMemorySchedulingStore semantics (PostgreSQL)."""

from __future__ import annotations

import os
import threading
from datetime import timedelta

import pytest
from sqlalchemy import text

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentState,
    MissionQueueState,
    ProjectQueueState,
    ReasonCode,
    SchedulerDecision,
    SchedulingDecisionReceipt,
    StaleVersionError,
)
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.scheduling.memory_store import InMemorySchedulingStore
from swarm.scheduling.store import SqlSchedulingStore

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
V23_TABLES = (
    "v23_project_queue_state",
    "v23_mission_queue_state",
    "v23_scheduler_receipts",
    "v23_dispatch_intents",
)


@pytest.fixture(scope="module")
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    yield make_session_factory(eng)
    eng.dispose()


@pytest.fixture(autouse=True)
def _clean(factory):
    with factory() as s:
        s.execute(text("TRUNCATE " + ", ".join(V23_TABLES)))
        s.commit()
    yield


@pytest.fixture(params=["memory", "sql"])
def store(request, factory):
    if request.param == "memory":
        return InMemorySchedulingStore()
    return SqlSchedulingStore(factory)


def test_project_versioning(store) -> None:
    first = store.put_project(ProjectQueueState(project_id="proj_a"), expected_version=None)
    assert first.version == 1
    with pytest.raises(StaleVersionError):
        store.put_project(ProjectQueueState(project_id="proj_a"), expected_version=None)
    second = store.put_project(first.model_copy(update={"credit": 4.0}), expected_version=1)
    assert second.version == 2
    with pytest.raises(StaleVersionError):
        store.put_project(first, expected_version=1)
    got = store.get_project("proj_a")
    assert got is not None and got.credit == 4.0 and got.version == 2


def test_missions_filtered_by_project(store) -> None:
    store.put_mission(MissionQueueState(mission_id="m1", project_id="p1"), expected_version=None)
    store.put_mission(MissionQueueState(mission_id="m2", project_id="p2"), expected_version=None)
    assert [m.mission_id for m in store.list_missions("p2")] == ["m2"]


def test_receipts_roundtrip_and_digest(store) -> None:
    seq = store.next_sequence()
    receipt = SchedulingDecisionReceipt(
        sequence=seq,
        decision=SchedulerDecision.ADMIT,
        reason_code=ReasonCode.ADMITTED,
        project_id="proj_a",
        scores={"proj_a": 1.5},
    )
    store.append_receipt(receipt)
    with pytest.raises(StaleVersionError):
        store.append_receipt(receipt.model_copy(update={"receipt_id": "sdr_dup"}))
    [back] = store.list_receipts(project_id="proj_a")
    assert back.digest() == receipt.digest()


def test_intent_unique_per_attempt(store) -> None:
    intent = DispatchIntent(
        attempt_id="att_1",
        project_id="proj_a",
        mission_id="m1",
        task_id="t1",
        expires_at=utc_now() + timedelta(seconds=30),
    )
    stored = store.put_intent(intent, expected_version=None)
    with pytest.raises(StaleVersionError):
        store.put_intent(intent.model_copy(update={"intent_id": "din_2"}), expected_version=None)
    moved = store.put_intent(
        stored.model_copy(update={"state": DispatchIntentState.RESERVED}), expected_version=1
    )
    assert moved.version == 2
    assert store.get_intent_by_attempt("att_1") == moved
    assert [i.intent_id for i in store.list_intents(states=frozenset({DispatchIntentState.RESERVED}))] == [
        intent.intent_id
    ]


def test_concurrent_update_has_one_winner(factory) -> None:
    store = SqlSchedulingStore(factory)
    base = store.put_project(ProjectQueueState(project_id="proj_race"), expected_version=None)
    results: list[str] = []

    def writer(credit: float) -> None:
        try:
            store.put_project(base.model_copy(update={"credit": credit}), expected_version=1)
            results.append("ok")
        except StaleVersionError:
            results.append("stale")

    threads = [threading.Thread(target=writer, args=(float(i),)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["ok", "stale", "stale", "stale"]
```

### Step 3 — run
```bash
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s2 OWNER swarm;" || true
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s2 uv run pytest tests/integration/db/test_v23_store_sql.py -q -m integration   # 9 passed
```
This session has no offline test, so the integration run is **required**. If Postgres cannot run at all, STOP (S3, section 10); PRs stay draft.

### Section-5 acceptance
- [ ] 9 integration tests pass (4 behaviors × 2 stores + 1 race test).
- [ ] `SqlSchedulingStore` satisfies the `SchedulingStore` protocol (mypy clean).
- [ ] No change to `models.py` or migrations.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s2 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s2
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
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
git add src/swarm/scheduling/store.py tests/integration/db/test_v23_store_sql.py docs/v2.3/sessions/SW-W1-S2.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): PostgreSQL SchedulingStore with optimistic versions and row locks" -m "Session: SW-W1-S2. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s2-sql-store
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s2-sql-store --title "[SW-W1-S2] Durable SchedulingStore on PostgreSQL (SqlSchedulingStore)" --body-file docs/v2.3/sessions/SW-W1-S2.md
git ls-remote origin refs/heads/cursor/v23-w1-s2-sql-store   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S2.md` with exactly these headings:
```markdown
# SW-W1-S2 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S2.md` then `git commit -m "WIP(SW-W1-S2): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s2-sql-store` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s2-sql-store?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S2
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/scheduling/store.py`, `tests/integration/db/test_v23_store_sql.py`, `docs/v2.3/sessions/SW-W1-S2.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: compare-and-set on version; no lost update under concurrency; tenant filter on every query.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
