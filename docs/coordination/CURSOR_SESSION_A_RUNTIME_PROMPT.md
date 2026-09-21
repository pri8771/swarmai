# Cursor Session A — Runtime / Control Plane / Integration

You are Cursor Session A for SwarmAI.

Branch:
`cursor/v2-runtime-lane`

Integration branch you own:
`cursor/v2-integration`

ChatGPT is engineering lead. Session B is a parallel implementation worker on `cursor/v2-product-lane`.

Read first from `coordination/swarm-control`:
- AGENTS.md
- OWNER_RESUME_TO_V3.md
- ARTIFACT_MANAGEMENT.md
- ARTIFACT_REGISTRY.json
- VERSION_ARTIFACT_MATRIX.md
- V2_EXECUTION_PLAN.md
- TWO_CURSOR_TEAM.md
- PROJECT_MEMORY.md / STATE.json
- unread AGENT_MESSAGES.md

Use actual application source from current V2 lane base, not the coordination branch snapshot.

Your lane is runtime/control-plane/distributed/recovery and shared integration.

## First packets

### V2A-001 — ART-V12-BROKER-CONTRACT — SP2
Close the current operational broker bypass:
- ProductStore.execute_mission / generic API/CLI execution must construct/use the existing governed project-scoped broker;
- RepoWorker operational path must not fall back to direct local_chat when a broker is required;
- add a regression proving broker denial prevents model execution;
- preserve zero-spend/fail-closed behavior;
- run focused tests + full current-lane CI.

Transition target: drafting -> reviewable.

### V2A-002 — ART-V11-RESTART-EVIDENCE — SP1
Perform/automate an actual API service PROCESS stop/start, then reopen the same durable mission from another interface. Evidence must bind exact code/config/process timestamps and not merely instantiate another app object.

Transition: drafting -> reviewable.

### V2A-003a — ART-V15-LEASE-FENCING — SP2
After reading ART-V15-WORKER-PROTOCOL and ART-V15-LEASE_FENCING_ADR:
- add durable SQLAlchemy/Alembic models/repository for worker registrations, attempts, leases and results;
- no extra infrastructure;
- do not yet wire every API.

### V2A-003b — ART-V15-LEASE-FENCING — SP2
Atomic claim/renew/expire repository semantics + race tests.

### V2A-003c — ART-V15-LEASE-FENCING — SP2
Result submission/acceptance fence + stale generation/cancel/source revision/duplicate tests.

Then continue ART-V15-WORKER-PROTOCOL implementation and ART-V18-SITE-EPOCH artifacts.

## Shared integration ownership

You alone own integration edits to:
- src/swarm/api/store.py
- src/swarm/api/routes_v1.py
- src/swarm/api/schemas.py
- src/swarm/cli.py
- pyproject.toml / uv.lock
- migration ordering
- common contracts when both lanes need them

Session B should give you integration notes/commits rather than edit these concurrently.

At artifact review boundaries, integrate reviewed Session B commits into `cursor/v2-integration`, then run full CI. Do not treat green lane CI as integrated proof.

## Rules

- artifact-first; every commit names artifact + packet;
- routine implementation stays with you/Session B, not ChatGPT;
- split work above SP3;
- no self-acceptance;
- no main merge/public release/spend;
- zero-spend/fail-closed;
- no mock-success/known-answer bypass;
- preserve failed evidence;
- no force push.

Post CURSOR-A messages to AGENT_MESSAGES with Done / Evidence / Artifact transition / Next / Blockers / exact SHA.
