# SW-W1-S1 handoff
- Branch: `cursor/sw-w1-s1-460c`   Base SHA: `c0c120968ea50344195b1d9b4d58e9870c5590fd`   Head SHA (code): `4c21931c21f5a7a8648df125fb7317b7847ed234`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S1.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/scheduling/wdrr.py`: pure weighted-deficit round-robin selector (project → mission → task), policy from `config/v23/scheduler_policy.v1.json`; no I/O, `now` injected, inputs not mutated.
- `tests/controller/test_v23_wdrr.py`: 15 tests (weight-proportional share ±15% over 600 decisions, no mission amplification, no starvation, blocked work earns no credit, stale cancellation generation excluded, paused/draining/capped reason codes, DEFER on resource-unavailable, determinism, bounded urgent bonus, deadline tie-break, task order, restart clamp).
- `wdrr.py` imports nothing from `swarm.db`, `swarm.api` or I/O modules.
## Verification
Checks run by `/agent/wt/check.sh` on commit `4c21931c21f5a7a8648df125fb7317b7847ed234` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 240 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 15 passed in 0.23s
offline CI: 542 passed, 3 skipped in 28.16s
integration (Postgres): 70 passed in 16.92s
tree: 8f6840452b5f08810654be1e315f3a6a8b2e6d5f dirty=0
```

## Acceptance
- [x] 15 tests pass, covering: weight-proportional share within ±15% over 600 decisions; no amplification from more missions; low weight not starved; blocked work earns no credit; stale cancellation generation never selected; paused, draining and capped work excluded with reason codes; resource-unavailable gives DEFER; deterministic output with inputs unchanged; urgent bonus bounded; deadline tie-break; task order; restart clamp.
- [x] `wdrr.py` imports nothing from `swarm.db`, `swarm.api` or any I/O module.
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
