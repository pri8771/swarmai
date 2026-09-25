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
| pytest `tests/mission/test_v17_protected_verify.py` | pass |
| pytest `tests/workers/test_continuous_connector.py` | pass |

## Not yet (genuine remaining work)

| Item | Blocker / next |
|---|---|
| Continuous outbound connector lease loop | **Lane A landed** — see `docs/evidence/v17/continuous-connector/SUMMARY.md` |
| ≥1 authorized native model-backed end-to-end mission | needs free route grant or fake-upstream adapter |
| Collaborative mission + context handoff evidence | V1.7 remaining (other lane) |
| Full V1.8 pause/resume/cancel/restart Goal proofs beyond unit | expand |
| V1.9 autonomous pursuit loop | after V1.7/1.8 |
| V2.0 product UI/SDK acceptance campaign | after V1.9 |
| R730 / DNS / CF / Linear | external gates |

## Commands

```sh
uv run pytest tests/mission/test_v17_protected_verify.py tests/foundation -q
```
