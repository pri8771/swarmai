# SwarmAI MVP / two-host state

**Owner:** Cursor Project implementation worker (`bc-39c5759a-8fb4-514e-a825-98363e5fb28d`)  
**Branch:** `cursor/two-host-mvp-b28d`  
**Worktree:** `/Users/pchordia/Downloads/swarm-ai-two-host-mvp`  
**Updated:** 2026-09-25T16:10:00Z  
**Public hostname:** `swarm.splitsignal.ai` (never `.com`)  
**Loopback server:** `http://127.0.0.1:18766`  
**Integration branch:** `origin/dev` @ `14c62a77` (TH-01–07; created 2026-09-25 per operator; `main` untouched)

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
| TH-07 | impl_complete (Mac eng) | Synthetic harness ready; live gate blocked pending grant |
| P01–P19 | planned | Product queue unchanged |

## Eval harness (TH-07)

| Item | Status |
|---|---|
| Starter suite (128; easy→expert; 8 families) | prepared |
| Sealed answers / holdout vs calibration | proven |
| Oracle + fixture-fail paths | pass |
| Live route/budget gate | **blocked** (no grant; dispatch not enabled) |
| Production routing auto-change | **forbidden / verified none** |

## Checks this session (TH-07)

| Check | Result |
|---|---|
| pytest `test_synthetic_harness_th07` | pass (10) |
| `scripts/th07_synthetic_eval_harness.py` | pass |
| Linear MCP | blocked needsAuth (queue only) |

## Next action

Live qualification only when an approved route+budget grant exists (do not wait on R730/DNS/CF). Otherwise continue product packets (P01+) on Mac loopback. External infra still blocked.
