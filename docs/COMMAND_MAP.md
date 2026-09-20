# Command map (subsequent packets)

| Intent | Command |
|---|---|
| Install | `uv sync` |
| Contract + spike tests | `uv run pytest tests/contracts tests/spikes` |
| Full offline unit suite | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Types | `uv run mypy src/swarm` |
| API (mock mode) | `uv run swarm serve --port 8765` |
| Health live | `curl -s http://127.0.0.1:8765/health/live` |
| Health ready | `curl -s http://127.0.0.1:8765/health/ready` |
| Export JSON Schema | `uv run python -m swarm.contracts.export_schemas` |
| DB migrate | `uv run swarm db migrate` |
| DB validate | `uv run swarm db validate` |
| DB integration tests | `SWARM_DATABASE_URL=... uv run pytest tests/integration/db` |
| Providers (mock) | `uv run swarm providers list --mode mock` |
| Sandbox self-test | `uv run swarm sandbox self-test --network off` |
| Capacity explain (mock) | `uv run swarm capacity explain --mode mock` |
| Broker tests | `uv run pytest tests/broker` |

PostgreSQL integration path (P02+; optional for P01):

```sh
export SWARM_DATABASE_URL=postgresql://swarm:swarm@127.0.0.1:5432/swarm
uv run pytest tests/integration/db -m integration
```

Kit offline checks (from handoff directory, use Python 3.12):

```sh
python3.12 verify_kit.py
python3.12 benchmark_tools.py validate
python3.12 test_helpers.py
```
