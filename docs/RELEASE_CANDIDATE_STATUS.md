# SwarmAI — Release Candidate Status

**Date:** 2026-09-20  
**Active version branch:** `cursor/v0.8-product-experience-11e2`  
**Interval commits:** IN FORCE  
**V0.8:** product experience **dogfood passed** — see `docs/v0.8/STATUS.md`  
**V0.7:** reliability **dogfood passed** — see `docs/v0.7/STATUS.md`  
**V0.6:** self-dev **dogfood passed** — see `docs/v0.6/STATUS.md`  
**V0.5:** tools/permissions **dogfood passed** — see `docs/v0.5/STATUS.md`  
**V0.4:** memory/recovery **dogfood passed** — see `docs/v0.4/STATUS.md`  
**V0.3:** swarm scaling **dogfood passed** (64 agents, cost `$0.00`) — see `docs/v0.3/STATUS.md`  
**V0.2:** heterogeneous routing **merged** (PR #4) — see `docs/v0.2/STATUS.md`  
**V0.1:** real mission runtime **dogfood passed** (merged via PR #2 / #3)

## Links

| Item | URL |
|---|---|
| Repo | https://github.com/pri8771/swarmai |
| V0.8 branch | https://github.com/pri8771/swarmai/tree/cursor/v0.8-product-experience-11e2 |
| Prior merged PRs | #1–#9 |

## Status

| Dimension | Result |
|---|---|
| V0.8 kit packets P57–P60 | **complete** (journey proof `$0.00`) |
| V0.8 P61 checkpoint | **in progress** (Draft PR) |
| Product contract | CLI + `/v1` aligned; internal fields stripped |
| Projects config | durable under `var/projects/` (gitignored; no secrets) |
| History / artifacts | searchable reopen via CLI + API + console |
| Mission-control UI | Projects / History / Artifacts tabs |
| Spend policy | **zero** (`SWARM_ALLOW_PAID=false`) |

## Limitations

- Full live Ollama mission remains optional for the product journey (plan + permission + API + history cover the UX contract).
- OpenAI still deferred (payment-gated).
