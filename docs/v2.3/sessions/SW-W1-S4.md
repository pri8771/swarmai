# SW-W1-S4 handoff
- Branch: `cursor/sw-w1-s4-460c`   Base SHA: `d628d28dd134474c50adda431ed34cf675090e49`   Head SHA (code): `74b72e25548f9e5d79506ab1eac4c82c0d70f9a9`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S4.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/scheduling/epoch.py`: scheduler epoch lease (fencing token in `v23_scheduler_epochs`), in-memory and SQL services; acquire bumps epoch after expiry; stale holders get `StaleSchedulerEpochError` on renew/`require_current`.
- `src/swarm/scheduling/singleton.py`: `SingletonTicker` runs a callback only while holding the lease; fencing during a tick reported as `fenced_after_tick`.
- Tests: `tests/controller/test_v23_epoch.py` (4), `tests/integration/db/test_v23_epoch_sql.py` (1; two service instances on one DB).
## Verification
Checks run by `/agent/wt/check.sh` on commit `74b72e25548f9e5d79506ab1eac4c82c0d70f9a9` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 244 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 5 passed in 0.45s
offline CI: 553 passed, 3 skipped in 26.77s
integration (Postgres): 80 passed in 18.28s
tree: 8111ad033179d99dfc702a7adb3e470236a9bb47 dirty=0
```

## Acceptance
- [x] A second holder cannot acquire while the lease is valid; after expiry the epoch increments; the old holder is fenced (`StaleSchedulerEpochError`) on renew and `require_current`.
- [x] `SingletonTicker` runs the tick in only one holder; fencing during a tick is reported as `fenced_after_tick`.
- [x] The SQL service gives the same results across two service instances sharing one database.
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c`.
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
