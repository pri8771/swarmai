# SwarmAI

Elastic multi-provider problem-solving swarm. Missions plan and launch collaborating
agents, use several model providers concurrently, adapt the task graph, verify results,
and preserve durable state. Small models are used where measured fitness supports them.

This repository is the product source. Planning/handoff files live separately in the
Cursor execution kit and must not be overwritten by this tree.

## Requirements

- Python 3.12 (pinned; kit helper scripts also expect <3.14)
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
cd /path/to/swarm-ai
uv sync
```

## Commands (P01)

```sh
uv sync
uv run pytest tests/contracts tests/spikes
uv run ruff check .
uv run mypy src/swarm
uv run swarm serve --port 8765
```

Health checks (with server running):

```sh
curl -s http://127.0.0.1:8765/health/live
curl -s http://127.0.0.1:8765/health/ready
```

## Status vocabulary

cataloged / implemented / configured / authenticated / inference-tested / task-qualified
are distinct. Missing credentials do not block offline mocks or contract work.

## Handoff

- Kit path (read-only planning): set in `.swarm-build-state.json`
- Live progress: `docs/handoff/CURRENT.md`
