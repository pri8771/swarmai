# SwarmAI MVP / two-host state

**Owner:** Cursor Project implementation worker (`bc-39c5759a-8fb4-514e-a825-98363e5fb28d`)  
**Branch:** `cursor/two-host-mvp-b28d`  
**Worktree:** `/Users/pchordia/Downloads/swarm-ai-two-host-mvp`  
**Updated:** 2026-09-25T15:40:00Z  
**Public hostname:** `swarm.splitsignal.ai` (never `.com`)  
**Loopback server:** `http://127.0.0.1:18766`

## Packet status

| Packet | Status | Notes |
|---|---|---|
| P00 | impl_complete | Docs + baseline frozen |
| TH-01 | impl_complete (Mac) | Compose+Postgres durable; R730 blocked |
| TH-02 | impl_complete (Mac eng) | HTTP + durable PG worker; restart hydrate |
| TH-03 | impl_complete (Mac eng) | Mac connector host + compose one-shot; server survives exit |
| TH-04 | impl_complete (Mac eng) | Durable CAS artifacts; identical sha256 after API restart |
| TH-05–TH-07 | planned | Next: minimal mission UI on real execution state (TH-05) |
| P01–P19 | planned | Product queue unchanged |

## Checks this session (TH-04)

| Check | Result |
|---|---|
| `pytest` artifact durability + workspace + mac_connector | pass (15) |
| Publish + list + content reopen | pass |
| API container restart recovery | pass |
| Volume CAS blob hash | pass (`a21e29cc…ee99`) |
| Worker re-enroll artifact intact | pass |
| Linear MCP | blocked needsAuth (queue only) |

## Next action

TH-05 minimal mission UI showing real execution state (still Mac loopback). External R730/DNS/CF still not required for continuation.
