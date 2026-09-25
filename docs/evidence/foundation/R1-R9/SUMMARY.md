# R1–R9 disposition matrix

**Branch:** `cursor/foundation-ci-c8a3` (Lane B; based on `origin/dev` @ `748078f2`)  
**Baseline reviewed:** `180eb73a`  
**Date:** 2026-09-25

| ID | Review claim | Eng disposition | Evidence |
|---|---|---|---|
| R1 | Forged acceptance via `required_checks` | Fixed — override 403; artifact required | `tests/foundation/test_r1_r9_regressions.py::test_r1_*`; probes after: accepted=null, HTTP 403 |
| R2 | In-memory workers vanish on restart | Mitigated — durable registry/idempotency under `var/` | `test_r2_*`; probes: workers_after=1, heartbeat 200. Continuous connector remains V1.7 / Lane A |
| R3 | Artifact metadata lost / new ID on replay | Fixed — flock+merge index; durable idempotency | `test_r3_*`; probes same_id=true; both refs preserved |
| R4 | Deleted content still 200 | Fixed — resolve tombstone | `test_r4_*`; probes HTTP 404 |
| R5 | Forged grader stdout; sandbox escape | Fixed — harness nonce; path gate | `test_r5_*`; probes correct=false; outside read false |
| R6 | Native full mediation claimed | Fixed — proven=false; admission gated | `test_r6_*`; TH-06 tests updated |
| R7 | Ruff/mypy/CI; PG skipped as notice | **Fixed (eng)** — lint clean; offline 367 pass; console lint/test/build pass; ephemeral Postgres CI job; integration 69 pass locally; `test_r7_ci_requires_ephemeral_postgres_integration_job` | See §R7 below |
| R8 | Zero-$ rejected; hash unstable | Fixed — free-route zero grants + ceilings; frozen `generated_at` | `test_r8_*`; hash matches retained file |
| R9 | Tracking/manifest/Linear | Partial — PLAN_MANIFEST file digests match (`test_r9_*`); Linear queue only; connector mount → Lane A | `docs/swarm-mvp/PLAN_MANIFEST.json`; `LINEAR_RECONCILIATION.md` |

## R7 verification (Lane B, 2026-09-25)

Commands (local):

```bash
uv run ruff check .
uv run mypy src/swarm
uv run pytest tests/contracts tests/spikes tests/api … tests/e2e -q --ignore=tests/integration
# → 367 passed
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm \
  uv run pytest tests/integration -q -m integration
# → 69 passed
cd apps/console && npm ci && npm run lint && npm run test && npm run build
# → 18 vitest passed; build ok
```

CI change: `.github/workflows/ci.yml` adds dedicated `integration` job with `postgres:16` service and always-on `SWARM_DATABASE_URL`. Offline job no longer treats a missing-DB notice as the integration path. Offline collection includes previously omitted `tests/foundation`, `knowledge`, `objectives`, `extensions`, `recovery`.

## Probe rerun (isolated)

Command: `uv run python docs/reviews/CURSOR_REVIEW_2026-09-25/CURSOR_REVIEW_PROBES.py .`  
Note: original probe's zero-$ grant lacks `free_routes_only` flags — correctly rejected until ceilings set (protected test covers approved free grant).
