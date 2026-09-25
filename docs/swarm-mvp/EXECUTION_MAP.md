# SwarmAI execution map (reconciled)

**Updated:** 2026-09-25T18:06Z  
**Integration branch:** `dev` @ `4c9566b7`  
**Hostname:** `swarm.splitsignal.ai`  
**Mandate:** `docs/v2-goal-pursuit-plan.md` (Project Context) + `internal/v2-operator-mandate.md`  
**Consolidate:** #50/#49/#46/#47/#51 merged into `dev` @ `4c9566b7`. #48 closed superseded (pursuit via #51). #45 closed superseded.

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
| R7 | **fixed** | Ruff/mypy/offline/console green on `dev` (#50); ephemeral Postgres `integration` job |
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
| #48 | D V1.9 Pursuit | stacked in #51 | eng on this tip — awaiting independent #48 land |
| #51 | E product UI | this branch | onto `05c0bc4b` + #48 pursuit stack |

## Next

1. Land #51 after offline CI green (includes #48 pursuit until #48 merges separately).  
2. When #48 merges to `dev`, rebase #51 to drop duplicate pursuit commits.  
3. Do **not** merge `main`.

## Lane D — V1.9 pursuit (stacked in #51)

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
| Goal schema | **uses Lane C on `dev`** | no fork |

## Lane E — V2.0 product UI/SDK (this lane)

| Packet | Status | Notes |
|---|---|---|
| P14 (SDK subset) | **in progress** | `src/swarm/sdk/client.py` — Lane C lifecycle + Lane D pursuit tick/status/why-next |
| P15 (console Goals) | **in progress** | Goals tab: create, agents, resources, start pursuit (tick), progress, interrupt/resume, why-next; Mission UI retained |
| Contract deps | #46 on `dev` + #48 stacked | Prefer those HTTP contracts; no parallel schemas |
| Deferred | elaborate server-admin UI; V3 multi-goal |

**Branch:** `cursor/v20-product-goal-ui-sdk-1418` → draft [PR #51](https://github.com/pri8771/swarmai/pull/51) to `dev`.
