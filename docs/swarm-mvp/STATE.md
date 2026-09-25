# SwarmAI MVP / two-host state

**Owner:** Cursor Project implementation worker (`bc-39c5759a-8fb4-514e-a825-98363e5fb28d`)  
**Branch:** `cursor/two-host-mvp-b28d`  
**Worktree:** `/Users/pchordia/Downloads/swarm-ai-two-host-mvp`  
**Updated:** 2026-09-25T15:45:00Z  
**Public hostname:** `swarm.splitsignal.ai` (never `.com`)  
**Loopback server:** `http://127.0.0.1:18766`  
**Console:** `http://127.0.0.1:43127` (live `?mode=live&baseUrl=…`)

## Packet status

| Packet | Status | Notes |
|---|---|---|
| P00 | impl_complete | Docs + baseline frozen |
| TH-01 | impl_complete (Mac) | Compose+Postgres durable; R730 blocked |
| TH-02 | impl_complete (Mac eng) | HTTP + durable PG worker; restart hydrate |
| TH-03 | impl_complete (Mac eng) | Mac connector host + compose one-shot |
| TH-04 | impl_complete (Mac eng) | Durable CAS artifacts; identical sha256 after restart |
| TH-05 | impl_complete (Mac eng) | Console live loader shows real missions/artifacts/workers |
| TH-06–TH-07 | planned | Next: optional OpenCode/Hermes qualification (TH-06) or eval harness (TH-07) |
| P01–P19 | planned | Product queue unchanged |

## Checks this session (TH-05)

| Check | Result |
|---|---|
| Console vitest | pass (18) |
| Console build + secret scan | pass |
| Live snapshot parity vs API | pass |
| Linear MCP | blocked needsAuth (queue only) |

## Next action

TH-06 optional OpenCode/Hermes runtime qualification, or TH-07 synthetic eval harness — still Mac loopback; R730/DNS/CF not required.
