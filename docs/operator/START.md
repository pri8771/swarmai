# Operator start (one page)

**Portable install (primary):** [`docs/install/`](../install/README.md)

## 1. Install

```sh
uv sync
cp .env.example .env   # add keys later; mock path works without them
```

## 2. Prove offline health

```sh
uv run swarm release verify
uv run swarm demo parser-issue --mode mock --report-dir var/reports/demo
uv run swarm providers onboarding-report
uv run swarm deploy doctor --profile mock
```

## 3. Optional console

```sh
npm --prefix apps/console install
npm --prefix apps/console run dev -- --host 127.0.0.1 --port 5173
```

## 4. Server / worker (when needed)

See [`docs/install/SERVER_WORKER_STARTUP.md`](../install/SERVER_WORKER_STARTUP.md).  
Named-host reference guides only: [`docs/reference/`](../reference/README.md).

## Troubleshooting

| Symptom | Action |
|---|---|
| Provider quota unavailable | Stay on `--mode mock`; do not invent live connected status |
| Worker offline | `uv run swarm worker self-test --mode mock`; check lease/heartbeat |
| Deploy doctor fails | `uv run swarm deploy doctor --profile mock` then `standalone --require-start` |
| Want live canaries | Supply zero-charge keys in `.env` only; never commit |

## Authority

- Operator admits missions / merges patches
- Workers never hold production secrets
- Self-dev produces patch artifacts only (no auto-merge)
