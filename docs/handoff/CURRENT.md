# SwarmAI handoff — CURRENT

**Updated:** 2026-09-20T01:20:00Z  
**Packets complete (offline):** P01–P18  
**Branch:** `cursor/p01-foundation-contracts-11e2`  
**Source:** `/Users/pchordia/Downloads/swarm-ai`

## What works

| Packet | Status | Evidence |
|---|---|---|
| P01–P14 | prior | through `93ed178` |
| P15 | offline_verified | `7fcc4f8` onboarding layers + mock canaries |
| P16 | offline_verified | `e8f4d2b` eval plan/run/report mock; live blocked |
| P17 | offline_verified | `4310a87` deploy doctor + recovery local |
| P18 | offline_verified | load 1000 tasks + chaos matrix mock |

### P15–P17 (prior turn)
- Cataloged ≠ implemented ≠ configured ≠ authenticated
- Qualification nulls for untested; fingerprint demotion
- Deploy profiles mock/standalone/hybrid/recovery — no production push

### P18 details
- Adaptive + fixed strategies under same synthetic envelope
- 100 logical sessions, 1000 queued tasks, bounded `actual_concurrency`
- Expand **and** contract observed; no oversubscription / starvation
- Faults: uncertain send, stale worker, outbox gap, cloud recovery fence
- `--mode live` exits 2 until account capacity verified

## Exact commands

```sh
cd /Users/pchordia/Downloads/swarm-ai

# P15–P16 offline
uv run pytest tests/onboarding tests/evals/test_qualify.py
uv run swarm providers onboarding-report
uv run swarm eval plan --suite starter --purpose evaluation --mode mock
uv run swarm eval run --plan PLAN_ID --mode mock

# P17 local
uv run pytest tests/deployment
uv run swarm deploy doctor --profile standalone
uv run swarm recovery verify --profile recovery

# P18
uv run pytest tests/load tests/chaos
uv run swarm load run --scenario adaptive --mode mock --tasks 1000 --sessions 100
uv run swarm chaos run --mode mock
```

## Next

**P19** — controlled self-development (deps P08, P14 already offline_verified).  
Live P15/P16/P18 remain paused on keys.

## User actions (live only — paused)

1. Create provider accounts eligible for **zero-charge** canaries (no paid/card activation as workaround).
2. Put keys in local `.env` only (never commit); confirm policy allows zero-spend probes.
3. Re-run P15 live canary → P16 `--mode live` with eligible route IDs → optional P18 live comparisons.
4. Do **not** push remotes or deploy production unless explicitly requested later.

## Mock vs live

| Area | Evidence |
|---|---|
| P15–P18 | mock / local / simulated only |
| Spend | none |
| Push / production | none |
