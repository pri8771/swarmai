# SW-W1-S2 handoff
- Branch: `cursor/sw-w1-s2-460c`   Base SHA: `d59a05638bbc2473db18d395694ca19fefa81ac2`   Head SHA (code): `9979b37aaa298fc1deb2fd681a1d1d7bcd8e02ba`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S2.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/scheduling/store.py`: `SqlSchedulingStore` (PostgreSQL) implementing the `SchedulingStore` protocol with the same versioning rule as `InMemorySchedulingStore` (insert on `expected_version=None`, `SELECT … FOR UPDATE` then compare, unique violations → `StaleVersionError`).
- `tests/integration/db/test_v23_store_sql.py`: 9 integration tests (4 behaviours × 2 stores + a 4-thread race with exactly one winner).
- No change to `models.py` or migrations.
## Verification
Checks run by `/agent/wt/check.sh` on commit `9979b37aaa298fc1deb2fd681a1d1d7bcd8e02ba` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 241 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 9 passed in 1.41s
offline CI: 542 passed, 3 skipped in 27.39s
integration (Postgres): 79 passed in 18.60s
tree: 2e7f8012bb14a3867ac5ab6df82605a8b142e058 dirty=0
```

## Acceptance
- [x] 9 integration tests pass (4 behaviors × 2 stores + 1 race test).
- [x] `SqlSchedulingStore` satisfies the `SchedulingStore` protocol (mypy clean).
- [x] No change to `models.py` or migrations.
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- Integration run is required for this session and was executed (private DB `swarm_sw460c`).
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
