# SW-W0-S2 handoff
- Branch: `cursor/sw-w0-s2-460c`   Base SHA: `dd134248dad645f00a80b384d7fe8da6b3619e02`   Head SHA (code): `d7d341e258fd9648b1a25debc9c13e9f730a18cb`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W0-S2.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/contracts/v23.py` (shared V2.3 contracts), `src/swarm/scheduling/__init__.py`, `src/swarm/scheduling/memory_store.py` (in-memory reference store) created verbatim from the prompt.
- Appended the V2.3/V2.0 ORM rows to the end of `src/swarm/db/models.py` (append-only diff). New tables: `v23_project_queue_state`, `v23_mission_queue_state`, `v23_scheduler_receipts`, `v23_dispatch_intents`, `v23_scheduler_epochs`, `v23_pack_installs`, `v23_ops_events`, `v20_goal_usage_holds`, `v20_pursuit_lessons`.
- Single migration `a23opsplatform0001` (down_revision `a20pursuitpersist0001`); `alembic heads` prints exactly one head.
- `tests/integration/db/test_action_receipts_durable.py`: only `NEW_HEAD` changed to `a23opsplatform0001`.
- Tests: `tests/contracts/test_v23_contracts.py`, `tests/controller/test_v23_store_memory.py`, `tests/integration/db/test_v23_schema.py` (upgrade → downgrade → upgrade).
- Contracts frozen; later sessions import only. Field changes need a follow-up PR from the coordinator.
## Verification
Checks run by `/agent/wt/check.sh` on commit `d7d341e258fd9648b1a25debc9c13e9f730a18cb` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 239 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 14 passed in 3.41s
offline CI: 517 passed, 3 skipped in 28.15s
integration (Postgres): 70 passed in 18.53s
tree: 0a34deabf6421ef70c4eb31ae9aab7681207a890 dirty=0
```

## Acceptance
- [x] `uv run alembic heads` prints exactly `a23opsplatform0001 (head)`.
- [x] `uv run python -c "import swarm.contracts.v23, swarm.scheduling.memory_store"` succeeds.
- [x] The 7 new offline tests pass; `test_v23_schema.py` passes (upgrade → downgrade to `a20pursuitpersist0001` → upgrade).
- [x] `models.py` diff is append-only (`git diff src/swarm/db/models.py` shows only `+` lines at the end).
- [x] Handoff lists the 9 new table names and says: "Contracts frozen; later sessions import only. Field changes need a follow-up PR from the coordinator."
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no real network calls, no `accepted`/`complete` claims.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c` (isolation from concurrent agents).
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
