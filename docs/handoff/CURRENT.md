# Handoff — V1.4 → V3.0 implementation lane

**Date:** 2026-09-23  
**Branch:** `cursor/cloud-agent-1790175458840-642hd` (off `main` @ `b9141fa`)  
**Plan:** `/opt/cursor/artifacts/plans/v1_to_v3_roadmap_e96337c7.plan.md`  
**Spend:** `SWARM_ALLOW_PAID=false` · **no** public launch · **no** self-accept  

## Phase 0 status

- Coordination docs copied from `coordination/swarm-control` into `docs/coordination/` and `docs/artifacts/future/`.
- V1.4 zero-spend slice already on tip (G10 honesty + local brokered `$0`).
- Next: Phase 1 G11–G14 local transplants, then V1.5–V3.0 per plan.

## Non-negotiable

- Transplant before inventing; reuse FastAPI/SQLAlchemy/Alembic/Pydantic/httpx/pydantic-ai/DBOS.
- No second scheduler, tool permission engine, worker registry, or orchestration framework.
- Missing live capacity = `live-blocked` / `UNKNOWN` / `USER_ACTION`.
