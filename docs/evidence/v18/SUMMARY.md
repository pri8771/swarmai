# V1.8 Goal lifecycle campaign evidence

**Date:** 2026-09-25  
**Lane:** C — durable Goal entity  
**Branch:** `cursor/v18-goals-lifecycle-614f` @ `c8f93d42`  
**Base:** `origin/dev` @ `748078f2` (extended; not rewritten)  
**Status:** eng_verified (deterministic) — **not** operator-accepted

## Objective

Prove persistent Goal entity above missions with required fields, state machine, finite vs ongoing semantics, pause/resume/cancel/restart recovery, duplicate-trigger handling, and retained decision history across cold reopen. Mission completion must not imply goal achievement.

## Protected tests

| Suite | Result |
|---|---|
| `tests/goals/test_v18_goal_lifecycle.py` | 7 passed |
| `tests/mission/test_v17_protected_verify.py` (Goal section retained) | 4 passed (file total) |
| Combined | **11 passed** |

Commands:

```bash
uv run ruff check src/swarm/goals src/swarm/api/schemas.py src/swarm/api/routes_v1.py tests/goals
uv run mypy src/swarm/goals src/swarm/api/schemas.py
uv run pytest tests/goals/test_v18_goal_lifecycle.py tests/mission/test_v17_protected_verify.py -q
```

## Campaign matrix

| Scenario | Result | Notes |
|---|---|---|
| Required Goal fields present | pass | outcome, criteria, scope, constraints, envelopes, owner/agents, strategy, deps, stop/expiry/cadence, progress, decision history |
| Transition matrix | pass | terminal states closed except explicit restart |
| Finite vs ongoing | pass | ongoing cannot transition to `achieved` |
| Mission ≠ achievement | pass | mission-outcome leaves goal `active`; API flag false |
| Pause / resume | pass | store + API |
| Cancel | pass | terminal; illegal transition to active without restart |
| Restart recovery | pass | history + restart_count retained; blockers cleared |
| Duplicate trigger | pass | same dedupe_key returns prior receipt with `duplicate=true` |
| Expiry | pass | `expires_at` → `expired`; restart revived |
| Cold reopen | pass | new GoalStore / new API app recovers identical history |
| Persistence schema | pass | `var/goals/goals.json` schema_version `1.8` |

## Artifacts

- `docs/evidence/v18/goal_lifecycle_campaign.json` — machine-readable summary
- Source: `src/swarm/goals/models.py`, API routes under `/v1/goals*`

## Non-claims

- Not V1.9 pursuit loop
- Not V2.0 UI/SDK
- Not live/model-backed qualification
- Not operator acceptance / independent review sign-off
- Linear MCP still needsAuth — queued in `docs/swarm-mvp/LINEAR_RECONCILIATION.md`
