# SwarmAI handoff — CURRENT

**Updated:** 2026-09-20T00:47:38Z  
**Packets complete:** P01, P02, P03, P08, P04, P05  
**Branch:** `cursor/p01-foundation-contracts-11e2`  
**Source:** `/Users/pchordia/Downloads/swarm-ai`  
**Handoff kit:** `/Users/pchordia/Downloads/SwarmAI_Cursor_Execution_Kit_2026-09-19`

## What works

| Packet | Status | Evidence |
|---|---|---|
| P01 | offline_verified | 14 contract/spike tests |
| P02 | integration_verified | 8 Postgres integration tests |
| P03 | offline_verified | 23 provider fixture tests |
| P08 | offline_verified | tools/sandbox; `swarm sandbox self-test --network off` |
| P04 | offline_verified | extended provider fixture tests |
| P05 | offline_verified | 20 broker tests; `swarm capacity explain --mode mock` |

### P05 details
- SharedInferenceBroker: assess → reserve → invoke → reconcile → explain
- Atomic multi-bucket ledger (deterministic lock order); BYOK/direct share buckets
- Purpose/privacy/cost policy; spending denial before network; unknown-charge deny
- Circuit breaker; single RetryOwner; ambiguous post-send retained
- Control reserve + benchmark envelope; distinct quota dimensions never collapsed
- Evidence is **mock/fake adapter**, not live inference or spend

## Exact commands

```sh
cd /Users/pchordia/Downloads/swarm-ai
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm
uv sync
uv run pytest tests/contracts tests/spikes tests/integration/db tests/providers tests/tools tests/broker
uv run swarm providers list --mode mock
uv run swarm sandbox self-test --network off
uv run swarm capacity explain --mode mock
uv run swarm db validate
```

## Next (kit order)

**P06** evals/qualification (integration_after P02+P05 — satisfied), then **P07** workspace.

## User actions

None for offline work. Provider API keys only for P15–P16 live probes.
