# TEST-HYGIENE-01 — the test suite no longer mutates tracked files

Finding 3 of the 2026-09-22 handoff: running `pytest` re-froze `schemas/v1/*` in place and rewrote `docs/evidence/fix-004/*`, so "commit source before evidence" required a manual `git checkout --` after every run.

## Changes
- `tests/release/test_v1.py::test_contract_freeze` freezes into a temporary copy of `schemas/contracts` and asserts the tracked `schemas/v1/product_contract.v1.json` is byte-identical afterwards. `freeze_public_contracts` itself is unchanged (the release CLI still writes into the real tree on purpose).
- `scripts/hourly/checkin.py`: honours `SWARM_HOURLY_REPO_EVIDENCE=0` (skip the in-repo evidence copy; the Application Support mirror is unchanged); the entry records `repo_evidence_skipped: true`. Default behaviour for the LaunchAgent is unchanged.
- `tests/regressions/test_hourly_runner.py` sets that variable and asserts `docs/evidence/fix-004/last-checkin.json` is untouched.

## Checks
- `uv run pytest tests/release tests/regressions -q` → 29 passed.
- Full suite → see `verify-receipt.json`; `git status --short` after the run shows only the three edited files (no evidence/schema churn).
