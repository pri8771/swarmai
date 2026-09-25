# SwarmAI execution map (reconciled)

**Updated:** 2026-09-25T18:29Z  
**Integration branch:** `dev` @ `58f72fa5`  
**Hostname:** configurable (operator deploy may use `swarm.splitsignal.ai`; not product hardcoded truth)  
**Mandate:** portable product (Project Context `docs/v2-portable-product-plan.md`) + prior goal-pursuit plan  
**Consolidate:** #50/#49/#46/#47/#51/#52 merged into `dev` @ `58f72fa5`. #48 closed superseded (pursuit via #51). #45 closed superseded.  
**Portable tracking branch:** `cursor/v2-portable-tracking-3ac7` (docs only)

## Single authority

| Source | Role after reconciliation |
|---|---|
| TH-01–07 | Two-host eng increments — evidence retained; disputed acceptance → **review-required** until R1–R4 closed; **particular deployment**, not generic product correctness |
| P00–P19 | Product MVP spine — remains active after foundation |
| PORT-01–05 | **Portable product** layer — defects, generic roles, install, portability tests, tracking (see below) |
| `plan/swarmai-v2-redesign-20260925` @ `8598e6ac` | **Planning donor only** — map requirements; do not run as competing backlog or replace contracts |
| Independent review R1–R9 | Foundation gate — protected regressions under `tests/foundation/` |
| V20 acceptance freeze | Lane F — `benchmarks/v20_acceptance/scenarios.freeze.json`; harness cannot accept versions |

## Gate taxonomy (do not collapse)

| Gate class | Blocks version accept? | Examples |
|---|---|---|
| Product correctness | Yes | Configurable freeze hostname; real connector execution; harness auth vs impl |
| Supported-platform qualification | Yes for “supported” claims | Linux container baseline; proven native adapters only |
| Particular deployment | No for generic eng | R730, CF tunnel, personal paths |
| Live inference | Yes for live cells | Approved LiveGrant only — never invent |
| Independent review | Yes for promotion | No self-approval |
| Operator acceptance | Yes for release claim | Separate from eng green |

**V1.7 / V1.8 / V1.9 / V2.0 remain unaccepted.**

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

## Portable product packets (PORT-*)

| Packet | Lane | Status | Notes |
|---|---|---|---|
| PORT-01 | P1 defects | **open** | freeze hostname config; connector no fixture/echo success; harness grant vs impl |
| PORT-02 | P2 roles | **open** | server/worker/combined; enrollment contracts; support matrix; generic connector |
| PORT-03 | P3 install | **open** | portable install + fresh-install example; R730/Mac/CF = reference only |
| PORT-04 | P4 tests | **open** | multi hostname/path/platform probes; two-container protocol proof |
| PORT-05 | P5 tracking | **in progress** | this map + packet queue + support matrix + Linear queue |

Plan SoT (user-facing): Project Context `docs/v2-portable-product-plan.md`.  
Repo support truth: `docs/swarm-mvp/PORTABLE_SUPPORT_MATRIX.md` + `docs/evidence/v20/support_matrix.json`.

## Next

1. Land PORT-01–04 draft PRs → `dev` when green; consolidate lane merges.  
2. Keep V1.7–V2.0 `accepted: false` until product + live + review + operator gates pass.  
3. Do **not** merge `main`. Missing R730/LiveGrant does **not** stop portable eng.

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
