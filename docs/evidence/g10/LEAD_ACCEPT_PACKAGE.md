# G10 / V1.0 repair — lead accept package

**Status:** worker packages for independent lead review — **not** lead-accepted  
**Candidate tip:** `aa6865a74249e046bfe697532accb00390bb5873`  
**Prior CI-green tip (docs):** `3c82e0feecb370a6c8cef363ef85cb363407d1d1`  
**Code tip (LEAD-009 complete):** `108145ea06af8e0ba11a4617f0d21a8e1fea2440`  
**Draft PR:** https://github.com/pri8771/swarmai/pull/14 (draft; **do not merge**)  
**Base main:** `b9141fa3150f853586dede0334a47b344571bc16`  
**Recorded (UTC):** 2026-09-20T21:22:43Z  
**cursor agent CLI:** Not logged in — `SWARM_HOURLY_SKIP_CURSOR_PROBE` **not** cleared  

This package binds LEAD-20260920-009 items #1–6 to pushed SHAs, CI run IDs, regression paths and AUD finding resolution. Lead acceptance is independent; this document does not invent it.

## CI evidence (current tip)

| Run | Trigger | SHA | Conclusion | Jobs |
|-----|---------|-----|------------|------|
| [35538395519](https://github.com/pri8771/swarmai/actions/runs/35538395519) | push `docs(g10)` | `3c82e0f` | **success** | offline + console + live-gated notice |
| [35538397490](https://github.com/pri8771/swarmai/actions/runs/35538397490) | PR #14 | `3c82e0f` | **success** | offline + console + live-gated notice |
| [35538252435](https://github.com/pri8771/swarmai/actions/runs/35538252435) | push LEAD-009 #5/#6 | `108145ea` | **success** | offline + console + live-gated notice |

Offline job includes: Ruff, mypy, packaging/install check, Alembic heads, broad offline pytest.  
Integration pytest: honest skip without `SWARM_DATABASE_URL`.  
Live-gated: blocked-notice only (not live product evidence).

## LEAD-009 checklist → evidence

| # | Requirement | Tip / files | Regression |
|---|-------------|-------------|------------|
| 1 | mypy `_broker` typing | `2335471` → `src/swarm/mission/runtime.py` | mypy clean in CI |
| 2 | Scoped idempotency + auth-before-cache | `2335471` → `src/swarm/api/routes_v1.py` | `tests/api/test_fix002_auth_isolation.py` |
| 3 | Bootstrap ≠ fixed demo principals | `2335471` → `src/swarm/api/app.py` | same + bootstrap defaults |
| 4 | Release evidence semantic validation | `2335471` → `src/swarm/release/verify.py` | `tests/release/test_release_verify.py` |
| 5 | Provider readiness fail-closed | `108145ea` → `capability_registry.py`, `evidence_router.py` | `tests/providers/test_capability_registry.py` |
| 6 | Parser dogfood fixture-only | `108145ea` → `worker.py`, `cli.py`, `selfdev/runner.py` | `tests/mission/test_parser_dogfood_fixture.py` |

## FIX packet map

| Packet | Status (worker) | Key commits | Notes for lead |
|--------|-----------------|-------------|----------------|
| FIX-001 | CI green on tip | `f028009`, `2f91d7d`, `2335471`, `108145ea` | Earlier mypy red tip superseded |
| FIX-002 | Source closed | `d622f1d`, `2335471` | Scoped keys; no silent demo principals |
| FIX-003 | Source closed + LEAD-011 identity | `51b2152`, `2335471`, `108145ea`, tip pending | SHA/exit/mode/freshness + evidence-kind identity groups |
| FIX-004 | Parallel lane | `d60394d` | Hourly runner installed; CLI login still Not logged in |
| FIX-005 | Source closed | `51b2152`, `108145ea` | No GOOD_FIX operational fallback; parser opt-in only |

## Findings resolution matrix

See [`findings-resolution-matrix.md`](./findings-resolution-matrix.md) on the full V1.4
integration branch if needed — **not** re-copied onto the 2026-09-23 zero-spend slice.

## Slice note (2026-09-23)

This package was re-landed onto `cursor/v1.4-zero-spend-slice-main` for review. Tip SHAs
above refer to the original V1.4 lineage; this slice branch is uncommitted off `main`
@ `b9141fa`. Still **not** lead-accepted.

## What is **not** claimed

- Lead accept of G10
- Main merge / tag / public deploy / spend
- Cursor CLI login or cleared `SKIP_CURSOR_PROBE`
- G12 dual-remote overlap, G13 qualification (≥5/cell screening path opened by dataset expansion but not yet qualified), G14 live multi-planner, LIVE-142

## Suggested lead review commands

```bash
git fetch origin cursor/v1.4-live-integration-11e2
git checkout aa6865a74249e046bfe697532accb00390bb5873
# or review PR https://github.com/pri8771/swarmai/pull/14
gh run view 35538395519
uv run ruff check . && uv run mypy src/swarm
uv run pytest tests/api/test_fix002_auth_isolation.py \
  tests/providers/test_capability_registry.py \
  tests/mission/test_parser_dogfood_fixture.py \
  tests/release/test_release_verify.py -q
```

## Related coordination

- CURSOR-014 / CURSOR-015 on `coordination/swarm-control`
- Gate matrix: `docs/evidence/GATE_MATRIX.md`
