# SW-W0-S3 — Security hotfixes: ops-events cross-project leak (F-01) and Retry-After cap (F-06)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W0-S3` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w0-s3-security-hotfixes` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 0 |
| Depends on | none |
| Handoff file | `docs/v2.3/sessions/SW-W0-S3.md` |
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
git checkout -b cursor/v23-w0-s3-security-hotfixes origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
This session has **no dependencies**. Go to Step 1.

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/api/routes_v1.py` — modify (only the function list_ops_events)
- `src/swarm/broker/retry.py` — modify
- `tests/api/test_v23_ops_events_scope.py` — create
- `tests/broker/test_retry_after_cap.py` — create
- `docs/v2.3/sessions/SW-W0-S3.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Fix two security findings with the smallest possible change.
- **F-01 (P1, cross-tenant):** `GET /v1/ops/events` without `project_id` returns every project's events. Only admins may see everything; other principals see only their own projects.
- **F-06 (P3, retries):** `RetryOwner.decide` uses upstream `Retry-After` unbounded (`wait = float(retry_after)`). Clamp it to `[0, max_retry_after_seconds]` (default 30 s) and treat NaN/inf as the cap.

Both fixes and tests were compiled and run against `dev @ 8e1c0fde` (all green).

### Step 1 — reproduce F-01 first (it must FAIL before the fix)
Create `tests/api/test_v23_ops_events_scope.py` exactly:
```python
"""SW-W0-S3 / F-01: GET /v1/ops/events must not leak other projects' events."""

from __future__ import annotations

from fastapi.testclient import TestClient

from swarm.api.app import create_app


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _app_with_events():
    app = create_app(require_auth=True, db_reachable=True, seed_fixtures=True)
    log = app.state.ops_events
    log.emit("scheduler.decision", "scheduler", project_id="proj_demo", detail={"n": 1})
    log.emit("scheduler.decision", "scheduler", project_id="proj_other", detail={"n": 2})
    log.emit("site.epoch", "recovery", project_id=None, detail={"n": 3})
    return app


def test_unscoped_list_only_returns_own_projects() -> None:
    app = _app_with_events()
    with TestClient(app) as client:
        res = client.get("/v1/ops/events", headers=_auth("atk_policy_demo"))
    assert res.status_code == 200
    projects = {e["project_id"] for e in res.json()["events"]}
    assert projects == {"proj_demo"}


def test_foreign_project_filter_is_forbidden() -> None:
    app = _app_with_events()
    with TestClient(app) as client:
        res = client.get(
            "/v1/ops/events", params={"project_id": "proj_other"}, headers=_auth("atk_policy_demo")
        )
    assert res.status_code == 403
    assert res.json()["code"] == "forbidden_project"


def test_admin_sees_all_events() -> None:
    app = _app_with_events()
    app.state.auth.issue(
        subject="site-admin", project_ids=set(), roles={"admin"}, token="atk_admin_test"
    )
    with TestClient(app) as client:
        res = client.get("/v1/ops/events", headers=_auth("atk_admin_test"))
    assert res.status_code == 200
    assert len(res.json()["events"]) == 3
```
Run `uv run pytest tests/api/test_v23_ops_events_scope.py -q`. Expected **before** the fix: `test_unscoped_list_only_returns_own_projects` fails (it sees `proj_other` and `None`). Write the failing output line in the handoff.

### Step 2 — fix `list_ops_events` in `src/swarm/api/routes_v1.py`
Find the function that starts with `@router.get("/ops/events")` (around line 2173). Replace the **whole function** (decorator through its `return`) with exactly this. Do not touch any other function.
```python
@router.get("/ops/events")
async def list_ops_events(
    request: Request,
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
) -> dict[str, Any]:
    from swarm.observability import OpsEventLog

    log = getattr(request.app.state, "ops_events", None)
    if log is None:
        log = OpsEventLog()
        request.app.state.ops_events = log
    if project_id:
        auth.require_project(principal, project_id)
        return {"events": log.list_events(project_id=project_id)}
    if "admin" in principal.roles:
        return {"events": log.list_events()}
    # Non-admin without project_id: only the principal's projects; never unscoped events.
    events: list[dict[str, Any]] = []
    for pid in sorted(principal.project_ids):
        events.extend(log.list_events(project_id=pid))
    events.sort(key=lambda e: (str(e.get("at")), str(e.get("event_id"))))
    return {"events": events[-100:]}
```
Re-run Step 1's test: 3 passed.

### Step 3 — reproduce F-06, then fix `src/swarm/broker/retry.py`
Create `tests/broker/test_retry_after_cap.py` exactly:
```python
"""SW-W0-S3 / F-06: upstream Retry-After is bounded."""

from __future__ import annotations

import math

import pytest

from swarm.broker.retry import RetryConfig, RetryOwner
from swarm.contracts.enums import ErrorClass


@pytest.mark.parametrize(
    ("retry_after", "expected"),
    [
        (5.0, 5.0),
        (86_400.0, 30.0),
        (-10.0, 0.0),
        (math.inf, 30.0),
        (math.nan, 30.0),
    ],
)
def test_retry_after_is_clamped(retry_after: float, expected: float) -> None:
    owner = RetryOwner()
    owner.note_attempt("call_1")
    decision = owner.decide("call_1", ErrorClass.RATE_LIMIT, retry_after=retry_after)
    assert decision.should_retry is True
    assert decision.wait_seconds == expected


def test_cap_is_configurable() -> None:
    owner = RetryOwner(RetryConfig(max_retry_after_seconds=2.5))
    owner.note_attempt("call_2")
    decision = owner.decide("call_2", ErrorClass.TRANSIENT, retry_after=100.0)
    assert decision.wait_seconds == 2.5


def test_attempt_bound_still_applies() -> None:
    owner = RetryOwner()
    for _ in range(3):
        owner.note_attempt("call_3")
    decision = owner.decide("call_3", ErrorClass.RATE_LIMIT, retry_after=1.0)
    assert decision.should_retry is False
    assert decision.reason == "max_attempts"
```
Run it: it fails before the fix (`RetryConfig` has no `max_retry_after_seconds`; waits are unbounded).

Edit `src/swarm/broker/retry.py`:
1. Add `import math` above `import random`.
2. In `class RetryConfig`, add a last field: `max_retry_after_seconds: float = 30.0`.
3. In `decide`, replace
```python
        if retry_after is not None:
            wait = float(retry_after)
```
with
```python
        if retry_after is not None:
            wait = float(retry_after)
            if not math.isfinite(wait):
                wait = self.config.max_retry_after_seconds
            wait = min(max(wait, 0.0), self.config.max_retry_after_seconds)
```
Nothing else changes (attempt counting stays as is).

### Section-5 acceptance
- [ ] Before-fix failure of both new test files recorded in the handoff.
- [ ] `tests/api/test_v23_ops_events_scope.py` 3 passed; `tests/broker/test_retry_after_cap.py` 7 passed.
- [ ] `git diff src/swarm/api/routes_v1.py` touches only `list_ops_events`.
- [ ] Existing `tests/api` and `tests/broker` pass unchanged.

> Later change (EXECUTED): SW-FIX-RETRY (`b3162712`) replaced the F-06 clamp with a give-up (`retry_after_exceeds_cap`) when `Retry-After` exceeds the cap; `tests/broker/test_retry_after_cap.py` was rewritten accordingly. On a tree containing that fix, this session's F-06 test expectations no longer apply.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w0_s3 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w0_s3
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/api/test_v23_ops_events_scope.py tests/broker/test_retry_after_cap.py tests/broker tests/api -q
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
git add src/swarm/api/routes_v1.py src/swarm/broker/retry.py tests/api/test_v23_ops_events_scope.py tests/broker/test_retry_after_cap.py docs/v2.3/sessions/SW-W0-S3.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "fix(security): scope GET /v1/ops/events to principal projects (F-01); cap upstream Retry-After (F-06)" -m "Session: SW-W0-S3. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w0-s3-security-hotfixes
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w0-s3-security-hotfixes --title "[SW-W0-S3] Security hotfixes: ops-events cross-project leak (F-01) and Retry-After cap (F-06)" --body-file docs/v2.3/sessions/SW-W0-S3.md
git ls-remote origin refs/heads/cursor/v23-w0-s3-security-hotfixes   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W0-S3.md` with exactly these headings:
```markdown
# SW-W0-S3 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W0-S3.md` then `git commit -m "WIP(SW-W0-S3): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w0-s3-security-hotfixes` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w0-s3-security-hotfixes?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W0-S3
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/api/routes_v1.py`, `src/swarm/broker/retry.py`, `tests/api/test_v23_ops_events_scope.py`, `tests/broker/test_retry_after_cap.py`, `docs/v2.3/sessions/SW-W0-S3.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: GET /v1/ops/events returns only the principal's projects (F-01); Retry-After is capped (F-06).
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
