# SwarmAI handoff — CURRENT

**Updated:** 2026-09-20T13:20:00Z  
**Packets complete (offline):** P01–P21  
**Label:** `offline-verified-release-candidate`  
**Branch:** `cursor/p01-foundation-contracts-11e2`  
**Remote:** https://github.com/pri8771/swarmai  
**PR:** https://github.com/pri8771/swarmai/pull/1  
**RC status doc:** `docs/RELEASE_CANDIDATE_STATUS.md`

## Live status (honest)

| Packet | Live | Reason |
|---|---|---|
| P15 | blocked | no `.env` / no process provider keys |
| P16 | blocked | no eligible live routes from P15 |
| P18 | skipped | no keys; mock soak/chaos already offline_verified |

**Spend:** none. **Payment methods:** none added.

## What works (offline)

| Packet | Status | Notes |
|---|---|---|
| P01–P14 | offline_verified | prior commits |
| P15 | offline_verified / live blocked | catalog≠configured≠auth |
| P16 | offline_verified / live blocked | mock qualify; live mode blocked |
| P17 | offline_verified | deploy doctor + recovery local |
| P18 | offline_verified / live skipped | mock load+chaos |
| P19–P21 | offline_verified | self-dev, review, RC verify |

## Exact commands

```sh
cd /path/to/swarm-ai
uv run pytest tests/selfdev tests/regressions tests/release -q
uv run swarm release verify
uv run swarm demo parser-issue --mode mock --report-dir var/reports/fresh-install
uv run swarm deploy doctor --profile standalone
uv run swarm serve --host 127.0.0.1 --port 8765
```

## User actions for live (paused)

1. `cp .env.example .env` and add zero-charge-eligible keys only (never commit).
2. Confirm spend policy = zero; keep `SWARM_ALLOW_PAID=false`.
3. `uv run swarm providers onboarding-report` then live canary on free routes only.
4. Then P16 live eval with eligible route IDs.

## Mock vs live

This completion pass: **offline/mock only**. No live provider calls.
