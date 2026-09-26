# SW-FIX-FLAKE — Deterministic V20-E08 kill-bound tests

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-FIX-FLAKE` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/sw-fix-killbound-flake` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | FIX |
| Depends on | SW-W1-S13 |
| Handoff file | `docs/v2.3/sessions/SW-FIX-FLAKE.md` |
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
git checkout -b cursor/sw-fix-killbound-flake origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W1-S13. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:tests/tools/test_v20_cancel_killbound.py && echo "OK tests/tools/test_v20_cancel_killbound.py" || echo "MISSING tests/tools/test_v20_cancel_killbound.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `tests/tools/test_v20_cancel_killbound.py` — modify
- `docs/v2.3/sessions/SW-FIX-FLAKE.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
> **EXECUTED** 2026-09-26 by the integrator: branch `cursor/sw-fix-killbound-flake-460c` head `ee739728aad89b81518b249e062bad665fdb6b4f` (code `221a1f69`), merged into `cursor/sw-v23-integration-460c` at `1b3f48ad2a1d27cb4d485416502cdd3ba2d12796`.

**Goal.** `tests/tools/test_v20_cancel_killbound.py::test_cancel_kills_group_before_timeout` failed about 1 in 25 full runs ("grandchild survived the kill bound"). Make it deterministic without weakening what it proves (V20-E08: cancel/timeout kill the whole process group within `KILL_BOUND_SECONDS`). Test-only; `src/swarm/tools/sandbox_runner.py` is unchanged.

### Step 0 — analysis
Direct reproduction under load (12 busy loops on 4 CPUs, 40 runs) stayed green. The helper has a real race matching the message: `_assert_dead` called `_alive` twice; when the loop saw a zombie and exited, PID 1 could reap it before the final call, whose `/proc/<pid>/stat` read then raised and `except OSError: return True` reported it alive. The cancel test also used a fixed `threading.Timer(1.0, cancel.set)`.

### Step 1 — `tests/tools/test_v20_cancel_killbound.py`
- `_alive`: `FileNotFoundError`/`ProcessLookupError` on the `/proc` read → dead; state after the last `)` in `Z`/`X` → dead; other `OSError` → alive.
- `_assert_dead`: poll until dead or the bound; assert on the last sample.
- Cancel test: a thread waits for `child.pid`, records `cancel_at`, sets `cancel`; assert `returned_at - cancel_at < KILL_BOUND_SECONDS` and the grandchild dies within the bound.
- Timeout test: `timeout_seconds` 4.0 so the grandchild exists before the timeout.
- Add `test_alive_treats_reaped_zombie_as_dead` (fails with the old helper).

### Acceptance (this session)
- [ ] `4 passed`; 50/50 green under CPU load.
- [ ] The kill bound is still asserted for cancel and timeout.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_fix_flake OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_fix_flake
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/tools/test_v20_cancel_killbound.py -q
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
git add tests/tools/test_v20_cancel_killbound.py docs/v2.3/sessions/SW-FIX-FLAKE.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "test(sandbox): make the V20-E08 kill-bound tests deterministic (SW-FIX-FLAKE)" -m "Session: SW-FIX-FLAKE. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/sw-fix-killbound-flake
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/sw-fix-killbound-flake --title "[SW-FIX-FLAKE] Deterministic V20-E08 kill-bound tests" --body-file docs/v2.3/sessions/SW-FIX-FLAKE.md
git ls-remote origin refs/heads/cursor/sw-fix-killbound-flake   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-FIX-FLAKE.md` with exactly these headings:
```markdown
# SW-FIX-FLAKE handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-FIX-FLAKE.md` then `git commit -m "WIP(SW-FIX-FLAKE): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/sw-fix-killbound-flake` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/sw-fix-killbound-flake?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-FIX-FLAKE
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `tests/tools/test_v20_cancel_killbound.py`, `docs/v2.3/sessions/SW-FIX-FLAKE.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: test-only; the kill bound is measured from cancel; the grandchild exists before the kill; no assertion weakened.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
