# TH-03 evidence summary

**Date:** 2026-09-25T15:26Z  
**Hostname:** `swarm.splitsignal.ai`  
**Server:** `http://127.0.0.1:18766`  
**Connector role:** Mac outbound only (no local Postgres)

## Results

| Check | Result | Evidence |
|---|---|---|
| Host one-shot `scripts/th03_mac_connector.py` | **pass** | `th03-mac-connector-5e47c04f7e13.json` / `latest.json` |
| Compose one-shot `deploy/compose/mac-connector.yml` | **pass** | `th03-mac-connector-8be5387d1f27.json` |
| Mac-local fixture used for protected checks | **pass** | steps `mac_local_fixture` |
| Forged / wrong-host review rejected | **pass** | step `reject_non_mac_or_forged` |
| Mission completed via authoritative review | **pass** | `final_mission_status=completed` |
| Server healthy after connector exit | **pass** | step `server_survives_connector_exit` |
| Registry `mac_local` scope gating | **pass** | `tests/workers/test_mac_connector.py` |

## Commands

```sh
# Server already up
uv run python scripts/th03_mac_connector.py
docker compose -f deploy/compose/mac-connector.yml up --abort-on-container-exit --exit-code-from connector
curl -fsS http://127.0.0.1:18766/health/ready
```

## Not run / blocked

R730, `.ai` DNS, Cloudflare Tunnel, Linear MCP (`needsAuth`), paid/live inference, OpenCode/Hermes.
