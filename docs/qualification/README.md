# Live/model qualification (P16)

Offline/mock scaffolding only until P15 zero-charge routes are verified.

## Commands

```sh
uv run swarm eval plan --suite starter --purpose evaluation --mode mock
uv run swarm eval run --plan PLAN_ID --mode mock
uv run swarm eval report --run RUN_ID
```

Plans land in `benchmarks/live-plans/` (mock plans are still stored here as artifacts).  
Reports land in `var/reports/qualification/`.

## Rules

- Untested cells stay `null` — no invented rankings
- Mock vs live labels must not be confused
- `--mode live` is blocked until operator completes P15 access + zero-charge proof
- Fingerprint/alias change demotes cells to `stale_recheck_required`
