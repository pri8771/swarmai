# SwarmAI

Elastic multi-provider problem-solving swarm. Missions plan and launch collaborating
agents, use several model providers concurrently, adapt the task graph, verify results,
and preserve durable state. Small models are used where measured fitness supports them.

This repository is the product source. Planning/handoff files live separately in the
Cursor execution kit and must not be overwritten by this tree.

**Current label:** offline-verified release candidate (not cloud-operating / not live-qualified).

## Requirements

- Python 3.12 (pinned; kit helper scripts also expect <3.14)
- [uv](https://docs.astral.sh/uv/)
- Node 20+ optional (operator console)

## Setup

```sh
cd /path/to/swarm-ai
uv sync
cp .env.example .env   # optional; mock demos work without keys
```

## Fresh-install / RC verify

```sh
uv run swarm release verify
uv run pytest tests/contracts tests/selfdev tests/regressions tests/release -q
uv run swarm demo parser-issue --mode mock --report-dir var/reports/fresh-install
```

## Operator start

See [`docs/operator/START.md`](docs/operator/START.md).

## Useful commands

```sh
uv run swarm serve --port 8765
uv run swarm providers onboarding-report
uv run swarm demo self-development --mode mock
uv run swarm load run --scenario adaptive --mode mock --tasks 200
uv run swarm chaos run --mode mock
uv run swarm review report
uv run swarm deploy doctor --profile standalone
```

## Status vocabulary

cataloged / implemented / configured / authenticated / inference-tested / task-qualified
are distinct. Missing credentials do not block offline mocks or contract work.

## Handoff

- Kit path (read-only planning): set in `.swarm-build-state.json`
- Live progress: `docs/handoff/CURRENT.md`
- RC notes: `docs/release/RELEASE_CANDIDATE.md`
