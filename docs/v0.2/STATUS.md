# SwarmAI V0.2 Status — Heterogeneous Model + Provider Intelligence

**Date:** 2026-09-20  
**Branch:** `cursor/v0.2-heterogeneous-routing`  
**Spend policy:** `SWARM_ALLOW_PAID=false` (total mission cost `$0.00`)

## Objective

Use approved available inference sources concurrently and route tasks using
measured capability, cost, latency, context, availability, and task size.

## Packets

| Packet | Status | Commit / evidence |
|---|---|---|
| P27 Provider capability registry | done | `c25e8b8`; CLI `swarm providers capability-report --save` |
| P28 Real model qualification benchmarks | done | `3766828`; CLI `swarm eval qualify-live` |
| P29 Evidence-based model router | done | `95ecf76`; CLI `swarm eval route` |
| P30 Concurrent heterogeneous mission | done | mission `08175577fb334c4f9ac64a0895acd25e` |
| P31 V0.2 checkpoint | done | Draft PR #4 → merge when exit criteria pass |

## Real proof (P30)

- **Goal:** Fix off-by-one in `sandbox/selfdev_issue/parser_helper.py`
- **Status:** `completed` / accepted
- **Heterogeneous:** yes — planner=`gemma3:4b`, worker=`qwen3.5:4b`, verifier/reviewer=`gemma3:4b`
- **Providers:** local Ollama only (cloud paid inference blocked; OpenAI deferred)
- **Cost:** `$0.00` (3 inference requests recorded in ledger)
- **Evidence paths (local, gitignored under `var/`):**
  - `var/reports/missions/08175577fb334c4f9ac64a0895acd25e/mission-report.json`
  - `var/routing/latest_mission_route_plan.json`
  - `var/reports/qualification/latest_live_benchmark.json`
  - `var/providers/capability-registry.json`

## Routing rationale (recorded)

Evidence router used P28 live benchmark cells under zero-spend policy:
- `implement` → `qwen3.5:4b` (best `code_generation` pass rate)
- `inspect` / `verify` / `review` → `gemma3:4b` (planning/latency-oriented + diversification)

## Limitations

- Live generation benchmarks run on Ollama only; cloud free-tier generation not exercised (paid-risk under zero-spend).
- Together/Fireworks remain `auth_ok_inference_blocked`; OpenAI deferred (payment-gated).
- Starter archive yields provisional profiles only (not statistically `qualified`).
- Concurrentism is sequential task graph with per-role model assignment (not multi-worker parallel GPU batching).

## Commands

```bash
uv run swarm providers capability-report --save
uv run swarm eval qualify-live --max-cases 6 --model gemma3:4b --model qwen3.5:4b
uv run swarm eval route
uv run swarm mission run --goal "Fix the off-by-one bug in sandbox/selfdev_issue/parser_helper.py..."
```
