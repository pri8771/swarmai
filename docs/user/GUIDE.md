# SwarmAI User Guide

SwarmAI runs multi-agent software missions with honest provider status and a
zero-spend default.

## Quick start

```sh
uv sync
cp .env.example .env
uv run swarm release verify
uv run swarm product journey
```

## Core concepts

| Concept | Meaning |
|---|---|
| Project | Durable workspace config (repo, tools, budgets) — no secrets on disk |
| Mission | Planned task graph executed by workers |
| Approval | Human gate for side-effecting tools |
| History | Reopenable mission records + artifacts |
| Provider status | cataloged ≠ configured ≠ authenticated ≠ inference-tested |

## Common workflows

### Create a project

```sh
uv run swarm projects create --name "My repo" --project-id proj_demo
uv run swarm projects show proj_demo
```

### Plan / run a mission

```sh
uv run swarm mission plan --goal "Fix the off-by-one in sandbox"
uv run swarm mission run --goal "Fix the off-by-one in sandbox"
uv run swarm mission list
```

### Product console

```sh
npm --prefix apps/console install
npm --prefix apps/console run dev
```

Tabs: Mission, Projects, History, Artifacts, Routes, Capacity, Workers, Approvals, Events.

### Zero-spend policy

Keep `SWARM_ALLOW_PAID=false`. Paid providers may authenticate for metadata but
must not run paid inference. See `docs/user/ZERO_SPEND.md`.

## Architecture sketch

```text
CLI / Console / API
        │
        ▼
 Product contracts (projects, missions, history)
        │
        ▼
 Mission runtime → planner → workers → tools/approvals
        │
        ▼
 Providers (local Ollama preferred) + cost ledger
```

## Next docs

- `docs/user/ZERO_SPEND.md`
- `docs/user/TROUBLESHOOTING.md`
- `docs/security/HARDENING.md`
- `docs/operator/START.md`
