# SW-FIX-ALEMBIC handoff
- Branch: `cursor/sw-fix-alembic-isolation-460c`   Base SHA: `e5fd04c00028b7e89ae749da7d2966ef742bea74`   Head SHA (code): `ebebadf459704a7f51ffaccb3ab461b8a1fda0e9`
- PR: to `cursor/sw-v23-integration-460c` (PR body `pr_bodies/SW-FIX-ALEMBIC.md` in the coordinator audit dir).
## Problem
Whole-repo `uv run pytest -q` against a private DB: `4 failed, 773 passed, 1 skipped` (`test_action_receipts_durable.py::test_single_alembic_head_after_upgrade`, `test_lease_fencing_schema.py::test_alembic_upgrade_empty_db`, `::test_alembic_upgrade_preserves_populated_legacy_rows`, `test_v23_schema.py::test_upgrade_downgrade_upgrade`), e.g. `assert 'action_receipts' in set()` right after `command.upgrade(cfg, "head")`.
## Root cause (differs from the earlier "offline tests wipe the DB" theory)
- `src/swarm/acceptance/probes.py::probe_sdk_ui_parity` (V20-S11) did `os.environ.pop` for every `SWARM_*` key and never restored them. Found by tracing `SWARM_DATABASE_URL` after each test: it disappears after `tests/acceptance/test_campaign_harness.py::test_campaign_runs_all_frozen_scenarios`.
- The schema modules bind `DATABASE_URL` at import (private DB), but `migrations/env.py` calls `database_url()` at run time, which then fell back to the default `…/swarm`. Alembic migrated the **shared default database** while the test inspected the private one. Side effect: every whole-repo run on a host with the default DB altered that DB.
## Done
- `probes.py`: `probe_sdk_ui_parity` snapshots `SWARM_*`, runs the unchanged body (`_probe_sdk_ui_parity`), and restores the caller's `SWARM_*` in `finally`.
- `tests/integration/db/conftest.py`: autouse fixture pins `SWARM_DATABASE_URL` to the module's `DATABASE_URL` (monkeypatch), so Alembic always migrates the database the test asserts on.
- `tests/acceptance/test_campaign_harness.py::test_sdk_ui_parity_probe_restores_swarm_env`: fails before the fix (`1 failed, 11 passed`), passes after.
- No assertion was removed or loosened.
## Verification (private DB `swarm_fix460c`)
- Whole-repo `uv run pytest -q`: both changes `778 passed, 1 skipped`; probe fix only `778 passed, 1 skipped`; conftest only `1 failed, 777 passed, 1 skipped` (only the new probe regression test). The skip is `tests/portability/test_two_container_compose.py` (needs `SWARM_PORTABLE_DOCKER=1`).
- `/agent/wt/check.sh` on `ebebadf4`: ruff pass; mypy `Success: no issues found in 256 source files`; one head `a23opsplatform0001`; session `53 passed`; offline CI `690 passed, 1 skipped`; integration (Postgres) `88 passed`.
## Status
implemented / offline-tested (NOT accepted; needs independent Codex review)
