# R1–R9 disposition matrix

**Branch:** `cursor/v2-foundation-r1r9-b28d`  
**Baseline reviewed:** `180eb73a`  
**Date:** 2026-09-25

| ID | Review claim | Eng disposition | Evidence |
|---|---|---|---|
| R1 | Forged acceptance via `required_checks` | Fixed — override 403; artifact required | `tests/foundation/test_r1_r9_regressions.py::test_r1_*`; probes after: accepted=null, HTTP 403 |
| R2 | In-memory workers vanish on restart | Mitigated — durable registry/idempotency under `var/` | `test_r2_*`; probes: workers_after=1, heartbeat 200. Continuous connector remains V1.7 |
| R3 | Artifact metadata lost / new ID on replay | Fixed — flock+merge index; durable idempotency | `test_r3_*`; probes same_id=true; both refs preserved |
| R4 | Deleted content still 200 | Fixed — resolve tombstone | `test_r4_*`; probes HTTP 404 |
| R5 | Forged grader stdout; sandbox escape | Fixed — harness nonce; path gate | `test_r5_*`; probes correct=false; outside read false |
| R6 | Native full mediation claimed | Fixed — proven=false; admission gated | `test_r6_*`; TH-06 tests updated |
| R7 | Ruff/mypy/CI | Partial — local introduced errors cleaned; full hosted CI + PG job pending | ruff/mypy on touched modules clean |
| R8 | Zero-$ rejected; hash unstable | Fixed — free-route zero grants + ceilings; frozen `generated_at` | `test_r8_*`; hash matches retained file |
| R9 | Tracking/manifest/Linear | Partial — PLAN_MANIFEST refreshed; Linear queue only | `docs/swarm-mvp/PLAN_MANIFEST.json`; `LINEAR_RECONCILIATION.md` |

## Probe rerun (isolated)

Command: `uv run python docs/reviews/CURSOR_REVIEW_2026-09-25/CURSOR_REVIEW_PROBES.py .`  
Note: original probe's zero-$ grant lacks `free_routes_only` flags — correctly rejected until ceilings set (protected test covers approved free grant).
