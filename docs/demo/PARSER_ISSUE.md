# Parser-issue dynamic demo

Offline mock demonstration of SwarmAI's dynamic swarm loop against a synthetic
CSV parser bug.

## What is real vs mocked

| Component | Status |
|---|---|
| MissionController / AdaptiveScheduler | real |
| SharedInferenceBroker (fixtures) | real code, mock routes |
| WorkerRegistryService | real membership |
| ProductStore / events | real in-memory API store |
| pytest on synthetic repo | real |
| Model completions | **fake / simulated** — no provider keys |

## Commands

```sh
cd /path/to/swarm-ai
uv run pytest tests/e2e
uv run swarm demo parser-issue --mode mock --report-dir var/reports/demo
```

## Acceptance

Final acceptance is asserted from test artifacts (`baseline` fails, wrong patch
caught, correct patch passes) — not from a model message.
