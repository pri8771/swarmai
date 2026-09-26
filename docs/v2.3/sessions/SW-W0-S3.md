# SW-W0-S3 handoff
- Branch: `cursor/sw-w0-s3-460c`   Base SHA: `cfcd412c1dab98e80b0a8f51ff8258dc6a4a2a80`   Head SHA (code): `4a4bd7dd7256c695926d46458986590603eff342`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W0-S3.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- F-01: `list_ops_events` in `src/swarm/api/routes_v1.py` (only this function) now returns all events only to `admin`; other principals without `project_id` get only events of their own projects (never unscoped events); a foreign `project_id` is 403 `forbidden_project` (unchanged path via `auth.require_project`).
- F-06: `RetryConfig.max_retry_after_seconds = 30.0`; `RetryOwner.decide` clamps upstream `Retry-After` to `[0, cap]`, NaN/inf → cap. Attempt counting unchanged.
- Tests `tests/api/test_v23_ops_events_scope.py` (3) and `tests/broker/test_retry_after_cap.py` (7).
- Before the fix: `6 failed, 4 passed` — `FAILED tests/api/test_v23_ops_events_scope.py::test_unscoped_list_only_returns_own_projects` plus 5 retry-cap failures (`test_retry_after_is_clamped[86400.0-30.0]`, `[-10.0-0.0]`, `[inf-30.0]`, `[nan-30.0]`, `test_cap_is_configurable - TypeError`). After: 10 passed.
## Verification
Checks run by `/agent/wt/check.sh` on commit `4a4bd7dd7256c695926d46458986590603eff342` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 239 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 54 passed in 2.89s
offline CI: 527 passed, 3 skipped in 27.59s
integration (Postgres): 70 passed in 18.19s
tree: 162990b907107312a80169ef6eff02de1597ab8d dirty=0
```

## Acceptance
- [x] Before-fix failure of both new test files recorded in the handoff.
- [x] `tests/api/test_v23_ops_events_scope.py` 3 passed; `tests/broker/test_retry_after_cap.py` 7 passed.
- [x] `git diff src/swarm/api/routes_v1.py` touches only `list_ops_events`.
- [x] Existing `tests/api` and `tests/broker` pass unchanged.
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no real network calls, no `accepted`/`complete` claims.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c`.
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
