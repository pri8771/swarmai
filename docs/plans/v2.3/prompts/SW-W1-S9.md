# SW-W1-S9 — V20-E03 pursuit PostgreSQL write-through store

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S9` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v20-w1-s9-pursuit-writethrough` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | none |
| Handoff file | `docs/v2.3/sessions/SW-W1-S9.md` |
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
git checkout -b cursor/v20-w1-s9-pursuit-writethrough origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
This session has **no dependencies**. Go to Step 1.

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/pursuit/pg_mirror.py` — create
- `src/swarm/pursuit/state_store.py` — modify
- `tests/pursuit/test_v20_writethrough.py` — create
- `tests/integration/db/test_v20_pursuit_writethrough_sql.py` — create
- `docs/v2.3/sessions/SW-W1-S9.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Implement V20-E03, the write-through half of finding **F-05**.
- Pursuit runtime state (history, satisfied criteria, dedupe, schedule) lives only in `var/pursuit/*.json`. The PostgreSQL tables `pursuit_cycles`, `pursuit_schedules` and `pursuit_dedupe` and the repository `swarm.db.repositories.PursuitStateRepository` exist but nothing writes to them.

**This session adds:**
- `PursuitPgMirror(session_factory)`, which writes the whole snapshot into `pursuit_schedules.payload["snapshot"]`, plus queryable cycle and dedupe rows, in **one transaction per save**.
- An optional `mirror=` argument on `DurablePursuitStateStore`:
  - **DB first** on write. If the DB fails, `PursuitMirrorError` is raised and the file is not written.
  - **DB first** on read, falling back to the file only when the DB has no row (migration from file-only installs).
  - A DB read error raises; it is never silently ignored.

Without `mirror`, behaviour is identical to today. **Do not** wire this into `api/store.py`; SW-W3-S2 owns that.

Design notes:
- Cycles that already exist, matched by `cycle_id`, are skipped, so re-saving is idempotent.
- Dedupe keys longer than 64 characters are stored as their sha256 hex digest; the original key is kept in `payload["key"]`.
- `next_due_at` is `0.0` when there is no schedule.

The code below was compiled and run against `dev @ 8e1c0fde`. `tests/pursuit` gives 36 passed and the integration test gives 1 passed. Paste it **exactly**.

### Step 1 — `src/swarm/pursuit/pg_mirror.py` (create, exactly)
```python
"""V20-E03: PostgreSQL write-through for pursuit runtime snapshots.

The whole snapshot is stored in ``pursuit_schedules.payload["snapshot"]``; cycles
and dedupe keys are also written to ``pursuit_cycles`` / ``pursuit_dedupe`` so
they can be queried. One transaction per save. Any database error becomes
``PursuitMirrorError`` so callers fail closed instead of silently diverging.
"""

from __future__ import annotations

import hashlib
from typing import Any, Protocol

from sqlalchemy.orm import Session, sessionmaker

MAX_KEY_LEN = 64


class PursuitMirrorError(RuntimeError):
    pass


class PursuitMirror(Protocol):
    def write_snapshot(self, goal_id: str, snapshot: dict[str, Any]) -> None: ...

    def load_snapshot(self, goal_id: str) -> dict[str, Any] | None: ...


def dedupe_db_key(key: str) -> str:
    """Keys longer than the column width are replaced by their sha256 hex (64 chars)."""
    if len(key) <= MAX_KEY_LEN:
        return key
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


class PursuitPgMirror:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def write_snapshot(self, goal_id: str, snapshot: dict[str, Any]) -> None:
        from swarm.db.engine import session_scope
        from swarm.db.models import PursuitCycleRow
        from swarm.db.repositories import PursuitStateRepository

        schedule = snapshot.get("schedule") or {}
        try:
            with session_scope(self._factory) as s:
                repo = PursuitStateRepository(s)
                repo.upsert_schedule(
                    goal_id=goal_id,
                    next_due_at=float(schedule.get("next_due_at") or 0.0),
                    backoff_seconds=float(schedule.get("backoff_seconds") or 0.0),
                    consecutive_failures=int(schedule.get("consecutive_failures") or 0),
                    consecutive_no_progress=int(schedule.get("consecutive_no_progress") or 0),
                    last_cycle_at=schedule.get("last_cycle_at"),
                    wait_reason=schedule.get("wait_reason"),
                    payload={"snapshot": snapshot},
                )
                for cycle in snapshot.get("history") or []:
                    cycle_id = str(cycle["cycle_id"])
                    if s.get(PursuitCycleRow, cycle_id) is not None:
                        continue
                    repo.append_cycle(
                        cycle_id=cycle_id,
                        goal_id=goal_id,
                        phase=str(cycle["phase"]),
                        decided_kind=cycle.get("decided_kind"),
                        payload=cycle,
                    )
                for key, proposal_id in sorted((snapshot.get("dedupe") or {}).items()):
                    repo.put_dedupe(
                        goal_id=goal_id,
                        dedupe_key=dedupe_db_key(str(key)),
                        proposal_id=str(proposal_id),
                        payload={"key": str(key)},
                    )
        except PursuitMirrorError:
            raise
        except Exception as exc:  # noqa: BLE001 - any DB failure must fail closed
            raise PursuitMirrorError(f"pursuit_mirror_write_failed:{type(exc).__name__}") from exc

    def load_snapshot(self, goal_id: str) -> dict[str, Any] | None:
        from swarm.db.engine import session_scope
        from swarm.db.models import PursuitScheduleRow

        try:
            with session_scope(self._factory) as s:
                row = s.get(PursuitScheduleRow, goal_id)
                payload = dict(row.payload or {}) if row is not None else None
        except Exception as exc:  # noqa: BLE001
            raise PursuitMirrorError(f"pursuit_mirror_read_failed:{type(exc).__name__}") from exc
        if payload is None:
            return None
        snap = payload.get("snapshot")
        return dict(snap) if isinstance(snap, dict) else None
```

### Step 2 — `src/swarm/pursuit/state_store.py` (replace the whole file, exactly)
```python
"""Durable pursuit runtime state — survives ProductStore / process reopen.

Closes R20-04: criteria progress, cycle history, dedupe, commitments, active
missions, failed approaches and schedules must not live only in process memory.
File-backed under ``var/pursuit/`` for local volume durability. When a
``mirror`` (V20-E03 PostgreSQL write-through) is given, the database is written
first and read first; mirror failures raise ``PursuitMirrorError`` (fail closed).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from swarm.pursuit.models import CycleRecord, ScheduleState
from swarm.pursuit.pg_mirror import PursuitMirror


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str)
            handle.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


class DurablePursuitStateStore:
    """Per-goal pursuit runtime snapshot under ``root/<goal_id>.json``."""

    schema_version = "2.0-pursuit-state"

    def __init__(self, root: Path, *, mirror: PursuitMirror | None = None) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.mirror = mirror

    def _path(self, goal_id: str) -> Path:
        safe = goal_id.replace("/", "_").replace("..", "_")
        return self.root / f"{safe}.json"

    def _load_file(self, goal_id: str) -> dict[str, Any] | None:
        path = self._path(goal_id)
        if not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return None
        if not isinstance(raw, dict):
            return None
        return raw

    def load(self, goal_id: str) -> dict[str, Any] | None:
        if self.mirror is not None:
            snap = self.mirror.load_snapshot(goal_id)
            if snap is not None:
                return snap
        return self._load_file(goal_id)

    def save(
        self,
        goal_id: str,
        *,
        satisfied: set[str],
        history: list[CycleRecord],
        dedupe: dict[str, str],
        failed_approaches: set[str],
        active_missions: set[str],
        commitments: list[str],
        schedule: ScheduleState | None,
    ) -> None:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "goal_id": goal_id,
            "satisfied_criteria": sorted(satisfied),
            "history": [c.model_dump(mode="json") for c in history],
            "dedupe": dict(dedupe),
            "failed_approaches": sorted(failed_approaches),
            "active_missions": sorted(active_missions),
            "commitments": list(commitments),
            "schedule": schedule.model_dump(mode="json") if schedule else None,
        }
        if self.mirror is not None:
            self.mirror.write_snapshot(goal_id, payload)
        _atomic_write(self._path(goal_id), payload)

    def parse_history(self, raw: dict[str, Any]) -> list[CycleRecord]:
        out: list[CycleRecord] = []
        for row in raw.get("history") or []:
            try:
                out.append(CycleRecord.model_validate(row))
            except (TypeError, ValueError):
                continue
        return out

    def parse_schedule(self, raw: dict[str, Any]) -> ScheduleState | None:
        row = raw.get("schedule")
        if not row:
            return None
        try:
            return ScheduleState.model_validate(row)
        except (TypeError, ValueError):
            return None
```

### Step 3 — `tests/pursuit/test_v20_writethrough.py` (create, exactly)
```python
"""SW-W1-S9 / V20-E03: DB-first write-through and fail-closed mirror (offline fakes)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from swarm.goals.models import Goal, GoalStore
from swarm.pursuit import PursuitEngine, PursuitScheduler, RecordingExecutor
from swarm.pursuit.pg_mirror import PursuitMirrorError, dedupe_db_key
from swarm.pursuit.state_store import DurablePursuitStateStore


class FakeMirror:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.fail = False

    def write_snapshot(self, goal_id: str, snapshot: dict[str, Any]) -> None:
        if self.fail:
            raise PursuitMirrorError("pursuit_mirror_write_failed:Fake")
        self.rows[goal_id] = snapshot

    def load_snapshot(self, goal_id: str) -> dict[str, Any] | None:
        if self.fail:
            raise PursuitMirrorError("pursuit_mirror_read_failed:Fake")
        return self.rows.get(goal_id)


def _goal(root: Path) -> tuple[GoalStore, Goal]:
    goals = GoalStore(root / "goals")
    goal = goals.create(
        Goal(
            project_id="proj_wt",
            desired_outcome="write through",
            verification_criteria=["one", "two"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )
    return goals, goal


def _engine(goals: GoalStore, store: DurablePursuitStateStore) -> PursuitEngine:
    return PursuitEngine(
        goals,
        executor=RecordingExecutor(default_success=True),
        scheduler=PursuitScheduler(clock=lambda: 50.0),
        state_store=store,
    )


def test_db_snapshot_is_authoritative_on_reopen(tmp_path: Path) -> None:
    goals, goal = _goal(tmp_path)
    mirror = FakeMirror()
    engine = _engine(goals, DurablePursuitStateStore(tmp_path / "ps", mirror=mirror))
    engine.tick(goal.id, force=True)
    assert goal.id in mirror.rows
    # The local file volume is lost; the DB snapshot alone restores state.
    cold = _engine(goals, DurablePursuitStateStore(tmp_path / "ps_new_volume", mirror=mirror))
    assert len(cold.history(goal.id)) == 1
    assert cold.satisfied_criteria(goal.id) == engine.satisfied_criteria(goal.id)


def test_mirror_write_failure_fails_closed_and_file_not_written(tmp_path: Path) -> None:
    mirror = FakeMirror()
    store = DurablePursuitStateStore(tmp_path / "ps", mirror=mirror)
    mirror.fail = True
    with pytest.raises(PursuitMirrorError):
        store.save(
            "goal_x",
            satisfied=set(),
            history=[],
            dedupe={},
            failed_approaches=set(),
            active_missions=set(),
            commitments=[],
            schedule=None,
        )
    assert not (tmp_path / "ps" / "goal_x.json").exists()


def test_mirror_read_failure_is_not_silently_ignored(tmp_path: Path) -> None:
    mirror = FakeMirror()
    store = DurablePursuitStateStore(tmp_path / "ps", mirror=mirror)
    mirror.fail = True
    with pytest.raises(PursuitMirrorError):
        store.load("goal_x")


def test_file_fallback_when_db_has_no_row(tmp_path: Path) -> None:
    plain = DurablePursuitStateStore(tmp_path / "ps")
    plain.save(
        "goal_old",
        satisfied={"a"},
        history=[],
        dedupe={},
        failed_approaches=set(),
        active_missions=set(),
        commitments=[],
        schedule=None,
    )
    mirrored = DurablePursuitStateStore(tmp_path / "ps", mirror=FakeMirror())
    raw = mirrored.load("goal_old")
    assert raw is not None and raw["satisfied_criteria"] == ["a"]


def test_long_dedupe_keys_are_hashed_to_column_width() -> None:
    assert dedupe_db_key("short") == "short"
    long_key = "k" * 200
    hashed = dedupe_db_key(long_key)
    assert len(hashed) == 64 and hashed == dedupe_db_key(long_key)
```

### Step 4 — `tests/integration/db/test_v20_pursuit_writethrough_sql.py` (create, exactly)
```python
"""SW-W1-S9 / V20-E03: pursuit snapshot write-through to PostgreSQL survives volume loss."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.goals.models import Goal, GoalStore
from swarm.pursuit import PursuitEngine, PursuitScheduler, RecordingExecutor
from swarm.pursuit.pg_mirror import PursuitPgMirror
from swarm.pursuit.state_store import DurablePursuitStateStore

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
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


def test_pursuit_state_restored_from_postgres(factory, tmp_path: Path) -> None:
    with factory() as s:
        s.execute(text("TRUNCATE pursuit_cycles, pursuit_schedules, pursuit_dedupe"))
        s.commit()
    goals = GoalStore(tmp_path / "goals")
    goal = goals.create(
        Goal(
            project_id="proj_wt_sql",
            desired_outcome="write through sql",
            verification_criteria=["one", "two"],
            resource_envelope={"spend_usd_ceiling": 0.0},
            authority_envelope={"tools": ["workspace.read"], "providers": ["fake"]},
        )
    )

    def engine(volume: str) -> PursuitEngine:
        return PursuitEngine(
            goals,
            executor=RecordingExecutor(default_success=True),
            scheduler=PursuitScheduler(clock=lambda: 10.0),
            state_store=DurablePursuitStateStore(
                tmp_path / volume, mirror=PursuitPgMirror(factory)
            ),
        )

    first = engine("vol_a")
    first.tick(goal.id, force=True)
    first.tick(goal.id, force=True)
    history = [c.cycle_id for c in first.history(goal.id)]

    cold = engine("vol_b_empty")
    assert [c.cycle_id for c in cold.history(goal.id)] == history
    assert cold.satisfied_criteria(goal.id) == first.satisfied_criteria(goal.id)
    with factory() as s:
        n_cycles = s.execute(
            text("SELECT count(*) FROM pursuit_cycles WHERE goal_id = :g"), {"g": goal.id}
        ).scalar_one()
    assert n_cycles == len(history)
```

### Step 5 — run
```bash
uv run pytest tests/pursuit -q          # all pass (5 new)
uv run pytest tests/product tests/api -q
```

### Section-5 acceptance
- [ ] With a mirror, a cold engine on an **empty file volume** restores history, satisfied criteria and schedule from PostgreSQL (integration test).
- [ ] A mirror write failure raises `PursuitMirrorError` and leaves no file behind; a read failure raises.
- [ ] Without a mirror, behaviour is unchanged, and `tests/pursuit/test_pursuit_durability.py` passes unchanged.
- [ ] Re-saving does not duplicate cycle rows; long dedupe keys fit the 64-character column.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s9 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s9
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/pursuit -q
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
git add src/swarm/pursuit/pg_mirror.py src/swarm/pursuit/state_store.py tests/pursuit/test_v20_writethrough.py tests/integration/db/test_v20_pursuit_writethrough_sql.py docs/v2.3/sessions/SW-W1-S9.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.0): E03 pursuit state write-through to PostgreSQL with fail-closed mirror" -m "Session: SW-W1-S9. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v20-w1-s9-pursuit-writethrough
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v20-w1-s9-pursuit-writethrough --title "[SW-W1-S9] V20-E03 pursuit PostgreSQL write-through store" --body-file docs/v2.3/sessions/SW-W1-S9.md
git ls-remote origin refs/heads/cursor/v20-w1-s9-pursuit-writethrough   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S9.md` with exactly these headings:
```markdown
# SW-W1-S9 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S9.md` then `git commit -m "WIP(SW-W1-S9): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v20-w1-s9-pursuit-writethrough` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v20-w1-s9-pursuit-writethrough?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S9
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/pursuit/pg_mirror.py`, `src/swarm/pursuit/state_store.py`, `tests/pursuit/test_v20_writethrough.py`, `tests/integration/db/test_v20_pursuit_writethrough_sql.py`, `docs/v2.3/sessions/SW-W1-S9.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete").
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
