# SW-W1-S13 handoff
- Branch: `cursor/sw-w1-s13-460c`   Base SHA: `c7a653eea358db2a9c45c3293f81c5d55af65ec2`   Head SHA (code): `91cff6f8b03067990153abd976fc963242320a66`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S13.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/tools/sandbox_runner.py`: `run_python` starts the script in its own session/process group (`start_new_session=True`); on timeout or when keyword-only `cancel: threading.Event` is set, the whole group gets `SIGKILL`; pipes are awaited at most `KILL_BOUND_SECONDS = 10.0`. `SandboxResult` gains `cancelled` and `killed_group` (default `False`); positional signature unchanged.
- `tests/tools/test_v20_cancel_killbound.py` (3): grandchild dead within the bound on timeout; cancel before timeout; normal run unchanged.
## Verification
Checks run by `/agent/wt/check.sh` on commit `91cff6f8b03067990153abd976fc963242320a66` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 249 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 3 passed in 2.63s
offline CI: 596 passed, 3 skipped in 30.35s
integration (Postgres): 85 passed in 21.87s
tree: 066a6d0191276994d53a6d16458f6d94e55ca381 dirty=0
```

## Acceptance
- [x] On timeout, a grandchild process is dead within `KILL_BOUND_SECONDS`, and the result has `timed_out=True, killed_group=True, ok=False`.
- [x] Setting `cancel` kills the group before the timeout, and the result has `cancelled=True`.
- [x] Normal runs return the same fields and values as before.
- [x] `swarm sandbox self-test --network off`, if it exists in the CLI, still reports `ok`.
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c`. Linux only (CI platform); existing `win32` skip kept, no new skips.
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
