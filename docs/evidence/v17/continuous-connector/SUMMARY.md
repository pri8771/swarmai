# V1.7 continuous Mac connector (Lane A / R2)

**Date:** 2026-09-25  
**Branch:** `cursor/v17-connector-continuous-b28d`  
**Hostname:** `swarm.splitsignal.ai`  
**Spend:** $0

## What landed

| Item | Status |
|---|---|
| HTTP `/v1/workers/claim|renew|submit-result|cancel-lease|reconnect|enqueue` | done |
| Registry leases with durable `var/workers/registry.json` (queue + leases + results) | done |
| Continuous connector loop (not one-shot TH-03) | done |
| Compose `mac-connector.yml` → continuous entrypoint | done |
| Submit never self-accepts (`acceptance_state=pending`) | done |
| Cancel fences submit; reconnect/reconcile recovers leases | done |
| Protected pytest | pass |

## Explicit non-claims

- Not two-host R730 proof (Mac loopback only).
- Not model-backed live mission (no LiveGrant spend).
- Not Goal/pursuit/UI (other lanes).

## Commands

```sh
uv run pytest tests/workers/test_continuous_connector.py tests/workers/test_mac_connector.py tests/workers/test_workers.py -q
```
