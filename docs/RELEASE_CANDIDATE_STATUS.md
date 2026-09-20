# SwarmAI — Offline Release Candidate Status

**Date:** 2026-09-20  
**Branch:** `cursor/p01-foundation-contracts-11e2`  
**Label:** `offline-verified-release-candidate`  
**Not:** fully live-verified, cloud-operating, or production-launched

## Links

| Item | URL |
|---|---|
| Repo | https://github.com/pri8771/swarmai |
| RC branch | https://github.com/pri8771/swarmai/tree/cursor/p01-foundation-contracts-11e2 |
| PR (merged) | https://github.com/pri8771/swarmai/pull/1 |
| Pre-release | https://github.com/pri8771/swarmai/releases/tag/v0.1.0-rc.1 |
| Merge commit | `827cb82c9aebc5f83741b215d025fcedf8ab16bd` |
| Latest SHA (pre-merge docs) | see git / release tag |

## Status

| Dimension | Result |
|---|---|
| Kit packets P01–P21 (offline) | complete |
| `swarm release verify` | pass |
| Required RC pytest slice | pass |
| Fresh-install mock demo | pass |
| Ruff / mypy (CI-defined) | pass |
| Live P15 canary | **blocked** — no local `.env` / process keys |
| Live P16 qualification | **blocked** — depends on P15 live routes |
| Live P18 comparisons | **skipped** — no keys; mock evidence retained |
| Spend policy | zero (no payment methods / paid credits used) |
| Merge / GitHub pre-release | **done** (merged PR #1; tag `v0.1.0-rc.1` prerelease) |
| Local launch | **done** — API on 127.0.0.1:18765 (mock mode) |
| Cloud production infra | **not** provisioned |

## Live setup (2026-09-20)

| Check | Result |
|---|---|
| `.env` present | **no** |
| Process env provider keys | **none** |
| `SWARM_ALLOW_PAID` | unset (treat as deny) |
| Zero-spend live canaries attempted | **no** |

### Exact user actions for live (paused)

1. Copy `.env.example` → `.env` (never commit `.env`).
2. Add only provider keys for **zero-charge-eligible** routes; confirm account billing/spend = zero.
3. Set `SWARM_ALLOW_PAID=false` and do not enable paid wrappers.
4. Re-run: `uv run swarm providers onboarding-report` then bounded `providers canary --mode live` only on verified free routes.
5. Then P16: `uv run swarm eval plan/run --mode live` only with eligible route IDs.

## Implemented by subsystem

| Area | Packets | Offline | Live |
|---|---|---|---|
| Contracts / tooling | P01–P02 | verified | n/a |
| Providers + broker | P03–P05 | verified | not tested |
| Sandbox / workspace / runtime | P06–P08, P10 | verified | n/a |
| Console + API | P09, P13 | verified | local launch only |
| Controller + workers | P11–P12 | verified | n/a |
| Integrated demo | P14 | verified (mock models) | n/a |
| Onboarding / qualify / deploy | P15–P17 | offline verified | P15/P16 live blocked |
| Load / chaos | P18 | mock verified | live skipped |
| Self-dev / review / RC | P19–P21 | verified | n/a |

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

- `.env` gitignored; no credentials committed
- Scrubbers refuse secret-shaped payloads in logs/API
- Workers/sandbox do not receive host secrets
- Self-dev cannot auto-merge or expand approval/release rights
- No paid inference or unofficial wrappers used in this completion pass

## Pending live validation

- [ ] Provider accounts with **zero-charge**-eligible routes
- [ ] Keys only in local `.env` (never commit); spend policy = zero
- [ ] P15 live canary on verified routes
- [ ] P16 live qualification (multi-route if eligible)
- [ ] Optional P18 live comparisons under verified capacity

## Known limitations

- Live inference and qualification rankings are **unverified**
- Integration DB tests may require `SWARM_DATABASE_URL`
- Console and compose profiles are local/dev oriented
- No cloud production hosting from this pass

## Next (after keys — not started here)

Live P15 → P16 under zero-spend only. Do not treat this RC as fully live-verified.
