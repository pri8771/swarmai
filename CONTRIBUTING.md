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

### V2.3 work (2026-09-26)

- Branch from `cursor/sw-v23-integration-460c` and open a **draft** PR to it, never to `dev` or `main` (decision C1 in `docs/swarm-mvp/DECISIONS.md`).
- Each session follows its prompt in `docs/plans/v2.3/prompts/` and ends its handoff with a Codex review packet.
- The independent reviewer is Codex (D2). Authors never accept their own work.

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
