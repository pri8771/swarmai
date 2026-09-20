# Contributing

Thanks for helping improve SwarmAI.

## Development setup

```sh
uv sync
cp .env.example .env
uv run swarm release first-run
uv run pytest -q
```

## Branching

- Feature work on `cursor/<topic>-11e2` branches
- Prefer small, reviewable commits (packet / coherent sub-slice)
- Secret-scan before push; never commit `.env` or keys

## Tests

```sh
uv run pytest tests/contracts tests/product tests/release -q
uv run swarm release verify
uv run swarm release harden
```

## Spend policy

Keep `SWARM_ALLOW_PAID=false` unless an operator explicitly authorizes spend
and records it in proof JSON.

## Pull requests

- Describe the real proof run (command, cost, evidence path)
- Link related `docs/v*/STATUS.md` updates
- Do not claim live-qualified or publicly launched without evidence

## Code of conduct

Be respectful. No harassment. Report security issues privately — see `SECURITY.md`.
