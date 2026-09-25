# V1.7 fake-upstream native mission + LiveGrant gate

**Date:** 2026-09-25  
**Hostname:** `swarm.splitsignal.ai`  
**Spend:** $0 — **no invented LiveGrant approval**

## Fake upstream E2E

- `FakeProviderAdapter` + `FakeInferenceBroker` invoke on `rt_fake_alpha`
- Artifact CAS + `protected_review` (worker forged checks ignored)
- Evidence: `fake-e2e.json` (written by script/tests)

## LiveGrant gate (prepared, blocked)

Pinned: `docs/evidence/v17/live-grant-gate.json`

| Field | Value |
|---|---|
| approved | **false** |
| budget_usd | 0 |
| free_routes_only | true |
| ceilings | max_calls/tokens/wall set |
| invented_approval | false |
| blocked | true |

Live dispatch remains blocked until an operator approves a real grant.

## Commands

```sh
uv run pytest tests/evals/test_v17_fake_e2e_live_grant.py -q
uv run python scripts/v17_fake_e2e_live_grant.py
```
