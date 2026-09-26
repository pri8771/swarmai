# SW-W1-S6 handoff
- Branch: `cursor/sw-w1-s6-460c`   Base SHA: `133ab3529f304d5aa544de87635fb80a56dfccf2`   Head SHA (code): `cd7190ccee0c43feb866e818a5dd509996ed2538`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S6.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/product/portability.py`: bundle schema 2 with `history`, `receipts`, `approvals`, `leases`, `artifact_digests` sections (per-section digests); approvals/leases tombstoned (`executable: false`); `min_reader` compatibility; `target_project_id` remap with `remapped_from`; value-based secret scan over every string with strict `^env:[A-Z_][A-Z0-9_]*$` references (F-03). Schema-1 bundles still import.
- `tests/portability/test_v23_bundle.py` (7). Existing portability and `test_v23_v20.py` tests pass unchanged.
## Verification
Checks run by `/agent/wt/check.sh` on commit `cd7190ccee0c43feb866e818a5dd509996ed2538` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 246 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 7 passed in 0.23s
offline CI: 569 passed, 3 skipped in 26.87s
integration (Postgres): 81 passed in 20.36s
tree: 772ac1ff9daf4c25b1ee3d423485ad086ec0309f dirty=0
```

## Acceptance
- [x] Secret values are caught anywhere (config, history, receipts); `env:` references must match `^env:[A-Z_][A-Z0-9_]*$`.
- [x] Round-trip into a clean directory verifies the integrity and section digests; imported approvals and leases are non-executable tombstones.
- [x] Tampered sections, injected `executable: true` and incompatible `min_reader` are rejected.
- [x] Remap rewrites `project_id` in sections and records `remapped_from`.
- [x] Schema-1 bundles still import.
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
