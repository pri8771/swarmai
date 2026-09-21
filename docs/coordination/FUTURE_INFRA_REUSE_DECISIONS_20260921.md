# SwarmAI future infrastructure/reuse decisions

Date: 2026-09-21
Status: PLANNING ONLY

Goal: minimize implementation time and operational complexity by extending the current stack unless a measured gap requires a new dependency.

## Decision 1 — PostgreSQL remains authoritative

Use PostgreSQL/SQLAlchemy/Alembic for:
- durable mission/task/worker state;
- leases/results/effects;
- site authority;
- scheduler fairness state;
- objective/trigger/learning state;
- unique dedupe constraints;
- transactional reservation intents;
- outbox.

For queue-like concurrent claims, PostgreSQL row locking / `FOR UPDATE ... SKIP LOCKED` is an available primitive when appropriate. It is specifically suitable for queue-like multi-consumer access, but not as a substitute for deterministic ordering/fairness policy.

Reference:
https://www.postgresql.org/docs/current/sql-select.html

Do not add Redis/Celery/Kafka/Temporal merely to create a task queue before the PostgreSQL approach is shown insufficient.

## Decision 2 — existing outbox is the event bridge

Reuse `src/swarm/db/outbox.py` for reliable post-transaction event publication.

Future trigger/scheduler/learning events should:
1. persist authority/state transition;
2. persist outbox row in same transaction where appropriate;
3. publish asynchronously/idempotently.

Do not make an external broker the source of truth.

## Decision 3 — DBOS remains partial reuse

The repo already carries Pydantic AI DBOS support and prior architecture chose partial reuse.

Good DBOS candidates:
- long-running worker-side workflows;
- recovery orchestration;
- bounded self-development workflows;
- learning evaluation/canary orchestration;
- durable waits/sleeps where Swarm authority is already frozen outside the workflow.

Not DBOS authority:
- project authorization;
- provider eligibility;
- budget/quota accounting;
- scheduler fairness entitlement;
- lease/result acceptance;
- tool/effect permission;
- SiteEpoch;
- artifact acceptance.

DBOS documents durable workflows/steps and recovery from interruption, and recommends Postgres for production/distributed use.

References:
https://docs.dbos.dev/python/tutorials/workflow-tutorial
https://docs.dbos.dev/python/integrating-dbos

## Decision 4 — no second scheduler

Evolve `src/swarm/controller/scheduler.py`.

V2.3 may split implementation into fairness/reservation/receipt modules, but one Swarm scheduler remains authoritative for mission/task admission and dispatch.

DBOS queue features, if used at all, are execution plumbing after Swarm admission—not fair-share or permission authority.

## Decision 5 — OpenTelemetry optional at V2.3, never audit authority

OpenTelemetry Python traces and metrics are currently stable; logs are still documented as development status.

Recommended V2.3 use:
- optional traces/metrics export;
- correlation IDs derived from Swarm receipt IDs;
- OTEL spans link to immutable Swarm events/receipts.

Do not:
- require an OTEL backend for Swarm correctness;
- treat OTEL retention as audit evidence;
- put secrets/private raw model content into telemetry.

Reference:
https://opentelemetry.io/docs/languages/python/

## Decision 6 — FastAPI/httpx/Pydantic remain integration defaults

Current stack already supports:
- API/control surface: FastAPI;
- HTTP integrations: httpx;
- schema/contracts: Pydantic;
- settings: pydantic-settings;
- persistence: SQLAlchemy/psycopg;
- migrations: Alembic.

Do not add a new framework for ordinary adapters/contracts.

## Decision 7 — capability packs/extensions are metadata + bounded code, not arbitrary marketplace execution

V1.9/V2.3 extension/pack runtime must:
- declare capabilities/scopes;
- be project-enabled;
- use normal ToolGateway/broker;
- have digest/provenance/version;
- be drainable/revocable.

Avoid a generic unrestricted plugin executor.

## Decision 8 — evidence remains Swarm-native

Authoritative acceptance/evidence comes from:
- source/config/candidate digests;
- durable Swarm receipts;
- deterministic tests;
- real live evidence manifests;
- independent review.

External telemetry/workflow systems can support operation but cannot create artifact acceptance.
