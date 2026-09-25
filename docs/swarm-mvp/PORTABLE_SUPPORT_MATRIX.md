# Portable support matrix

**Date Recorded:** 2026-09-25  
**Status:** drafting / evidence-grounded honesty only  
**Integration tip:** `origin/dev` @ `58f72fa5`  
**Related:** `docs/evidence/v20/support_matrix.json`, Project Context `docs/v2-portable-product-plan.md`  
**Versions accepted:** V1.7–V2.0 = **false**

Use only these status classes:

- `supported` — proven on declared config with acceptance evidence
- `experimental` — works in limited eng paths; not claimed for operators
- `local_only` — loopback / single-host eng only
- `in_progress` — active portable eng (PORT-*)
- `external_prerequisite_blocked` — needs LiveGrant, R730, DNS/CF, etc.
- `unsupported` — must not be claimed; defect or out of scope

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
| Linux container server | `in_progress` → target `supported` | product_correctness + platform | Preferred baseline; PORT-02/04 |
| Linux container worker | `in_progress` → target `supported` | product_correctness + platform | Enrollment contracts PORT-02 |
| Combined server+worker role | `in_progress` | product_correctness | Config-driven; one coordinator MVP |
| macOS native adapter | `local_only` | platform | Optional; must not be default success path |
| Unqualified “all OS/arch” | `unsupported` | — | Do not claim |
| R730 always-on server deploy | `external_prerequisite_blocked` | particular_deployment | Reference guide only (PORT-03) |
| Mac as connected worker (personal) | `external_prerequisite_blocked` | particular_deployment | TH-03 eng evidence ≠ portable default |
| Cloudflare / DNS `swarm.splitsignal.ai` | `external_prerequisite_blocked` | particular_deployment | Config external |

## Worker identity / scheduling

| Row | Status | Gate class | Notes |
|---|---|---|---|
| Enrolled worker id + platform/arch + runtimes | `in_progress` | product_correctness | PORT-02 |
| Verified capabilities / resource limits | `in_progress` | product_correctness | Authorized — self-report ≠ access |
| Workspace grants / data locality | `in_progress` | product_correctness | Bounded workspaces; no whole-repo mounts |
| Scheduling by personal machine name | `unsupported` | product_correctness | Defect if present; use contracts |
| Peer consensus / auto failover / replicated writable memory | `unsupported` (deferred) | — | Explicit non-goal for MVP |

## Execution / connector

| Row | Status | Gate class | Notes |
|---|---|---|---|
| Claim → permitted executor → immutable artifact → protected verify | `in_progress` | product_correctness | PORT-01b + PORT-04 |
| Lease renew / cancel / reconnect / stale-result reject | `local_only` / eng present | product_correctness | Retain; prove under portable configs |
| Default Mac fixture / completed echo as success | `unsupported` (defect) | product_correctness | PORT-01b must remove |
| Fixture/echo in explicit test/demo mode only | `in_progress` | product_correctness | Allowed when mode is explicit |

## Acceptance / freeze / live

| Row | Status | Gate class | Notes |
|---|---|---|---|
| Freeze hostname from deployment config | `in_progress` (defect today) | product_correctness | PORT-01a; tip still hardcodes |
| Historical freeze hash preservation | `in_progress` | product_correctness | Version freeze when scope changes |
| Deterministic campaign S01–S11 | `local_only` / eng green | product_correctness | ≠ version accepted |
| Live S12 / native model mission | `external_prerequisite_blocked` | live_inference | LiveGrant; never invent |
| Harness labels missing impl as `blocked_live_grant` | `unsupported` (defect) | product_correctness | PORT-01c |
| V1.7–V2.0 harness `accepted` | **false** | review + operator | Do not flip |

## Install / ops

| Row | Status | Gate class | Notes |
|---|---|---|---|
| Fresh install without editing app code | `in_progress` | product_correctness | PORT-03 |
| Fresh install without personal paths/creds | `in_progress` | product_correctness | PORT-03 example |
| Health/readiness + useful config errors | `in_progress` | product_correctness | PORT-03 |
| Backup/restore / migrations | `local_only` / schema present | product_correctness | Qualify under portable paths |
| Two-container protocol proof | `in_progress` | product_correctness | PORT-04; ≠ two-host |
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

- Mark `supported` without PORT acceptance evidence  
- Treat R730/CF absence as blocking PORT-01–04 eng  
- Mark any of V1.7–V2.0 accepted from this matrix alone  
