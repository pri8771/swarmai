# ADR 0002 — DBOS reuse for Swarm lease fencing (V2A-003X)

- Status: proposed (spike evidence; not production migration)
- Date: 2026-09-21
- Packet: V2A-003X
- Artifact: ART-V15-ARCH
- Installed DBOS: 3.0.0 (transitive via `pydantic-ai[dbos]>=2.46,<2.47`)

## Context

Session A needs an implementation-choice spike for durable execution reuse versus the
existing SQLAlchemy/Postgres `LeaseLifecycleService` claim/renew/expire path. Production
queue replacement is out of scope. Public/paid DBOS Conductor is forbidden.

## Options considered

1. **Full reuse** — replace Swarm claim/renew/expire with DBOS queues/workflows.
2. **Partial reuse** — keep Swarm durable authority in Postgres; optionally use DBOS for
   worker-side workflow/step restart after leases are fenced.
3. **Do not adopt** — remain on SQLAlchemy/Postgres only for V2.0.

## Spike evidence

Isolated module: `src/swarm/spike/dbos_lease_mapping.py` (private SQLite system DB only).

Observations:
- `SetWorkflowID` + `@DBOS.step` provide workflow-level idempotency / step durability.
- Swarm-specific fences (`source_revision`, `cancellation_generation`, project match,
  `renewable_until`, terminal task/attempt) are **not** provided by DBOS and were
  demonstrated as caller-owned checks in the spike.
- Restarting the harness clears in-memory FakeLeaseAuthority; durable Swarm stamps must
  remain in Postgres or authority is lost.

Focused tests: `tests/spikes/test_dbos_lease_mapping_spike.py`.

## Decision

**Partial reuse.** Do not adopt DBOS as the Swarm lease/authority store. After
`ART-V15-LEASE-FENCING` claim/renew/expire is lead-verified, DBOS may be considered for
worker execution durability only, with explicit mapping of lease generation / source /
cancel fences at Swarm boundaries.

## Consequences

- No production schema migration from this packet.
- No V1.5/V2 acceptance claim from this spike.
- V2A-004 durable worker service remains the next implementation path for claim clients.
- Revisit only with new spike evidence if DBOS adds first-class multi-tenant fencing
  primitives that match Swarm contracts.
