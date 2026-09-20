# SwarmAI — Offline Release Candidate Status

**Date:** 2026-09-20  
**Branch:** `cursor/p01-foundation-contracts-11e2`  
**Label:** `offline-verified-release-candidate`  
**Not:** cloud-operating, live-qualified, publicly launched, or merge-ready without human review

## Links

| Item | URL |
|---|---|
| Repo | https://github.com/pri8771/swarmai |
| RC branch | https://github.com/pri8771/swarmai/tree/cursor/p01-foundation-contracts-11e2 |
| Draft PR | https://github.com/pri8771/swarmai/pull/1 |
| Latest SHA | `16c14f41c1a24775ce4e1d4c50c8ebd6e49c84b6` |

## Status

| Dimension | Result |
|---|---|
| Kit packets P01–P21 (offline) | complete |
| `swarm release verify` | pass |
| Required RC pytest slice | pass |
| Fresh-install mock demo | pass |
| Ruff / mypy (CI-defined) | pass |
| Live P15/P16/P18 | **not attempted** (paused — keys) |
| Remote | `origin` → https://github.com/pri8771/swarmai.git |
| Draft PR | open (draft) vs `main` — **do not merge** |
| Merge / deploy / launch | **not authorized** |

## Implemented by subsystem

| Area | Packets | Notes |
|---|---|---|
| Contracts, fixtures, tooling | P01–P02 | typed contracts, pytest/ruff/mypy baseline |
| Providers + broker | P03–P05 | adapters, catalog, durable inference broker |
| Sandbox / workspace / runtime | P06–P08, P10 | isolation, context, agent sessions |
| Console + API | P09, P13 | Vite console, FastAPI product API |
| Controller + workers | P11–P12 | adaptive scheduling, membership |
| Integrated demo | P14 | parser-issue mock mission |
| Onboarding / qualify / deploy | P15–P17 | offline layers; live blocked |
| Load / chaos | P18 | synthetic soak + fault matrix |
| Self-dev / review / RC | P19–P21 | patch artifacts, checklist, release verify |

## Verification (commands)

```sh
cd /path/to/swarm-ai
uv run pytest tests/selfdev tests/regressions tests/release -q
uv run swarm release verify
uv run swarm demo parser-issue --mode mock --report-dir var/reports/fresh-install
uv run ruff check .
uv run mypy src/swarm
```

## Safety

- `.env` gitignored; `.env.example` only in tree
- No production secrets tracked; scrubbers refuse secret-shaped payloads in logs/API
- Workers / sandbox do not receive host secrets
- Self-dev cannot auto-merge or expand approval/release rights
- Release verify fails closed if secret files or required docs missing

## Pending live validation

- [ ] Provider accounts with **zero-charge**-eligible routes
- [ ] Keys only in local `.env` (never commit); spend policy = zero
- [ ] P15 live canary on verified routes
- [ ] P16 live qualification (multi-route if eligible)
- [ ] Optional P18 live comparisons under verified capacity
- [ ] Explicit auth before any push-to-production / public launch

## Known limitations

- Live inference, qualification rankings, and cloud deploy are **unverified**
- Single local branch today; no `origin` remote configured at RC checkpoint
- Integration DB tests may require `SWARM_DATABASE_URL` (marked `integration`)
- Console and compose profiles are local/dev oriented

## Next milestone

1. Create/configure GitHub remote + default `main` (human).
2. Push this branch and open a **draft** PR for review (do not merge until approved).
3. After keys: live P15 → P16 only under zero-spend policy.
4. Do not begin live work from this captain run.
