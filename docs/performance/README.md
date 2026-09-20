# Performance / load / chaos (P18)

Offline synthetic load and fault injection. Separate:

| Layer | Meaning |
|---|---|
| logical_sessions | Mission session count under test (not prod capacity) |
| simulated_provider_concurrency | Fake provider envelope |
| actual_concurrency | Host process dispatch bound for the run |

## Commands

```sh
uv run pytest tests/load tests/chaos
uv run swarm load run --scenario adaptive --mode mock --report-dir var/reports/load
uv run swarm load run --scenario fixed --mode mock --tasks 1000 --sessions 100
uv run swarm chaos run --mode mock
```

## Gates

- No oversubscription beyond `actual_concurrency`
- Expansion **and** contraction observed
- Multi-mission fairness (no starvation)
- Fault matrix: uncertain send, stale worker, outbox gap, cloud recovery fence
- `--mode live` blocked until verified account capacity exists
