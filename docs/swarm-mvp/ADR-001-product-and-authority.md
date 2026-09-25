# ADR-001 — Product and authority baseline

**Status:** accepted  
**Date Recorded:** 2026-09-25  
**Actual Start Date:** 2026-09-25  
**Related Prompt:** Project two-host implementation mandate  
**Related Decision:** DEC-TH-001

## Context

Planning bundle (2026-09-25) defines the autonomous-agent MVP. Repository coordination still scopes LIVE V1.7 on `cursor/v17-single-session`. Project mandate authorizes a parallel two-host MVP lane without overwriting that owner.

## Decision

- Product definition: individual agents pursuing one collective mission; crews optional.
- Authority: one kernel for admission, permissions, budgets, ownership, lifecycle, acceptance.
- Stack: FastAPI + React/Vite + PydanticAI + PostgreSQL + one DBOS substrate (compatibility spike pending).
- Inference: HTTP client to separate `inference_server` only; free-only default; no silent paid fallback.
- MCP: generic; Linear is tracking only, not a runtime dependency.
- Implementation location: isolated worktree/branch `cursor/two-host-mvp-b28d` from `origin/main` @ `08b910f981eff2ab66873a71055090f2c60f2a91`.

## Consequences

V1.7 recovery continues on its own branch. This lane adopts planning docs under `docs/swarm-mvp/` and executes P00→TH-01 first.
