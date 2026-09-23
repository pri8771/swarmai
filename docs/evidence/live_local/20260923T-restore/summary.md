# live_local restore run — 2026-09-23

Branch: `cursor/restore-live-local-tests-712f`
Suite tip at run: `042844bfbe5a1aa73854bee2dcad7b64f847bc32` (pre-evidence-docs commit; rebind after final push)

## Commands

```sh
SWARM_LIVE_LOCAL=1 SWARM_ALLOW_PAID=false uv run pytest -m live_local -q --tb=short
SWARM_ALLOW_PAID=false uv run swarm providers canary --route rt_ollama_default --policy bounded_probe --mode live --billing-known-zero
```

## Results (honest)

| Check | Result |
|---|---|
| pytest `-m live_local` | **10 passed, 1 skipped**, 399 deselected |
| Skipped | `test_service_binds_loopback_only` — `no non-loopback address to probe on this host` (environment has only loopback hostname IP) |
| Ollama canary | **canaried**, `cost_usd: 0.0`, `billing_known_zero: true`, `endpoint_loopback: true` |
| Paid/cloud | `SWARM_ALLOW_PAID=false` throughout; fail-closed in `tests/conftest.py` |

## Not claimed

- 11/11 fixture passes (1 intentional skip on this host)
- Default GitHub Actions live execution (manual `workflow_dispatch` only)
- Paid/cloud provider live

## How to reproduce

```sh
SWARM_LIVE_LOCAL=1 SWARM_ALLOW_PAID=false uv run pytest -m live_local -q --tb=short
```

Unset `SWARM_LIVE_LOCAL` → 11 skipped (never counted as pass).
