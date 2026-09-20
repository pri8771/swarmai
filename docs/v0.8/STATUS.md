# SwarmAI V0.8 Status — Product Experience

**Date:** 2026-09-20  
**Branch:** `cursor/v0.8-product-experience-11e2`  
**Interval commits:** IN FORCE (packet + version-checkpoint commits; secret-scan before push)

## Proof

`swarm product journey` exercised the full local user path:

1. Create durable project config (`proj_demo`, `allow_paid=false`, no secrets on disk)
2. Submit + watch mission via authenticated `/v1` API
3. Approve a gated tool write (permission resume)
4. Persist mission with artifacts + timeline
5. History search / reopen / artifact inspect
6. CLI/API public contract alignment (internal fields stripped)

```text
ok: true
cost_usd: 0.0
spend_policy: zero
mock_vs_live: live_local_product_journey_api_cli_tools
report: var/reports/product/latest_journey_proof.json
```

## Packets

| Packet | Result |
|---|---|
| P57 API/CLI product contract | complete — `swarm product contract`, `/v1/product/contract` |
| P58 Mission-control UI | complete — Projects / History / Artifacts console tabs |
| P59 Projects + configuration | complete — `swarm projects create\|list\|show\|update` |
| P60 History + artifact UX | complete — `swarm product history\|reopen\|artifacts` |
| P61 Product checkpoint | complete — journey proof + tests |

## CLI

- `swarm projects create|list|show|update`
- `swarm product contract|journey|history|reopen|artifacts`

## API

- `GET/POST /v1/projects`, `GET/PATCH /v1/projects/{id}`
- `GET /v1/missions`, `GET /v1/missions/{id}/report`, `GET /v1/missions/{id}/artifacts`
- `GET /v1/history`, `GET /v1/history/{mission_id}`
- `GET /v1/product/contract`

## Tests

- `uv run pytest tests/product/test_product.py tests/api/test_api.py` — pass
- `apps/console` vitest — 11 pass

## Limitations

- Journey uses a planned/persisted mission with real permission gate + API create; full Ollama end-to-end mission run remains available via `swarm mission run`.
- Console live mode still merges partial capacity; primary UX proof is fixture + API contract alignment.
