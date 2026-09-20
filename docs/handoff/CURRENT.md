# SwarmAI handoff — CURRENT

**Updated:** 2026-09-20T13:15:00Z  
**Packets complete (offline):** P01–P21  
**Label:** `offline-verified-release-candidate`  
**Branch:** `cursor/p01-foundation-contracts-11e2`  
**Remote:** https://github.com/pri8771/swarmai  
**Draft PR:** https://github.com/pri8771/swarmai/pull/1 (do not merge)  
**RC status doc:** `docs/RELEASE_CANDIDATE_STATUS.md`

## What works

| Packet | Status | Notes |
|---|---|---|
| P01–P18 | offline_verified | prior commits |
| P19 | offline_verified | `4b337af` self-dev pack; patch artifact; no auto-merge |
| P20 | offline_verified | `816997a` review checklist + regressions; live skip |
| P21 | offline_verified | `release verify` → offline-verified-release-candidate |

### P19
- Isolated worktree, independent reviewer ≠ worker
- Variants: good / failing / malicious
- Host secrets not forwarded into sandbox

### P20
- Checklist C01–C12 with evidence IDs; C10 = skip_live
- Regressions: double-settle, stale worker, privilege expansion
- Distinguishes software ready vs accounts/deploy unprovisioned

### P21
- `swarm release verify`, `docs/release/`, `docs/operator/START.md`
- Fresh-install demo path exercised
- Honest matrix: live_tested=no, deployed=no

## Exact commands

```sh
cd /path/to/swarm-ai
uv run pytest tests/selfdev tests/regressions tests/release -q
uv run swarm demo self-development --mode mock
uv run swarm review report
uv run swarm release verify
uv run swarm demo parser-issue --mode mock --report-dir var/reports/fresh-install
```

## Next

Kit offline packets **complete**. Remaining work is **live** (paused) or maintenance.

## User actions (live only — paused)

1. Zero-charge-eligible provider accounts (no paid/card workaround).
2. Keys in local `.env` only; spend policy = zero.
3. P15 live canary → P16 live qualification → optional P18 live.
4. Explicit authorization required before push, production, or public launch.

## Mock vs live

All P01–P21 evidence this session is **mock/local/simulated**. No spend, no push, no production.
