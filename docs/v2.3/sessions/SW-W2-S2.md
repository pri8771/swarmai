# SW-W2-S2 handoff
- Branch: `cursor/sw-w2-s2-460c`   Base SHA: `1edd99f50b3309e2be9e5b0f072dc5e95340518c`   Head SHA (code): `f866fb50e6bcae6f3bf98224f99a1e39d54adc99`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W2-S2.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/pursuit/native_loop.py`: bounded native model/tool loop through `RouterClient` (W1-S11); hard bounds on turns, model calls and tool calls; only allow-listed tools execute; any router error stops and is recorded (no retries); missing usage → `usage_known=False`.
- `src/swarm/pursuit/native_dispatch.py` (base was unchanged from `8e1c0fde`): the live path needs a ready `LiveGrant` + `SWARM_ROUTER_BASE_URL` + `SWARM_ROUTER_MODEL`; otherwise an honest blocker (`router_not_configured`, `router_model_not_configured`, or preflight reason such as `missing_live_grant`). Never invents success: outcome stays `submitted_pending`; `plan["native_loop"]` + `native_loop.<status>` timeline entry.
- `tests/pursuit/test_v20_native_loop.py` (8) using the offline `FakeRouter`; no network.
## Verification
Checks run by `/agent/wt/check.sh` on commit `f866fb50e6bcae6f3bf98224f99a1e39d54adc99` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 253 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 8 passed in 0.79s
offline CI: 635 passed, 1 skipped in 33.41s
integration (Postgres): 86 passed in 21.59s
tree: 48524cef2f3560c50aef7197a479c0ed7040a322 dirty=0
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
- Tests ran against the private Postgres DB `swarm_sw460c`. No live router call was made (no LiveGrant).
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
