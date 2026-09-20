# ADR 0001 — Dependency pins for P01 foundation

- Status: accepted
- Date: 2026-09-19
- Packet: P01

## Context

P01 requires a mutually compatible stable set for Python, PydanticAI, DBOS, FastAPI, and
a PostgreSQL client. Older PydanticAI/DBOS wrapper examples (`DBOSAgent`) are deprecated
in favor of the `DBOSDurability` capability (S02).

## Decision

| Package | Pin | License (as packaged) | Notes |
|---|---|---|---|
| Python | `>=3.12,<3.14` | PSF | 3.14 breaks handoff `argparse` help strings; pin away from 3.14 for now |
| pydantic | `>=2.10,<2.14` | MIT | Contract models |
| pydantic-ai[dbos] | `>=2.46,<2.47` | MIT | Uses `DBOSDurability`, not deprecated `DBOSAgent` |
| dbos (transitive) | 3.x | MIT / DBOS license as published | Open-source library only; no Conductor required |
| fastapi | `>=0.115,<0.142` | MIT | Health + future API |
| uvicorn | `>=0.32,<0.54` | BSD-3 | Local server |
| psycopg[binary] | `>=3.2,<3.4` | LGPL-3 | PostgreSQL client for later packets |
| sqlalchemy | `>=2.0,<2.1` | MIT | Persistence groundwork |

Exact installed versions are recorded in `uv.lock` and `.swarm-build-state.json`.

## Consequences

- Spike tests must construct agents with `capabilities=[DBOSDurability()]` and call
  `agent.run()` inside `@DBOS.workflow()`.
- No paid DBOS Conductor or Logfire dependency.
- A proven compatibility failure may justify one documented pin adjustment; do not reopen
  product architecture.
