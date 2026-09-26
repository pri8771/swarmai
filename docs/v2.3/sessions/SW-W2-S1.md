# SW-W2-S1 handoff
- Branch: `cursor/sw-w2-s1-460c`   Base SHA: `97c20078f18e5a5bae8a5956686b31e5adda3ee2`   Head SHA (code): `887010cebd05bb13a85eee75c131565588e2b603`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W2-S1.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/scheduling/service.py`: `SchedulerService`, the single dispatch authority composing WDRR (W1-S1), `SchedulingStore` (W0-S2/W1-S2), `DispatchIntentService` (W1-S3), `SchedulerEpochService` (W1-S4), `SiteAuthorityService`, `OpsEventLog` (W1-S8). One decision per `schedule_once`; non-holders get `DENY / stale_scheduler_epoch` and write nothing; duplicate `attempt_id`s dropped; failed reservation → `DEFER / reservation_failed` with full compensation and no credit change; `running` == non-terminal intents; `recover()` expires, clamps, recounts; `finish()` fenced on stale generation / site epoch / scheduler epoch.
- `src/swarm/controller/resource_allocator.py`: optional `scheduler=` routes through the service; without it the legacy path is unchanged (`tests/controller/test_v23_v20.py` passes).
- Tests: `tests/controller/v23_harness.py` (helper), `tests/controller/test_v23_service.py`, `tests/controller/test_v23_pathological.py` (11 ART pathological cases `test_01`…`test_11`), `tests/integration/db/test_v23_service_restart_sql.py` (restart on PostgreSQL: credit preserved/clamped, crashed intent expired and released, new holder epoch 2).
## Verification
Checks run by `/agent/wt/check.sh` on commit `887010cebd05bb13a85eee75c131565588e2b603` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 252 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 18 passed in 1.96s
offline CI: 627 passed, 1 skipped in 35.73s
integration (Postgres): 86 passed in 21.58s
tree: 7e2b81d7f193d9aaec58031794d8f50c75ac9119 dirty=0
```

## Acceptance
- [x] All 11 ART pathological cases pass (`test_01` … `test_11`), each named after its ART bullet.
- [x] With equal weights the share is within ±15% after 200 decisions; with weights 3:1 the share is within ±15% of 75% and the light project is never starved.
- [x] Every decision (admit, defer, idle, or deny for a stale site) has exactly one receipt with a monotonic `sequence`; fenced non-holders write none.
- [x] Restart on PostgreSQL preserves credit (positive side clamped), expires the crashed intent, releases its reservation, and the new holder gets epoch 2.
- [x] The legacy `ResourceAllocator` path is unchanged; with `scheduler=` it produces an `admit` receipt.
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c`. Dependency signatures matched; no STOP.
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
