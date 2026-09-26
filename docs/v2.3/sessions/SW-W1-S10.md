# SW-W1-S10 handoff
- Branch: `cursor/sw-w1-s10-460c`   Base SHA: `41a2543fc487ab0c4c2ac8d5f9c33be7150546fa`   Head SHA (code): `9fca17c9a040fcfdec42de618911cc7a12dbf0ae`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S10.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- F-13: `src/swarm/pursuit/accounting.py` — an unknown-usage hold keeps `max(reserved, reported)` committed; `release()` refuses unknown holds (`unknown_hold_requires_reconciliation`); only `reconcile_unknown(..., evidence_ref=...)` (non-empty) clears it. Unknown is never treated as zero.
- V20-E04: `src/swarm/pursuit/durable_accounting.py` — `HoldStore` (memory + SQL over `v20_goal_usage_holds`), `bind_durable_ledger` (restore, persist-before-visible, rollback on failure), `LessonPersistence` (memory + SQL over `v20_pursuit_lessons`).
- `src/swarm/pursuit/learning.py`: `PursuitLessonStore(persistence=None)` keeps today's behaviour without the argument. Not wired into `api/store.py`/`pursuit/loop.py` (SW-W3-S2).
- Tests: `tests/pursuit/test_v20_unknown_usage_budget.py`, `tests/pursuit/test_v20_durable_holds.py`, `tests/integration/db/test_v20_holds_sql.py`. No existing test encodes F-13 (`tests/pursuit/test_usage_accounting.py` unchanged and passing).
## Verification
Checks run by `/agent/wt/check.sh` on commit `9fca17c9a040fcfdec42de618911cc7a12dbf0ae` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 249 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 10 passed in 0.48s
offline CI: 593 passed, 3 skipped in 27.13s
integration (Postgres): 85 passed in 20.21s
tree: a9da38c4e9f969467181b5bfd1e161e9a5a98528 dirty=0
```

## Acceptance
- [x] After an unknown settle, `remaining()` still subtracts `max(reserved, reported)`, and a reserve that needs the freed amount fails with `insufficient_spend_budget`.
- [x] `release()` of an unknown hold raises `unknown_hold_requires_reconciliation`; `reconcile_unknown` requires a non-empty `evidence_ref`.
- [x] Holds, including unknown holds, and lessons survive a cold restart through the store (both in-memory and PostgreSQL).
- [x] A persistence failure leaves in-memory ledger and lesson state unchanged, and the error propagates.
- [x] With no store or persistence, behaviour is unchanged apart from the F-13 fix.
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c` (isolation from concurrent agents).
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
