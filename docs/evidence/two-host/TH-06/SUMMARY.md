# TH-06 evidence summary

**Date:** 2026-09-25T15:51Z  
**Hostname:** `swarm.splitsignal.ai`  
**Server:** `http://127.0.0.1:18766`

## Qualification status

| Runtime | Availability | Mission admissible | Notes |
|---|---|---|---|
| Native | **available** | **yes** | Partial capability proof (TH-02/TH-04); other caps unproven |
| OpenCode | **discovered_unqualified** | **no** | Binary present (`v2.0.15`); config ≠ SwarmAI enforcement |
| Hermes | **unavailable** | **no** | Not installed; native path unaffected |

**Policy:** `config_alone_enforces_swarm_contracts: false` on every runtime.

## Results

| Check | Result |
|---|---|
| pytest `test_runtime_adapters_th06` | **pass** (6) |
| Local qualification report honesty | **pass** |
| `GET /v1/runtimes` on loopback | **pass** |
| OpenCode not mission-admissible | **pass** |
| Hermes unavailable | **pass** |
| No live inference / no Hermes install / no OpenCode service start | **honored** |

## Commands

```sh
uv run pytest tests/runtime/test_runtime_adapters_th06.py -q
uv run python scripts/th06_runtime_qualification.py
curl -fsS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:18766/v1/runtimes
```

## Not run / blocked

R730, `.ai` DNS, Cloudflare Tunnel, Linear MCP (`needsAuth`), Hermes install, OpenCode headless mission mediation, paid/live model qualification, nested OpenCode/Hermes subagent trees.
