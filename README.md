# SwarmAI

Elastic multi-provider problem-solving swarm. Missions plan and launch collaborating
agents, use several model providers concurrently, adapt the task graph, verify results,
and preserve durable state. Small models are used where measured fitness supports them.

This repository is the product source. Planning/handoff files live separately in the
Cursor execution kit and must not be overwritten by this tree.

**Current label:** V2.3 implementation-complete candidate (not accepted) — **not** a public launch.

**V2.3 operator commands:** `swarm v23 --help` (offline scheduler/pack/portability tools).
Deterministic acceptance campaign: `uv run python scripts/v23_acceptance_campaign.py`.

## Requirements

- Python 3.12 (pinned; `<3.14`)
- [uv](https://docs.astral.sh/uv/)
- Node 20+ optional (operator console)

## Setup

```sh
cd /path/to/swarm-ai
uv sync
cp .env.example .env   # optional; mock demos work without keys
```

**Portable install (primary):** [`docs/install/FRESH_INSTALL.md`](docs/install/FRESH_INSTALL.md)  
**Reference hosts only:** [`docs/reference/`](docs/reference/README.md)

## Fresh-install / RC verify

```sh
uv run swarm release install-check
uv run swarm release harden
uv run swarm release verify
uv run swarm release demo-suite
uv run pytest tests/contracts tests/selfdev tests/regressions tests/release tests/product -q
```

Or: `bash examples/v0_9/run_rc_demo.sh`  
Portable mock example: [`examples/fresh-install/`](examples/fresh-install/README.md)

## Operator start

See [`docs/operator/START.md`](docs/operator/START.md), [`docs/install/`](docs/install/README.md), and [`docs/user/GUIDE.md`](docs/user/GUIDE.md).

## Useful commands

```sh
uv run swarm serve --port 8765
uv run swarm product journey
uv run swarm projects list
uv run swarm providers onboarding-report
uv run swarm demo self-development --mode mock
uv run swarm reliability proof
uv run swarm deploy doctor --profile standalone
uv run swarm deploy doctor --profile mock --require-start
```

## Status vocabulary

cataloged / implemented / configured / authenticated / inference-tested / task-qualified
are distinct. Missing credentials do not block offline mocks or contract work.

Keep `SWARM_ALLOW_PAID=false` unless spend is explicitly authorized.

## Handoff

- Live progress: `docs/handoff/CURRENT.md`
- RC notes: `docs/release/RELEASE_CANDIDATE.md`
- Zero-spend: `docs/user/ZERO_SPEND.md`
- Security: `docs/security/HARDENING.md`
