# SwarmAI execution map (reconciled)

**Updated:** 2026-09-25T21:10Z  
**Integration branch:** `dev` @ `dd7726eb8c22986ef72847994c8e435a81a869b6`  
**Hostname:** configurable (operator deploy may use `swarm.splitsignal.ai`; freeze is config-driven — PORT-01 **closed**)  
**Mandate:** portable product + FAST_TRACK (Project Context `docs/v2-fast-track-plan.md` / `docs/v2-portable-product-plan.md`)  
**Consolidate:** portable #53–#58 + Lane F #47/#52 + L5 #61 + L1 #63 + L3 #62 + L4 #64 + L2 #65 + L6 #60 on tip. #48/#45 closed superseded.  
**Post-merge verify (portable):** PASS (Mac 2026-09-25T18:49Z; 78 passed @ `f39e0032`) — FT tip CI green on #65/#60 merges  
**Tracking branch:** `cursor/v20-tracking-tipsync-4635` (docs only — tip sync)

## Single authority

| Source | Role after reconciliation |
|---|---|
| TH-01–07 | Two-host eng increments — evidence retained; disputed acceptance → **review-required** until R1–R4 closed; **particular deployment**, not generic product correctness |
| P00–P19 | Product MVP spine — remains active after foundation |
| PORT-01–05 | **Portable product** layer — defects closed; roles/install/tests eng done; tracking continuous (see below) |
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
| #48 | D V1.9 Pursuit | stacked in #51 | **closed superseded** (pursuit via #51) |
| #51 | E product UI | — | **merged** |
| #52 | F acceptance probes | — | **merged** (`58f72fa5`) |
| #53 | P5 portable tracking | `13955489` | **merged** (`d8537386`) |
| #54 | P4 portability tests | `70c1a7cb` | **merged** (`fab9186c`) |
| #55 | P1 portable defects | `82d34b8c` | **merged** (`6211a567`) |
| #56 | P3 portable install | `2bff8d79` | **merged** (`f39e0032`) |
| #57 | P2 portable roles | `761d5859` | **merged** (`3fca9d29`) |
| #58 | PORT-05 tip-sync | — | **merged** (prior @ `f39e0032`) |
| #61 | L5 verify/acct | — | **merged** (`c294d8ca`) |
| #63 | L1 durable storage | — | **merged** (on tip before L4) |
| #62 | L3 workers/perms | — | **merged** (`53401981`) |
| #64 | L4 comms/memory | — | **merged** (`45efb242`) |
| #65 | L2 R20-01 pursuit | — | **merged** (`ad0ed567`) |
| #60 | L6 UI/SDK/Docker | — | **merged** (`dd7726eb` = tip) |

## FAST_TRACK lanes (L1–L6)

| Lane | PR | Status | Remaining depth |
|---|---|---|---|
| L1 storage | #63 | **eng_landed** | PG write-through (V20-E03); ledger/lesson persist (V20-E04) |
| L2 pursuit | #65 | **eng_landed** | Native model/tool loop fake HTTP (V20-E05); coordinator singleton (V20-E06) |
| L3 workers | #62 | **eng_landed** | Cancel kill-bound (V20-E08) |
| L4 memory | #64 | **eng_landed** | Optional mailbox PG (V20-E11) |
| L5 verify | #61 | **eng_landed** | Live adapter behind grant (V20-E07) |
| L6 product | #60 | **eng_landed** | Drain/revoke UI (V20-E09); compose smoke (V20-E10) |

## Portable product packets (PORT-*)

| Packet | Lane | Status | Notes |
|---|---|---|---|
| PORT-01 | P1 defects | **done** | #55 — freeze hostname config; connector no fixture/echo success; harness grant vs impl; Mac verify PASS |
| PORT-02 | P2 roles | **eng done** | #57 — server/worker/combined; enrollment contracts; matrix draft; cells stay experimental |
| PORT-03 | P3 install | **eng done** | #56 — portable install + fresh-install example; R730/Mac/CF = reference only |
| PORT-04 | P4 tests | **eng done** | #54 — multi hostname/path/platform probes; two-container protocol proof (Mac Docker green) |
| PORT-05 | P5 tracking | **eng done** (continuous) | Tip-sync @ `dd7726eb`; keep refreshing on future lands |

Plan SoT (user-facing): Project Context `docs/v2-fast-track-plan.md` + `docs/v2-portable-product-plan.md`.  
Repo support truth: `docs/swarm-mvp/PORTABLE_SUPPORT_MATRIX.md` + `docs/evidence/v20/support_matrix.json`.  
Gap audit: Project Context `internal/v20-gap-audit.md`.

## Remaining gaps (honest)

| Gap | Class |
|---|---|
| PG write-through / ledger durability / native model-tool loop / coordinator loop | V2.0 eng depth (V20-E03–E06) |
| Live adapter dispatch → `blocked_missing_implementation` | implementation (V20-E07) |
| Linux/enrollment claimed `supported` | platform qualification (keep experimental) |
| Real non-container cross-host proof | particular deployment / platform |
| LiveGrant / R730 / DNS/CF / Linear MCP / independent review / operator accept | genuinely external |

## Next

1. Continue V2.0 eng depth PRs (E03→E06) → `dev` when green.  
2. Keep V1.7–V2.0 `accepted: false` until product + live + review + operator gates pass.  
3. Do **not** merge `main`. Optional live dispatcher only with authentic LiveGrant — no invent, no spend.

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
| Live model-backed pursuit | **not claimed** | Operational path uses `NativeMissionDispatchExecutor` (R20-01); RecordingExecutor fixture/mock only; no spend |
| Goal schema | **uses Lane C on `dev`** | no fork |

## Lane E — V2.0 product UI/SDK

| Packet | Status | Notes |
|---|---|---|
| P14 (SDK subset) | **eng landed** (#51) | `src/swarm/sdk/client.py` — lifecycle + pursuit tick/status/why-next |
| P15 (console Goals) | **eng landed** (#51) | Goals tab retained Mission UI |
| Contract deps | #46 + #51 on `dev` | Prefer those HTTP contracts; no parallel schemas |
| Deferred | elaborate server-admin UI; V3 multi-goal |
| Version accept | **false** | independent review + operator required |
