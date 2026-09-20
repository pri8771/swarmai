# SwarmAI handoff — CURRENT

**Updated:** 2026-09-20T01:16:00Z  
**Packets complete (offline):** P01–P17  
**Branch:** `cursor/p01-foundation-contracts-11e2`  
**Source:** `/Users/pchordia/Downloads/swarm-ai`

## What works

| Packet | Status | Evidence |
|---|---|---|
| P01–P14 | prior | earlier commits through `93ed178` |
| P15 | offline_verified | `7fcc4f8` — onboarding inventory/audit/canary mock; catalog≠configured≠auth |
| P16 | offline_verified | qualify plan/run/report mock; untested nulls; live blocked |
| P17 | offline_verified | `4310a87` — deploy doctor + recovery verify local only |

### P15 details
- Layers: cataloged / implemented / configured (secrets present ≠ authenticated)
- CLI: `providers list|onboarding-report|inspect|canary --mode mock`
- Live canaries refuse without verified zero-charge policy

### P16 details
- `swarm eval plan|run|report` mock path
- Sparse/untested cells stay `null`; no invented rankings
- Fingerprint change → `stale_recheck_required`
- `--mode live` exits 2 with `live_qualification_blocked`

### P17 details
- Profiles: mock / standalone / hybrid / recovery
- `swarm deploy doctor`, `swarm recovery verify`
- Compose + backup manifest local artifacts only

## Exact commands

```sh
cd /Users/pchordia/Downloads/swarm-ai

# P15 offline
uv run pytest tests/onboarding
uv run swarm providers list --mode mock
uv run swarm providers onboarding-report
uv run swarm providers canary --route rt_fake_alpha --mode mock

# P16 mock qualification
uv run pytest tests/evals/test_qualify.py
uv run swarm eval plan --suite starter --purpose evaluation --mode mock
uv run swarm eval run --plan PLAN_ID --mode mock
uv run swarm eval report --run RUN_ID

# P17 local deploy
uv run pytest tests/deployment
uv run swarm deploy doctor --profile standalone
uv run swarm recovery verify --profile recovery

# Combined regression slice
uv run pytest tests/evals/test_qualify.py tests/onboarding tests/deployment
```

## Next

**P18** — scaling/chaos offline (deps P11/P12/P14 start; P17 integration).  
P16 live + multi-source mission remain blocked on keys.

## User actions (live only — paused)

1. Create provider accounts eligible for **zero-charge** canaries (no paid/card activation as workaround).
2. Put keys in local `.env` only (never commit); confirm policy allows zero-spend probes.
3. Re-run P15 live canary on verified routes, then P16 `--mode live` with eligible route IDs.
4. Do **not** push remotes or deploy production from this kit path unless explicitly requested later.

## Mock vs live

| Area | Evidence type |
|---|---|
| P15–P17 | mock / local / simulated |
| P16 rankings | provisional/untested nulls only — not live qualification |
| Spend | none |
