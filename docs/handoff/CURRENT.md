# SwarmAI handoff — CURRENT

**Updated:** 2026-09-20T00:49:48Z  
**Packets complete:** P01, P02, P03, P08, P04, P05, P06  
**Branch:** `cursor/p01-foundation-contracts-11e2`  
**Source:** `/Users/pchordia/Downloads/swarm-ai`  
**Handoff kit:** `/Users/pchordia/Downloads/SwarmAI_Cursor_Execution_Kit_2026-09-19`

## What works

| Packet | Status | Evidence |
|---|---|---|
| P01–P05, P08, P04 | offline/integration as prior | see previous commits |
| P06 | offline_verified | 11 eval tests; dataset validate; mock plan |

### P06 details
- `benchmarks/starter.jsonl` (128 cases from kit)
- Graders: `json_exact`, `topological_order` (any valid DAG), `python_unit` via IsolatedCodeRunner
- Leakage protection: only `case.input` to model
- Wilson lower bound; provisional vs qualified (starter cannot auto-qualify)
- Alias→stale; policy→quarantine; simulated scores excluded from live tables
- Evidence is **fixtures/sandbox**, not live qualification matrix

## Exact commands

```sh
cd /Users/pchordia/Downloads/swarm-ai
uv sync
uv run pytest tests/broker tests/evals tests/tools tests/providers
uv run swarm capacity explain --mode mock
uv run swarm eval validate-dataset benchmarks/starter.jsonl
uv run swarm eval plan --suite starter --mode mock
```

## Next (kit order)

**P07** scoped workspace / context (integration_after P02+P05 — satisfied).

## User actions

None for offline work. Live provider keys only for P15–P16.
