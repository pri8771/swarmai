> **EXECUTED** 2026-09-26 by the integrator: branch `cursor/sw-fix-alembic-isolation-460c` head `412679129d013033ee8658e6c747fba1ed8a9feb` (code `ebebadf4`), merged into `cursor/sw-v23-integration-460c` at `604f7acec2c560cffa39bafd87ab9284e4b9a565`. Whole-repo `uv run pytest -q`: `778 passed, 1 skipped` (was `4 failed`).

**Goal.** A whole-repo `uv run pytest -q` against a private database failed 4 Alembic schema tests (`test_single_alembic_head_after_upgrade`, `test_alembic_upgrade_empty_db`, `test_alembic_upgrade_preserves_populated_legacy_rows`, `test_upgrade_downgrade_upgrade`). Make the run pass without weakening assertions.

### Step 0 — find the cause (do not assume)
Trace `os.environ.get("SWARM_DATABASE_URL")` after every test with a throwaway pytest plugin (`pytest_runtest_logfinish`) loaded through `PYTHONPATH` and `-p`. Observed: the variable disappears after `tests/acceptance/test_campaign_harness.py::test_campaign_runs_all_frozen_scenarios`. The cause is `src/swarm/acceptance/probes.py::probe_sdk_ui_parity` (V20-S11), which pops every `SWARM_*` key. `migrations/env.py` reads `database_url()` at run time, so Alembic then migrated the **default** `swarm` database while the tests inspected the private one.

### Step 1 — `src/swarm/acceptance/probes.py`
Rename the body to `_probe_sdk_ui_parity(tmp)`. `probe_sdk_ui_parity` snapshots `SWARM_*`, calls it, and in `finally` removes any `SWARM_*` key and restores the snapshot.

### Step 2 — `tests/integration/db/conftest.py` (create)
Autouse fixture: `monkeypatch.setenv("SWARM_DATABASE_URL", request.module.DATABASE_URL)` when the module defines `DATABASE_URL`.

### Step 3 — regression test
Append `test_sdk_ui_parity_probe_restores_swarm_env` to `tests/acceptance/test_campaign_harness.py` (fails before Step 1: `1 failed, 11 passed`).

### Step 4 — whole-repo run
With `SWARM_DATABASE_URL` set to your private DB: both changes `778 passed, 1 skipped`; each change alone closes the 4 failures.

### Acceptance (this session)
- [ ] Whole-repo `uv run pytest -q` passes against a private DB.
- [ ] No assertion removed or loosened.
