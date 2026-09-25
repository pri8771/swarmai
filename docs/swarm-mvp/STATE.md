# SwarmAI MVP / two-host state

**Owner:** Cursor Project implementation worker (`bc-39c5759a-8fb4-514e-a825-98363e5fb28d`)  
**Branch:** `cursor/two-host-mvp-b28d`  
**Worktree:** `/Users/pchordia/Downloads/swarm-ai-two-host-mvp`  
**Updated:** 2026-09-25T15:51:00Z  
**Public hostname:** `swarm.splitsignal.ai` (never `.com`)  
**Loopback server:** `http://127.0.0.1:18766`

## Packet status

| Packet | Status | Notes |
|---|---|---|
| P00 | impl_complete | Docs + baseline frozen |
| TH-01 | impl_complete (Mac) | Compose+Postgres durable; R730 blocked |
| TH-02 | impl_complete (Mac eng) | HTTP + durable PG worker; restart hydrate |
| TH-03 | impl_complete (Mac eng) | Mac connector host + compose one-shot |
| TH-04 | impl_complete (Mac eng) | Durable CAS artifacts; identical sha256 after restart |
| TH-05 | impl_complete (Mac eng) | Console live loader shows real missions/artifacts/workers |
| TH-06 | impl_complete (Mac eng) | Runtime adapters qualified honestly; OpenCode/Hermes not mission-admissible |
| TH-07 | planned | Next: synthetic eval harness + live qualification gate |
| P01–P19 | planned | Product queue unchanged |

## Runtime qualification (TH-06)

| Runtime | Status |
|---|---|
| Native | available (partial) |
| OpenCode | discovered_unqualified — **not** mission-admissible |
| Hermes | unavailable — **not** mission-admissible |

Framework config alone does **not** enforce SwarmAI contracts.

## Checks this session (TH-06)

| Check | Result |
|---|---|
| pytest runtime adapters | pass (6) |
| `scripts/th06_runtime_qualification.py` | pass |
| `GET /v1/runtimes` | pass |
| Linear MCP | blocked needsAuth (queue only) |

## Next action

TH-07 synthetic evaluation harness and live qualification gate (still Mac loopback; R730/DNS/CF not required).
