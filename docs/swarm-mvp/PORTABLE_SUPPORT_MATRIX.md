# Portable support matrix

**Date Recorded:** 2026-09-25  
**Status:** evidence-grounded honesty — eng landed; no false `supported` claims  
**Integration tip:** `origin/dev` @ `f39e003249b73849a699bb554dddcdfbfffa502c`  
**Post-merge verify:** PASS (Mac 2026-09-25T18:49Z; 78 passed with `SWARM_PORTABLE_DOCKER=1`)  
**Related:** `docs/evidence/v20/support_matrix.json`, `docs/install/`, Project Context `docs/v2-portable-product-plan.md`  
**Versions accepted:** V1.7–V2.0 = **false**  
**PRs landed:** #53 (tracking) · #54 (PORT-04) · #55 (PORT-01) · #56 (PORT-03) · #57 (PORT-02)

Use only these status classes:

- `supported` — proven on declared config with acceptance evidence
- `experimental` — works in limited eng paths; not claimed for operators
- `local_only` — loopback / single-host eng only
- `in_progress` — active eng or missing implementation (not auth mislabel)
- `external_prerequisite_blocked` — needs LiveGrant, R730, DNS/CF, etc.
- `unsupported` — must not be claimed; out of scope or closed defect pattern
- `closed` — former defect fixed on tip

A row is never `supported` because code exists.

## Gate class for each row

| Gate class | When to use |
|---|---|
| product_correctness | Generic behavior any supported install must satisfy |
| supported_platform_qualification | Explicit OS/arch/runtime cell evidence |
| particular_deployment | Operator topology (R730, Mac, CF) |
| live_inference | Approved LiveGrant routes |
| independent_review / operator_acceptance | Promotion only |

## Platform / role

| Row | Status | Gate class | Evidence / notes |
|---|---|---|---|
| Linux container server | `experimental` | product_correctness + platform | Preferred baseline; #57 + Docker two-container proof; **not** operator-`supported` |
| Linux container worker | `experimental` | product_correctness + platform | Enrollment contracts #57; do not claim `supported` |
| Combined server+worker role | `experimental` | product_correctness | Config-driven; one coordinator MVP (#57) |
| macOS native adapter | `local_only` | platform | Optional; operational mode no longer fixture/echo-success (#55) |
| Unqualified “all OS/arch” | `unsupported` | — | Do not claim |
| R730 always-on server deploy | `external_prerequisite_blocked` | particular_deployment | Reference guide only (#56 / `docs/reference/`) |
| Mac as connected worker (personal) | `external_prerequisite_blocked` | particular_deployment | TH-03 eng evidence ≠ portable default |
| Cloudflare / DNS `swarm.splitsignal.ai` | `external_prerequisite_blocked` | particular_deployment | Config external |

## Worker identity / scheduling

| Row | Status | Gate class | Notes |
|---|---|---|---|
| Enrolled worker id + platform/arch + runtimes | `experimental` | product_correctness | #57 landed |
| Verified capabilities / resource limits | `experimental` | product_correctness | Authorized — self-report ≠ access |
| Workspace grants / data locality | `experimental` | product_correctness | Bounded workspaces; no whole-repo mounts |
| Scheduling by personal machine name | `unsupported` | product_correctness | Use contracts (#57) |
| Peer consensus / auto failover / replicated writable memory | `unsupported` (deferred) | — | Explicit non-goal for MVP |

## Execution / connector

| Row | Status | Gate class | Notes |
|---|---|---|---|
| Claim → permitted executor → immutable artifact → protected verify | `experimental` | product_correctness | PORT-01b closed (#55); PORT-04 probes green (#54) |
| Lease renew / cancel / reconnect / stale-result reject | `local_only` / eng present | product_correctness | Retained; proven under portable configs |
| Default Mac fixture / completed echo as success | **closed** (was defect) | product_correctness | Operational → `unsupported` (#55) |
| Fixture/echo in explicit test/demo mode only | `experimental` | product_correctness | Allowed when mode is explicit |
| Live adapter dispatch after approved grant | `in_progress` | product_correctness | Honest `blocked_missing_implementation` — not auth (#55) |

## Acceptance / freeze / live

| Row | Status | Gate class | Notes |
|---|---|---|---|
| Freeze hostname from deployment config | **closed** (was defect) | product_correctness | Config-driven match; historical content hash `b3e1e524…e749819` preserved |
| Historical freeze hash preservation | **closed** | product_correctness | Verified on post-merge suite |
| Deterministic campaign S01–S11 | `local_only` / eng green | product_correctness | ≠ version accepted |
| Live S12 / native model mission | `external_prerequisite_blocked` | live_inference | LiveGrant; never invent |
| Harness labels missing impl as `blocked_live_grant` | **closed** (was defect) | product_correctness | Approved grant → `blocked_missing_implementation` (#55) |
| V1.7–V2.0 harness `accepted` | **false** | review + operator | Do not flip |

## Install / ops

| Row | Status | Gate class | Notes |
|---|---|---|---|
| Fresh install without editing app code | `experimental` | product_correctness | #56 — `docs/install/` + `examples/fresh-install/` |
| Fresh install without personal paths/creds | `experimental` | product_correctness | Placeholder `coordinator.example.test`; tests guard personal paths |
| Health/readiness + useful config errors | `experimental` | product_correctness | Doctor `ready_to_start` + `config_errors`; `/health/*` docs |
| Backup/restore / migrations | `local_only` / schema present | product_correctness | `docs/install/STORAGE_BACKUP_RESTORE.md` |
| R730 / Mac / Cloudflare docs | `external_prerequisite_blocked` (guides only) | particular_deployment | `docs/reference/*` labelled REFERENCE ONLY |
| Two-container protocol proof | `experimental` | product_correctness | #54; Mac Docker 5/5 green; ≠ two-host; ≠ operator-`supported` |
| Real cross-host proof | `external_prerequisite_blocked` | particular_deployment | Separate from PORT-04 |

## Surfaces (prior local evidence — unchanged honesty)

| Surface | Status | Evidence |
|---|---|---|
| API | implemented (local) | `tests/api/test_api.py` |
| CLI | implemented (local) | `src/swarm/cli.py` |
| Console | packaging_present | `apps/console` |
| Postgres | schema_present | migrations; live DSN optional |
| Paid cloud | blocked | `SWARM_ALLOW_PAID=false` |

## Do not

- Mark `supported` without operator-grade qualification + review  
- Treat R730/CF absence as blocking portable eng (already landed)  
- Mark any of V1.7–V2.0 accepted from this matrix alone  
- Re-open closed PORT-01 defects as present on tip `f39e0032`
