# SW-W3-S4 handoff
- Branch: `cursor/sw-w3-s4-460c`   Base SHA: `7209b18c6a107556da6275f301449f7b1a309b82`   Head SHA (code): `4f5b4d757e08c31bdd9331158fcb11c906a2f1e1`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W3-S4.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/acceptance/v23_probes.py`: ten deterministic probes V23-A01…A10 bound to `benchmarks/v23_acceptance/scenarios.freeze.json`, driving the real V2.3 services in-process with fake brokers and injected clocks; `load_v23_freeze` fails closed (schema ≠ 2.3.0, policy_version mismatch, missing `version_claim_policy`, unknown probe or duplicate ids); a raising probe counts as `error:<Type>` failure; `version_claim` is always `not_accepted_by_harness`. V23-A11 (multi-process/private) has no probe → `pending_owner_approval`.
- `tests/acceptance/test_v23_acceptance.py` (15).
## Verification
Checks run by `/agent/wt/check.sh` on commit `4f5b4d757e08c31bdd9331158fcb11c906a2f1e1` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 256 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 39 passed in 2.88s
offline CI: 672 passed, 1 skipped in 36.92s
integration (Postgres): 88 passed in 22.09s
tree: 6e57c1accdd33042a99b458653db6b73feff1007 dirty=0
```
- `run_v23_probes(tmp)` → `10 10 not_accepted_by_harness` (all ten probes `pass`), run from the repository root.
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
- Tests ran against the private Postgres DB `swarm_sw460c`. No probe check was loosened.
## Needs other owner
none
## Follow-ups
- Known limitation (not fixed here, per prompt): a non-admit decision has no task, so its `scheduler.decision` ops event carries `project_id=None` and appears only in the admin (site-wide) view; probe A09 therefore queries by `kind`.
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
