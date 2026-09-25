# TH-05 evidence summary

**Date:** 2026-09-25T15:45Z  
**Hostname:** `swarm.splitsignal.ai`  
**Server:** `http://127.0.0.1:18766`  
**Console:** `http://127.0.0.1:43127/?mode=live&baseUrl=http://127.0.0.1:18766&missionId=…`

## Results

| Check | Result | Evidence |
|---|---|---|
| Live API mission with artifact hash | **pass** | mission `9cf531a7…`, hash `a21e29cc…` |
| Console live endpoints (mission/graph/artifacts/workers/projects) | **pass** | step `console_live_endpoints` |
| Console vitest (18) | **pass** | step `console_vitest` |
| Console production build | **pass** | step `console_build` |
| Dist has hostname, no secret literals | **pass** | step `dist_no_secrets_has_hostname` |
| Node live snapshot parity with console fetches | **pass** | step `node_live_snapshot_parity` |

## Commands

```sh
# Server already up on :18766
uv run python scripts/th05_mission_ui_live.py
cd apps/console && npm test && npm run build
# Browser (operator appends token locally — never commit tokens):
# http://127.0.0.1:43127/?mode=live&baseUrl=http://127.0.0.1:18766&missionId=<id>&token=<loopback>
```

## Not run / blocked

R730, `.ai` DNS, Cloudflare Tunnel, Linear MCP (`needsAuth`), paid/live inference, full P15 Playwright suite (deferred — TH-05 is minimal live wiring).
