# SW-W4-S1 handoff
- Branch: `cursor/sw-w4-s1-460c`   Base SHA: `10fd924efd866fbaa8ce7348b24aad3019a13ecc`   Head SHA (code): `ead39ccf92cdc80afa51df2183c0a6a07857fc0e`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W4-S1.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- F-14: `CURRENT_SCHEMA_REVISION = "a23opsplatform0001"` in `src/swarm/release/candidate.py` (one head confirmed); the three `"a18tov30schema0001"` literals in `cli.py` (2) and `routes_v1.py` (1) replaced; `tests/release/test_schema_revision.py` pins it to the Alembic head.
- F-16: `POST /v1/release/candidate-freeze` is admin-only (`forbidden_admin`, 403).
- `scripts/v23_acceptance_campaign.py` added and run on code commit `723f6e55`; evidence `docs/evidence/v23/acceptance_campaign.json`: deterministic `pass` 10/10; `multi_process_private: pending_owner_approval`; `live_router_free_route: blocked:router_not_configured` (no router/SplitSignal env, no LiveGrant — nothing was set to make it green); `compose_smoke_v20_e10: fail`; `durable_postgres_flag: false`; `version_claim: not_accepted_by_harness`.
- `docs/v2.3/EXIT_CHECKLIST.md` filled from the campaign (items 1–15 done with cited tests, item 16 pending; SplitSignal adapter `pending: SW-X1-S1 not merged (gate SP1)`; V20-E10 **not done**, gate fail).
- Status/agent docs: `docs/v2.3/STATUS.md` (candidate, NOT accepted, gates, not-claimed list), `docs/v2.0/STATUS.md`, `docs/agents/CURRENT.md`, `context.json` (valid JSON), `RESUME.md`, `V20_TODO.md`, `CHANGELOG.md` (new top section), `README.md` (F-12 label + V2.3 operator pointer).
## Verification
Checks run by `/agent/wt/check.sh` on commit `ead39ccf92cdc80afa51df2183c0a6a07857fc0e` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 256 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 64 passed in 3.53s
offline CI: 675 passed, 1 skipped in 37.27s
integration (Postgres): 88 passed in 20.99s
tree: e652c397df6ede051f6de965df9e9d20b1f58d83 dirty=0
```
- Whole-repo `uv run pytest -q` (informational): `4 failed, 759 passed, 1 skipped`. The 4 are Alembic schema tests (`test_action_receipts_durable.py::test_single_alembic_head_after_upgrade`, `test_lease_fencing_schema.py::test_alembic_upgrade_empty_db`, `::test_alembic_upgrade_preserves_populated_legacy_rows`, `test_v23_schema.py::test_upgrade_downgrade_upgrade`), which fail only when offline tests (`tests/workers`, `tests/knowledge` `drop_all/create_all`) share the DB in one run. Baseline `origin/dev@8e1c0fde` reproduces the first three the same way (`3 failed, 576 passed, 3 skipped`); all pass in the separate integration run above (the CI layout).
- Console: `npx vitest run` → `Tests 26 passed (26)`; `npx oxlint src` → 0 errors, pre-existing warnings only.
- `grep -rn a18tov30schema0001 src/swarm/cli.py src/swarm/api/routes_v1.py` → nothing; `python3 -m json.tool docs/agents/context.json` → JSON_OK; false-accept grep → `NO_FALSE_ACCEPT_CLAIMS` (remaining hits are negative statements in other sessions' handoffs).
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
- V20-E10 is left **open** (the prompt says to tick E03–E06 and E08–E10, but the E10 smoke gate is `fail`); E07 = implemented, live blocked.
- No GitHub PRs could be opened from this environment, so V20_TODO cites session branches instead of PR links.
- The template's nonexistent `docs/architecture/ART-V23-SCHEDULER-CONTRACTS.md` reference was replaced with `src/swarm/contracts/v23.py` + `docs/artifacts/future/ART-V23-MULTIMISSION_SCHEDULER.md`.
- `pause: false` / `v20_work` kept as recorded by SW-W0-S1 (owner's V2.3 request).
## Needs other owner
- `deploy/compose/product.yml` `worker`: disable the inherited API HEALTHCHECK (V20-E10 follow-up from SW-W3-S5).
- `src/swarm/broker/retry.py`: give up instead of retrying at the 30 s cap when `Retry-After` exceeds it (SplitSignal contract; from SW-X1-S1).
- Test isolation: offline tests in `tests/workers/` and `tests/knowledge/` should not `drop_all` the database the Alembic integration tests use (pre-existing whole-repo run failures).
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)

## Follow-up (after merge)
The three "Needs other owner" items and the SW-W1-S13 flake were fixed by SW-FIX-RETRY (`b3162712`), SW-FIX-COMPOSE (`e5fd04c0`), SW-FIX-ALEMBIC (`604f7ace`), SW-FIX-FLAKE (`1b3f48ad`) (handoffs in this directory). Campaign re-run on `1b3f48ad`: deterministic `pass` 10/10, `compose_smoke_v20_e10: pass`, other gates unchanged. Whole-repo `uv run pytest -q` (private DB): `778 passed, 1 skipped` — the 4 Alembic failures above were caused by the V20-S11 probe clearing `SWARM_DATABASE_URL`, not by `drop_all` in offline tests. Status: implemented / offline-tested.
