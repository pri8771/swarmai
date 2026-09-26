# SW-W3-S1 handoff
- Branch: `cursor/sw-w3-s1-460c`   Base SHA: `94cdc07bda84e8876a30ddfe1a317fd11aafae39`   Head SHA (code): `b52fdc424202f18503dfe59f6a4e8d7e899b292d`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W3-S1.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/api/routes_v23.py`: scheduler (queues, receipts, project upsert/weight/pause/resume), ops trace, packs (install/enable/drain/disable/uninstall/revoke/history), portability export/import, fleet place/audit, worker drain/revoke by path — shapes exactly as frozen in the plan.
- Security: every route resolves a `Principal`; `auth.require_project` before reads/writes; admin-only for pack admin ops, fleet audit, unscoped receipts, fleet-level workers; non-admin queues show own projects only; foreign trace → 404; import checks target and source projects and `bundle_id` against `^port_[A-Za-z0-9_-]{1,64}$`; pack registry `require_signature=True, trusted_keys=trusted_keys_from_env()`; API runtime never dispatches (reserve raises `api_runtime_has_no_broker`); every mutation emits a redacted `operator.action` event with the actor.
- `src/swarm/api/app.py` (base unchanged from `8e1c0fde`): `routes_v23` imports, `OpsEventLog, SqlOpsSink`, `app.state.v23` factory block, `include_router(v23_router)`. Durable stores only with `SWARM_V23_DURABLE=1` and a reachable DB (default off).
- Tests: `tests/api/test_v23_routes.py` (7), `tests/integration/db/test_v23_routes_durable_sql.py` (1).
## Verification
Checks run by `/agent/wt/check.sh` on commit `b52fdc424202f18503dfe59f6a4e8d7e899b292d` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 254 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 42 passed in 4.25s
offline CI: 642 passed, 1 skipped in 36.28s
integration (Postgres): 87 passed in 22.68s
tree: 6488bc2de6c2519196c5fd827506443d5da7c09c dirty=0
```
- First full offline run on this commit: `1 failed, 641 passed, 1 skipped` — the failure was `tests/tools/test_v20_cancel_killbound.py::test_cancel_kills_group_before_timeout` ("grandchild survived the kill bound"), a SW-W1-S13 test outside this session's files. It passes 8/8 in isolation and passed on the immediate re-run (result above) and in every other full run so far; recorded as an intermittent flake for SW-W1-S13 review, not worked around.
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
- Tests ran against the private Postgres DB `swarm_sw460c`. `SWARM_V23_DURABLE` stays off by default.
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
