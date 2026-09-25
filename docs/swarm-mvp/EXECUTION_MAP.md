# SwarmAI execution map (reconciled)

**Updated:** 2026-09-25T17:50Z  
**Integration branch:** `dev` @ `e9ae85c4`  
**Lane F branch:** `cursor/v20-acceptance-freeze-92df`  
**Hostname:** `swarm.splitsignal.ai`  
**Mandate:** `docs/v2-goal-pursuit-plan.md` (Project Context) + `internal/v2-operator-mandate.md`  
**Consolidate:** PR #50 (Lane B / R7) merged into `dev`. Lane F rebasing onto `e9ae85c4` for offline CI green. Other lane drafts may still need rebase.

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
| R2 | **mitigated** | Durable worker + idempotency mirror under `var/`; continuous lease connector still V1.7 |
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
| #50 | B foundation CI | `4d512777` | **merged** into `dev` (`5236fbba` → `e9ae85c4`) |
| #46 | C V1.8 Goals | `2ea1e655` | blocked — offline ruff fail; rebase onto `dev` |
| #48 | D V1.9 Pursuit | `1f6c0ddd` | blocked — offline pytest fail (`artifact_required`); skip until newer tip green |
| #45 | A connector | `e4212873` | blocked — offline ruff; superseded content in #49 |
| #49 | A connector+E2E | `330277b3` | blocked — offline ruff; prefer over #45 when green |
| #47 | F acceptance | rebasing → CI | rebased onto `e9ae85c4`; offline/ruff/mypy fixes; target green |
| #51 | E product UI | `3ae1e31f` | blocked — offline ruff; needs #46+#48 first |

## Next

1. Land Lane F (#47) when offline CI green on `e9ae85c4`.  
2. Other lanes rebase onto `origin/dev` and re-run hosted CI.  
3. Merge next green non-conflicting drafts in order: #49 (or #45) → #46 → #48 (when green) → #47 → #51.  
4. R2 continuous connector + V1.7 integrated mission with ≥1 authorized model-backed run.  
5. Do **not** merge `main`.
