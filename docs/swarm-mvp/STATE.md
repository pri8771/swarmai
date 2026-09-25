# SwarmAI MVP / two-host state

**Owner:** Cursor Project implementation worker (`bc-39c5759a-8fb4-514e-a825-98363e5fb28d`)  
**Branch:** `cursor/two-host-mvp-b28d`  
**Worktree:** `/Users/pchordia/Downloads/swarm-ai-two-host-mvp`  
**Base:** `origin/main` @ `08b910f981eff2ab66873a71055090f2c60f2a91`  
**Updated:** 2026-09-25T15:19:00Z  
**Public hostname:** `swarm.splitsignal.ai` (never `.com`)  
**Loopback server:** `http://127.0.0.1:18766`

## Packet status

| Packet | Status | Notes |
|---|---|---|
| P00 | impl_complete | Docs + baseline frozen |
| TH-01 | impl_complete (Mac) | Compose+Postgres durable; R730 still blocked |
| TH-02 | impl_complete (Mac eng) | HTTP native mission + durable PG worker; restart hydrate OK |
| TH-03–TH-07 | planned | Next: Mac connector scoped task (TH-03) |
| P01–P19 | planned | Product queue unchanged |

## Checks this session (TH-02)

| Check | Result |
|---|---|
| `pytest tests/deployment` (+ repo_root) | pass (9) |
| HTTP native mission authoritative path | pass |
| Durable worker claim/submit/accept on Postgres | pass |
| Mission survives API recreate | pass |
| R730 / DNS `.ai` / CF / Linear | blocked |

## Next action

TH-03 Mac connector completing a scoped task through the server (still Mac loopback; no R730 wait). Linear auth still needed for in-place issue updates.
