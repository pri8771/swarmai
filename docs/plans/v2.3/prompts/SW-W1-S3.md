# SW-W1-S3 — DispatchIntent reservation / compensation service

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S3` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s3-dispatch-intent` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | SW-W0-S2 |
| Handoff file | `docs/v2.3/sessions/SW-W1-S3.md` |
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
git checkout -b cursor/v23-w1-s3-dispatch-intent origin/cursor/sw-v23-integration-460c
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
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/scheduling/dispatch_intent.py` — create
- `tests/controller/test_v23_dispatch_intent.py` — create
- `docs/v2.3/sessions/SW-W1-S3.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Make reservations transactional and fail-closed (ART-V23 "DispatchIntent"). Before a task is dispatched, the scheduler reserves **every** required component (provider route, worker, tool units, budget). If any reservation fails, everything already reserved is released and the intent ends `COMPENSATED`. Intents are idempotent per `attempt_id`, have a TTL, and expired `PREPARED`/`RESERVED` intents are released on restart. `DISPATCHED` intents are never auto-released.

The service does not know how to reserve capacity. It calls the injected `reserve(intent, component) -> reservation_id` and `release(intent, component)` functions, which SW-W2-S1 wires to real capacity. It persists through any `SchedulingStore` (the in-memory store from SW-W0-S2 in tests; the SQL store in production).

The code below was compiled and run against `dev + SW-W0-S2` (7 passed; ruff and mypy clean). Paste it **exactly**.

### Step 1 — `src/swarm/scheduling/dispatch_intent.py` (create, exactly)
```python
"""DispatchIntent service — all-or-nothing reservation with durable compensation.

State machine (ART-V23-MULTIMISSION_SCHEDULER "DispatchIntent"):

    PREPARED --reserve all ok--> RESERVED --mark_dispatched--> DISPATCHED --complete--> COMPLETED
    PREPARED --any reserve fails--> COMPENSATED   (every already-reserved part released)
    PREPARED|RESERVED --cancel--> CANCELLED       (reserved parts released)
    PREPARED|RESERVED --expired (recover_expired)--> EXPIRED (reserved parts released)

DISPATCHED is never auto-recovered: work may already run on a worker, so it needs
explicit completion/reconciliation, never a silent release.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from swarm.contracts.common import payload_hash, utc_now
from swarm.contracts.v23 import (
    TERMINAL_INTENT_STATES,
    DispatchIntent,
    DispatchIntentComponent,
    DispatchIntentState,
    SchedulingStore,
)

ReserveFn = Callable[[DispatchIntent, DispatchIntentComponent], str | None]
ReleaseFn = Callable[[DispatchIntent, DispatchIntentComponent], None]
Clock = Callable[[], datetime]


class DispatchIntentError(RuntimeError):
    pass


def attempt_digest(
    *, attempt_id: str, task_id: str, site_epoch: int, scheduler_epoch: int, generation: int
) -> str:
    return payload_hash(
        {
            "attempt_id": attempt_id,
            "task_id": task_id,
            "site_epoch": site_epoch,
            "scheduler_epoch": scheduler_epoch,
            "cancellation_generation": generation,
        }
    )


class DispatchIntentService:
    def __init__(
        self,
        store: SchedulingStore,
        *,
        reserve: ReserveFn,
        release: ReleaseFn,
        clock: Clock | None = None,
        ttl_seconds: float = 30.0,
    ) -> None:
        self.store = store
        self._reserve = reserve
        self._release = release
        self._clock: Clock = clock or utc_now
        self.ttl_seconds = ttl_seconds

    def prepare(
        self,
        *,
        attempt_id: str,
        project_id: str,
        mission_id: str,
        task_id: str,
        components: list[DispatchIntentComponent],
        site_epoch: int,
        scheduler_epoch: int,
        cancellation_generation: int,
    ) -> DispatchIntent:
        """Create the intent and reserve every component, or compensate all of them.

        Idempotent per ``attempt_id``: a second call returns the existing intent
        unchanged (duplicate scheduler ticks cannot double-reserve).
        """
        existing = self.store.get_intent_by_attempt(attempt_id)
        if existing is not None:
            return existing
        digest = attempt_digest(
            attempt_id=attempt_id,
            task_id=task_id,
            site_epoch=site_epoch,
            scheduler_epoch=scheduler_epoch,
            generation=cancellation_generation,
        )
        intent = self.store.put_intent(
            DispatchIntent(
                attempt_id=attempt_id,
                project_id=project_id,
                mission_id=mission_id,
                task_id=task_id,
                components=[c.model_copy(update={"reserved": False}) for c in components],
                site_epoch=site_epoch,
                scheduler_epoch=scheduler_epoch,
                cancellation_generation=cancellation_generation,
                attempt_digest=digest,
                expires_at=self._clock() + timedelta(seconds=self.ttl_seconds),
            ),
            expected_version=None,
        )
        reserved: list[DispatchIntentComponent] = []
        for comp in intent.components:
            try:
                reservation_id = self._reserve(intent, comp)
            except Exception as exc:  # noqa: BLE001 — any failure compensates
                return self._compensate(intent, reserved, f"reserve_failed:{comp.kind}:{exc}")
            reserved.append(
                comp.model_copy(update={"reserved": True, "reservation_id": reservation_id})
            )
            components = reserved + intent.components[len(reserved) :]
            intent = self.store.put_intent(
                intent.model_copy(update={"components": components}),
                expected_version=intent.version,
            )
        return self.store.put_intent(
            intent.model_copy(update={"state": DispatchIntentState.RESERVED}),
            expected_version=intent.version,
        )

    def mark_dispatched(self, intent_id: str) -> DispatchIntent:
        intent = self._require(intent_id)
        if intent.state == DispatchIntentState.DISPATCHED:
            return intent
        if intent.state != DispatchIntentState.RESERVED:
            raise DispatchIntentError(f"dispatch_illegal_from:{intent.state.value}")
        if self._clock() >= intent.expires_at:
            raise DispatchIntentError("intent_expired")
        return self.store.put_intent(
            intent.model_copy(update={"state": DispatchIntentState.DISPATCHED}),
            expected_version=intent.version,
        )

    def complete(self, intent_id: str) -> DispatchIntent:
        intent = self._require(intent_id)
        if intent.state == DispatchIntentState.COMPLETED:
            return intent
        if intent.state != DispatchIntentState.DISPATCHED:
            raise DispatchIntentError(f"complete_illegal_from:{intent.state.value}")
        return self.store.put_intent(
            intent.model_copy(update={"state": DispatchIntentState.COMPLETED}),
            expected_version=intent.version,
        )

    def cancel(self, intent_id: str, *, reason: str = "cancelled") -> DispatchIntent:
        intent = self._require(intent_id)
        if intent.state in TERMINAL_INTENT_STATES:
            return intent
        if intent.state == DispatchIntentState.DISPATCHED:
            raise DispatchIntentError("cancel_dispatched_requires_worker_cancel")
        self._release_all(intent)
        return self.store.put_intent(
            intent.model_copy(
                update={"state": DispatchIntentState.CANCELLED, "failure_reason": reason}
            ),
            expected_version=intent.version,
        )

    def recover_expired(self) -> list[DispatchIntent]:
        """Release and expire PREPARED/RESERVED intents past their TTL (restart path)."""
        now = self._clock()
        out: list[DispatchIntent] = []
        states = frozenset({DispatchIntentState.PREPARED, DispatchIntentState.RESERVED})
        for intent in self.store.list_intents(states=states):
            if now < intent.expires_at:
                continue
            self._release_all(intent)
            out.append(
                self.store.put_intent(
                    intent.model_copy(
                        update={"state": DispatchIntentState.EXPIRED, "failure_reason": "ttl"}
                    ),
                    expected_version=intent.version,
                )
            )
        return out

    def _compensate(
        self, intent: DispatchIntent, reserved: list[DispatchIntentComponent], reason: str
    ) -> DispatchIntent:
        for comp in reversed(reserved):
            self._release(intent, comp)
        released = [c.model_copy(update={"reserved": False}) for c in intent.components]
        return self.store.put_intent(
            intent.model_copy(
                update={
                    "state": DispatchIntentState.COMPENSATED,
                    "components": released,
                    "failure_reason": reason[:200],
                }
            ),
            expected_version=intent.version,
        )

    def _release_all(self, intent: DispatchIntent) -> None:
        for comp in reversed(intent.components):
            if comp.reserved:
                self._release(intent, comp)

    def _require(self, intent_id: str) -> DispatchIntent:
        intent = self.store.get_intent(intent_id)
        if intent is None:
            raise DispatchIntentError(f"intent_missing:{intent_id}")
        return intent
```

### Step 2 — `tests/controller/test_v23_dispatch_intent.py` (create, exactly)
```python
"""SW-W1-S3: dispatch intents are all-or-nothing, idempotent and recoverable."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from swarm.contracts.v23 import DispatchIntent, DispatchIntentComponent, DispatchIntentState
from swarm.scheduling.dispatch_intent import DispatchIntentError, DispatchIntentService
from swarm.scheduling.memory_store import InMemorySchedulingStore


class FakeCapacity:
    def __init__(self, fail_kind: str | None = None) -> None:
        self.fail_kind = fail_kind
        self.held: dict[str, str] = {}
        self.reserve_calls = 0

    def reserve(self, intent: DispatchIntent, comp: DispatchIntentComponent) -> str:
        self.reserve_calls += 1
        if comp.kind == self.fail_kind:
            raise RuntimeError("capacity_unavailable")
        rid = f"res_{comp.kind}_{intent.attempt_id}"
        self.held[rid] = comp.kind
        return rid

    def release(self, intent: DispatchIntent, comp: DispatchIntentComponent) -> None:
        self.held.pop(f"res_{comp.kind}_{intent.attempt_id}", None)


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


COMPONENTS = [
    DispatchIntentComponent(kind="provider", ref="rt_ollama_default"),
    DispatchIntentComponent(kind="worker", ref="local"),
    DispatchIntentComponent(kind="tool", ref="workspace.read"),
]


def _service(cap: FakeCapacity, clock: Clock | None = None) -> DispatchIntentService:
    return DispatchIntentService(
        InMemorySchedulingStore(),
        reserve=cap.reserve,
        release=cap.release,
        clock=clock or Clock(),
        ttl_seconds=30,
    )


def _prepare(svc: DispatchIntentService, attempt: str = "att_1") -> DispatchIntent:
    return svc.prepare(
        attempt_id=attempt,
        project_id="proj_a",
        mission_id="msn_1",
        task_id="tsk_1",
        components=COMPONENTS,
        site_epoch=1,
        scheduler_epoch=1,
        cancellation_generation=0,
    )


def test_all_components_reserved() -> None:
    cap = FakeCapacity()
    intent = _prepare(_service(cap))
    assert intent.state == DispatchIntentState.RESERVED
    assert all(c.reserved for c in intent.components)
    assert len(cap.held) == 3


def test_partial_failure_compensates_everything() -> None:
    cap = FakeCapacity(fail_kind="worker")
    intent = _prepare(_service(cap))
    assert intent.state == DispatchIntentState.COMPENSATED
    assert cap.held == {}
    assert intent.failure_reason is not None and "worker" in intent.failure_reason


def test_prepare_is_idempotent_per_attempt() -> None:
    cap = FakeCapacity()
    svc = _service(cap)
    first = _prepare(svc)
    second = _prepare(svc)
    assert first.intent_id == second.intent_id
    assert cap.reserve_calls == 3


def test_dispatch_complete_and_illegal_transitions() -> None:
    cap = FakeCapacity()
    svc = _service(cap)
    intent = _prepare(svc)
    with pytest.raises(DispatchIntentError):
        svc.complete(intent.intent_id)
    svc.mark_dispatched(intent.intent_id)
    with pytest.raises(DispatchIntentError, match="cancel_dispatched"):
        svc.cancel(intent.intent_id)
    done = svc.complete(intent.intent_id)
    assert done.state == DispatchIntentState.COMPLETED


def test_cancel_releases_reservations() -> None:
    cap = FakeCapacity()
    svc = _service(cap)
    intent = _prepare(svc)
    cancelled = svc.cancel(intent.intent_id, reason="mission_cancelled")
    assert cancelled.state == DispatchIntentState.CANCELLED
    assert cap.held == {}


def test_recover_expired_releases_once_and_skips_dispatched() -> None:
    cap = FakeCapacity()
    clock = Clock()
    svc = _service(cap, clock)
    stuck = _prepare(svc, "att_stuck")
    running = _prepare(svc, "att_running")
    svc.mark_dispatched(running.intent_id)
    clock.now = clock.now + timedelta(seconds=31)
    recovered = svc.recover_expired()
    assert [i.intent_id for i in recovered] == [stuck.intent_id]
    assert recovered[0].state == DispatchIntentState.EXPIRED
    assert svc.recover_expired() == []
    assert set(cap.held) == {f"res_{k}_att_running" for k in ("provider", "worker", "tool")}


def test_expired_intent_cannot_dispatch() -> None:
    cap = FakeCapacity()
    clock = Clock()
    svc = _service(cap, clock)
    intent = _prepare(svc)
    clock.now = clock.now + timedelta(seconds=31)
    with pytest.raises(DispatchIntentError, match="intent_expired"):
        svc.mark_dispatched(intent.intent_id)
```

### Step 3 — run
```bash
uv run pytest tests/controller/test_v23_dispatch_intent.py -q     # 7 passed
```

### Section-5 acceptance
- [ ] Partial reservation failure releases every earlier reservation (pathological case: "partial provider reservation succeeds but worker reservation fails").
- [ ] Crash after reserve, before dispatch: `recover_expired` releases exactly once and never touches `DISPATCHED` (pathological case: "scheduler crashes after reservations but before dispatch").
- [ ] A duplicate `prepare` for the same attempt does not reserve again (pathological case: duplicate ticks).
- [ ] 7 tests pass.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s3 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s3
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/controller/test_v23_dispatch_intent.py -q
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
git add src/swarm/scheduling/dispatch_intent.py tests/controller/test_v23_dispatch_intent.py docs/v2.3/sessions/SW-W1-S3.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): transactional dispatch intents with all-or-nothing reservation and compensation" -m "Session: SW-W1-S3. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s3-dispatch-intent
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s3-dispatch-intent --title "[SW-W1-S3] DispatchIntent reservation / compensation service" --body-file docs/v2.3/sessions/SW-W1-S3.md
git ls-remote origin refs/heads/cursor/v23-w1-s3-dispatch-intent   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S3.md` with exactly these headings:
```markdown
# SW-W1-S3 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S3.md` then `git commit -m "WIP(SW-W1-S3): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s3-dispatch-intent` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s3-dispatch-intent?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S3
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/scheduling/dispatch_intent.py`, `tests/controller/test_v23_dispatch_intent.py`, `docs/v2.3/sessions/SW-W1-S3.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: reservation intent is fail-closed; no double dispatch; expiry handling.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
