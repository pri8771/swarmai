# SW-W1-S7 handoff
- Branch: `cursor/sw-w1-s7-460c`   Base SHA: `d80ac0e97fcc9171e3ea694d567060fb595325b7`   Head SHA (code): `ce016e41ff1f7cda69ed577637f86478b8594569`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S7.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/workers/fleet.py`: ART trust classes (`observe_only` < `sandbox_compute` < `model_worker` < `tool_worker` < `integration_worker`) with `LEGACY_TRUST_ALIASES`; drain state machine (active → draining → drained; revoked terminal); deterministic least-privilege placement (lowest sufficient rank, then lowest `worker_id`); per-project trust ceiling; strict locality; DRAINING/QUARANTINED/OFFLINE registry workers refused. Public API preserved.
- `tests/workers/test_v23_fleet_policy.py` (6). No existing test asserts a legacy output `trust_class`.
## Verification
Checks run by `/agent/wt/check.sh` on commit `ce016e41ff1f7cda69ed577637f86478b8594569` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 246 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 6 passed in 0.12s
offline CI: 575 passed, 3 skipped in 27.84s
integration (Postgres): 81 passed in 21.03s
tree: 779e8a0da6483ee9f71ad7157a094b7b84b18316 dirty=0
```

## Acceptance
- [x] `normalize_trust("code_write") == TrustClass.TOOL_WORKER` and the other 3 legacy aliases map as documented; unknown names raise `FleetError`.
- [x] With two eligible workers, placement picks the lowest sufficient trust class and then the lowest `worker_id`, and the result is the same on every run.
- [x] Draining, drained and revoked workers get no new work; `revoked` cannot transition back.
- [x] A worker drained via `registry.operator_drain` is not placed.
- [x] A project trust ceiling below the required class denies placement.
- [x] Locality is strict.
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
