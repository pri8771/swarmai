# V1.7 progress evidence

**Date:** 2026-09-25  
**Branch tip (pre-push):** see git  
**Hostname:** `swarm.splitsignal.ai`

## Delivered this increment

| Item | Status |
|---|---|
| Server protected extract verifier (ignores worker checks) | done |
| HTTP review path uses protected verifier + artifact bytes | done |
| Goal entity + durable store + API (create/list/get/transition/link) | done (V1.8 foundation) |
| Continuous Mac connector claim/renew/submit/cancel/reconnect | **done (Lane A)** |
| Collaborative mission + X→Y handoff via continuous connector | **done (Lane A residual)** |
| Fake-upstream native E2E + LiveGrant gate record (no spend) | **done (Lane A residual)** |
| pytest `tests/mission/test_v17_protected_verify.py` | pass |
| pytest `tests/workers/test_continuous_connector.py` | pass |
| pytest collab + fake-e2e suites | pass |

## Not yet (genuine remaining work)

| Item | Blocker / next |
|---|---|
| ≥1 authorized **live** native model-backed mission | LiveGrant prepared, **not approved** — no spend |
| R730 two-host qualification | external gate |
| Full V1.8 / V1.9 / V2.0 | other lanes |
| R7 CI / Linear | other lanes / needsAuth queue |

## Commands

```sh
uv run pytest tests/mission/test_v17_protected_verify.py tests/foundation -q
```
