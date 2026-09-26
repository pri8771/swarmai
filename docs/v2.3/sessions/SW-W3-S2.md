# SW-W3-S2 handoff
- Branch: `cursor/sw-w3-s2-460c`   Base SHA: `12c54026d1d941352bca1d678684c57453b6da15`   Head SHA (code): `72794fd506edd885733613cf4b5fa0bcd56aec5a`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W3-S2.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- Applied the exact source patch (`git apply --check` clean) to `src/swarm/api/store.py` and `src/swarm/pursuit/loop.py`.
- V20-E03: `ProductStore.pursuit_engine()` uses `DurablePursuitStateStore(root, mirror=PursuitPgMirror(factory))` when durable.
- V20-E04: `PursuitEngine(hold_store=SqlHoldStore(factory))` restores holds via `bind_durable_ledger`; `PursuitLessonStore(persistence=SqlLessonPersistence(factory))` restores lessons.
- V20-E06: `PursuitEngine.tick_all_due()` (ACTIVE/WAITING due goals in goal-id order), `PursuitEngine.singleton_tick(ticker)`, and `ProductStore.run_pursuit_tick()` using epoch row `site_id="pursuit-ticker"`.
- Gating: PostgreSQL only when `SWARM_V23_DURABLE=1` and `db_reachable is True`; otherwise `pg_session_factory()` returns `None` and file state under `var/` stays authoritative. Default off; `.env.example`/compose untouched.
- Tests: `tests/product/test_v20_durable_wiring.py` (6), `tests/integration/db/test_v20_durable_wiring_sql.py` (1).
## Verification
Checks run by `/agent/wt/check.sh` on commit `72794fd506edd885733613cf4b5fa0bcd56aec5a` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 254 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 96 passed in 4.15s
offline CI: 648 passed, 1 skipped in 35.39s
integration (Postgres): 88 passed in 22.61s
tree: 4cab570e7a62327c4368452cfd46d30296f8bbe8 dirty=0
```

## Acceptance
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
