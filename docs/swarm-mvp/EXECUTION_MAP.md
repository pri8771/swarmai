# SwarmAI execution map (reconciled)

**Updated:** 2026-09-25T17:30Z  
**Integration branch:** `dev`  
**Lane B impl branch:** `cursor/foundation-ci-c8a3`  
**Hostname:** `swarm.splitsignal.ai`  
**Mandate:** `docs/v2-goal-pursuit-plan.md` (Project Context) + `internal/v2-operator-mandate.md`

## Single authority

| Source | Role after reconciliation |
|---|---|
| TH-01–07 | Two-host eng increments — evidence retained; disputed acceptance → **review-required** until R1–R4 closed |
| P00–P19 | Product MVP spine — remains active after foundation |
| `plan/swarmai-v2-redesign-20260925` @ `8598e6ac` | **Planning donor only** — map requirements; do not run as competing backlog or replace contracts |
| Independent review R1–R9 | Foundation gate — protected regressions under `tests/foundation/` |

## Version path (mandate)

Foundation (R1–R9) → **V1.7** complete mission → **V1.8** durable goals → **V1.9** autonomous pursuit → **V2.0** integrated product.  
Do **not** implement V3/V4. Do **not** merge `main` without auth.

## R1–R9 disposition (this branch)

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

## Next

1. Land PR #50 into `dev` when operator accepts (Lane B).  
2. R2 continuous connector on HTTP path (Lane A).  
3. V1.7 integrated mission lifecycle with ≥1 authorized model-backed run.  
4. V1.8 Goal lifecycle campaign → V1.9 pursuit → V2.0 product UI/SDK + acceptance freeze.
