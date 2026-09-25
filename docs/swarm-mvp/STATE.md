# SwarmAI MVP / two-host state

**Owner:** Cursor Project implementation worker (`bc-39c5759a-8fb4-514e-a825-98363e5fb28d`)  
**Branch:** `cursor/two-host-mvp-b28d`  
**Worktree:** `/Users/pchordia/Downloads/swarm-ai-two-host-mvp`  
**Updated:** 2026-09-25T15:26:00Z  
**Public hostname:** `swarm.splitsignal.ai` (never `.com`)  
**Loopback server:** `http://127.0.0.1:18766`

## Packet status

| Packet | Status | Notes |
|---|---|---|
| P00 | impl_complete | Docs + baseline frozen |
| TH-01 | impl_complete (Mac) | Compose+Postgres durable; R730 blocked |
| TH-02 | impl_complete (Mac eng) | HTTP + durable PG worker; restart hydrate |
| TH-03 | impl_complete (Mac eng) | Mac connector host + compose one-shot; server survives exit |
| TH-04–TH-07 | planned | Next: durable artifacts + restart recovery (TH-04) |
| P01–P19 | planned | Product queue unchanged |

## Checks this session (TH-03)

| Check | Result |
|---|---|
| `pytest` deployment + mac_connector | pass (10) |
| Host mac connector one-shot | pass |
| Compose mac-connector one-shot | pass |
| Server after connector exit | ready / database up |
| Linear MCP | blocked needsAuth (queue only) |

## Next action

TH-04 durable artifacts and recovery after worker/server restart (still Mac loopback).
