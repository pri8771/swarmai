# SwarmAI — Release Candidate Status

**Date:** 2026-09-20  
**Active version branch:** `cursor/v0.3-scale-orchestration-11e2`  
**V0.3:** swarm scaling **dogfood passed** (64 agents, cost `$0.00`) — see `docs/v0.3/STATUS.md`  
**V0.2:** heterogeneous routing **merged** (PR #4) — see `docs/v0.2/STATUS.md`  
**V0.1:** real mission runtime **dogfood passed** (merged via PR #2 / #3)

## Links

| Item | URL |
|---|---|
| Repo | https://github.com/pri8771/swarmai |
| V0.2 branch | https://github.com/pri8771/swarmai/tree/cursor/v0.2-heterogeneous-routing |
| Prior merged PRs | #1 (RC), #2 (V0.1 runtime), #3 (onboarding) |

## Status

| Dimension | Result |
|---|---|
| V0.2 kit packets P27–P30 | **complete** (live Ollama proof) |
| V0.2 P31 checkpoint | **complete** (Draft PR #4) |
| Provider capability registry | live — 14 auth_ok / paid blocks honored |
| Model qualification | live provisional cells on `gemma3:4b` + `qwen3.5:4b` |
| Evidence router | heterogeneous planner/worker assignment |
| Heterogeneous mission | **passed** mission `08175577fb334c4f9ac64a0895acd25e` cost `$0.00` |
| Spend policy | **zero** (`SWARM_ALLOW_PAID=false`) |
| OpenAI | deferred (payment-gated) |
| Together / Fireworks | auth ok; inference blocked under zero-spend |

## Limitations

- Cloud free-tier **generation** not used for benchmarks (metadata auth probes only).
- Profiles remain provisional (starter archive; not statistical qualified).
- `swarm release verify` matrix still labels historical P01–P21 offline modules; V0.2 live proof is documented in `docs/v0.2/STATUS.md`.
