# TH-02 evidence summary

**Date:** 2026-09-25T15:19Z  
**Hostname:** `swarm.splitsignal.ai` (never `.com`)  
**Server:** `http://127.0.0.1:18766` (Mac loopback Compose)

## Results

| Path | Result | Evidence |
|---|---|---|
| HTTP product API native mission | **pass** | `latest.json` / `th02-native-mission-*.json` |
| Durable PG worker enroll→claim→submit→accept | **pass** | `durable-worker-latest.json` |
| Mission hydrate after API recreate | **pass** | `restart-hydrate.json` |
| Forged review rejection | **pass** | step `reject_forged_review` in latest.json |

## Fixes required for authoritative durability

1. Publish host port **18766** (18765 occupied by unrelated `swarm-ai-v14` process).
2. Mount full `/app/var` volume; entrypoint chowns then drops to `swarm`.
3. Set `SWARM_REPO_ROOT=/app` so non-editable image installs persist missions under the volume (not site-packages-adjacent paths).

## Not run / blocked

- R730 placement, `.ai` DNS, Cloudflare Tunnel, Linear MCP, paid/live inference, OpenCode/Hermes

## Commands

```sh
docker compose -f deploy/compose/server.yml up -d
uv run python scripts/th02_native_mission_authoritative.py
docker compose -f deploy/compose/server.yml exec -T -u swarm api \
  python /app/scripts/th02_durable_worker_incontainer.py
```
