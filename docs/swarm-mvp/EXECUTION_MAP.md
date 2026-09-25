# SwarmAI execution map (reconciled)

**Updated:** 2026-09-25T18:05Z  
**Integration branch:** `dev`  
**Hostname:** `swarm.splitsignal.ai`  
**Mandate:** `docs/v2-goal-pursuit-plan.md` (Project Context) + `internal/v2-operator-mandate.md`  
**Consolidate:** #50+#49+#46+#47 on `dev` @ `05c0bc4b`. #48 rebased onto that tip (push pending CI). Hold #51 until #46+#48 landed.

## Single authority

| Source | Role after reconciliation |
|---|---|
| TH-01–07 | Two-host eng increments — evidence retained; disputed acceptance → **review-required** until R1–R4 closed |
| P00–P19 | Product MVP spine — remains active after foundation |
| `plan/swarmai-v2-redesign-20260925` @ `8598e6ac` | **Planning donor only** — map requirements; do not run as competing backlog or replace contracts |
| Independent review R1–R9 | Foundation gate — protected regressions under `tests/foundation/` |
| V20 acceptance freeze | Lane F — `benchmarks/v20_acceptance/scenarios.freeze.json`; harness cannot accept versions |

## Version path (mandate)

Foundation (R1–R9) → **V1.7** complete mission → **V1.8** durable goals → **V1.9** autonomous pursuit → **V2.0** integrated product.  
Do **not** implement V3/V4. Do **not** merge `main` without auth.

## R1–R9 disposition (integration tip)

| ID | Status | Protected tests / notes |
|---|---|---|
| R1 | **fixed** | Reject caller `required_checks` override; require artifact before accept |
| R2 | **mitigated→connector landed** | Continuous claim/renew/submit/cancel/reconnect + durable registry; PG still preferred when configured (`cursor/v17-connector-collab-e2e-b28d`) |
| R3 | **fixed** | Locked merge-safe artifact index; durable idempotent artifact IDs |
| R4 | **fixed** | Content reads enforce tombstone via `resolve` |
| R5 | **fixed** | Harness-owned nonce verdict; path-gated sandbox |
| R6 | **fixed** | `kernel_mediation_proven=false`; admission requires mandatory caps |
| R7 | **fixed** | Ruff/mypy/offline/console green; ephemeral Postgres `integration` job; hosted CI success `36167607568` / `36167588681`; protected `test_r7_*` |
| R8 | **fixed** | Zero-$ free-route grants with ceilings; frozen report hash |
| R9 | **partial** | PLAN_MANIFEST file hashes verified (`test_r9_*`); Linear still needsAuth queue; connector mount hardening deferred (Lane A) |

## Access gates (continue Mac eng)

| Gate | Status |
|---|---|
| Mac loopback | available |
| R730 / DNS / CF | blocked — record separately |
| Linear MCP | needsAuth — reconciliation queue only |
| Live paid providers | blocked — fake upstreams first |

## Lane F packet (this map owner)

| Packet | Status | Notes |
|---|---|---|
| V20-ACCEPT-FREEZE | **done** | §10 scenarios + pass criteria sealed; gates separated |
| V20-ACCEPT-HARNESS | **done** | `src/swarm/acceptance/`; CLI `swarm acceptance *`; scaffolds for product-owned scenarios |
| V20-ACCEPT-MATRICES | **done** | V1.7–V2.0 matrices always `accepted: false` |
| V20-ACCEPT-LIVE/HOST/ELAPSED | **blocked external** | No invented LiveGrant; host/elapsed not started |

## Dev consolidate status (2026-09-25)

| PR | Lane | Tip | Disposition |
|---|---|---|---|
| #50 | B foundation CI | `4d512777` | **merged** (`5236fbba`) |
| #49 | A connector+collab+E2E | `91250613` | **merged** (includes #45) |
| #45 | A connector | — | **closed superseded** by #49 |
| #46 | C V1.8 Goals | `bd6e44bf` | **merged** |
| #47 | F acceptance | `f8d10704` | **merged** |
| #48 | D V1.9 Pursuit | (rebased tip — see tip SHA after push) | rebased onto `05c0bc4b`; await hosted CI |
| #51 | E product UI | `3ae1e31f` | hold until #46+#48 landed |

## Next

1. Await hosted CI green on rebased #48; then merge to `dev` (not `main`).  
2. Hold #51 until #46+#48 landed; then rebase/CI.  
3. Do **not** merge `main`.

## Lane D — V1.9 pursuit (this increment)

| Packet | Status | Notes |
|---|---|---|
| Observe→assess→propose→admit→execute→verify→update | **eng done** | `src/swarm/pursuit/` + `PursuitEngine.tick` |
| Justified frontier + act/ask/experiment/wait/request-human | **eng done** | `frontier.py` |
| Schedules/backoff (no endless polling) | **eng done** | injectable clock; `PursuitScheduler` |
| Anti-duplicate + stagnation | **eng done** | dedupe keys; waiting transition on stagnation |
| Learning adopt/rollback (held-out required) | **eng done** | `PursuitLessonStore`; never expands envelopes |
| Deterministic tests (zero-spend) | **pass** | `tests/pursuit/test_v19_pursuit_loop.py` + Goal regressions |
| HTTP surface | **eng done** | `/v1/goals/{id}/pursuit/*` |
| Live model-backed pursuit | **not claimed** | RecordingExecutor default; no spend |
| Goal schema | **uses Lane C** | no fork; rebase on `05c0bc4b` |
