# SW-W1-S3 handoff
- Branch: `cursor/sw-w1-s3-460c`   Base SHA: `7ee30ef3b1594d70056c0a60235efadf7bced929`   Head SHA (code): `05db8f814c2cb57ac0f1c562a1e6e7cc7fec255b`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S3.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/scheduling/dispatch_intent.py`: `DispatchIntent` reservation/compensation service over injected `reserve`/`release` callables and any `SchedulingStore`; idempotent per `attempt_id`, TTL, fail-closed compensation, `recover_expired` releases expired PREPARED/RESERVED exactly once and never touches DISPATCHED.
- `tests/controller/test_v23_dispatch_intent.py`: 7 tests (partial reservation failure releases earlier ones, crash-before-dispatch recovery, duplicate prepare does not re-reserve, …).
## Verification
Checks run by `/agent/wt/check.sh` on commit `05db8f814c2cb57ac0f1c562a1e6e7cc7fec255b` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 242 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 7 passed in 0.10s
offline CI: 549 passed, 3 skipped in 27.18s
integration (Postgres): 79 passed in 16.89s
tree: ce9483f0a95805786954a66b730c58cd1049322d dirty=0
```

## Acceptance
- [x] Partial reservation failure releases every earlier reservation (pathological case: "partial provider reservation succeeds but worker reservation fails").
- [x] Crash after reserve, before dispatch: `recover_expired` releases exactly once and never touches `DISPATCHED` (pathological case: "scheduler crashes after reservations but before dispatch").
- [x] A duplicate `prepare` for the same attempt does not reserve again (pathological case: duplicate ticks).
- [x] 7 tests pass.
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
