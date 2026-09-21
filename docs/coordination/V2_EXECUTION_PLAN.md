# SwarmAI execution plan — current state -> V2.0 candidate -> V2.3 -> V3.0

Adopted: 2026-09-20
Owner direction: resume engineering, work as one lead + two Cursor implementation sessions, artifact-first. Major milestones are V1.7, V2.3 and V3.0. Immediate target is at least a V2.0 implementation/artifact-complete candidate today.

## Truth boundary

The prior V1.4 abrupt stop is superseded by the owner's new resume/acceleration directive.

Implementation may proceed through V3.0. This does NOT independently authorize:
- main merge;
- tag/release/public launch;
- destructive production changes;
- additional spend / paid fallback.

Zero-additional-spend remains the default.

Time-bound acceptance is not compressible. The existing V1.4 contract requires a real 24-hour observation window; V2.0 also needs reliability observation. Therefore today's executable target is:

**V2.0 implementation/artifact-complete reviewable candidate**, while wall-clock acceptance artifacts continue honestly.

Never relabel an unelapsed observation window as passed.

## Milestone model

### Milestone V1.7 — complete core platform

V1.7 milestone means the product has:
1. the current V1.4 elastic swarm foundations;
2. durable distributed workers (V1.5 capability group);
3. scoped reusable knowledge (V1.6 capability group);
4. unified tools/browser permission/session model (V1.7 capability group).

V1.5 and V1.6 remain artifact groups, not separate operator stop points.

### Immediate target V2.0 — complete deployable product candidate

V2.0 candidate additionally includes:
5. cloud/local recovery architecture + implementation (V1.8 group);
6. clean-install/beta/extension/self-development readiness (V1.9 group);
7. integrated V2.0 support/install/reliability/release artifacts.

Implementation can be complete before the required observation windows finish. Acceptance cannot.

### Milestone V2.3 — operational platform

V2.1–V2.3 are one artifact tranche ending in the V2.3 milestone:
- multi-mission scheduling/resource fairness;
- capability-pack/extension lifecycle;
- stronger observability/operations/admin surface;
- portability/export/import;
- controlled cross-project/fleet operations needed before persistent objectives.

Exact sub-artifacts are refined while V2.0 builds.

### Milestone V3.0 — persistent learning operations

V3.0 integrates:
- persistent authorized objectives;
- event/schedule-created missions;
- governed operational learning and rollback;
- controlled self-development;
- cross-project resource allocation;
- reusable signed capability ecosystem;
- stronger fleet/tenancy/audit.

## Current repo baseline

Application branch at resume:
- PR #14 / cursor/v1.4-live-integration-11e2
- frozen tip at abrupt stop: 2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea
- last application-source change: d9da26c7a8b47d1ffeabf866250cdbf30d14ffce

Reusable foundations already present:
- durable mission store/API/CLI/console;
- generic task-family execution;
- broker/admission primitives;
- worker registration, generation, heartbeat, drain and stale-result fencing;
- memory store with bounded retrieval;
- tool registry/gateway, payload-bound approvals and receipts;
- self-development sandbox/policy scaffolding;
- PostgreSQL/Alembic/FastAPI stack;
- standalone compose;
- evaluation/routing/screening framework;
- console/operator surfaces.

Do not replace these with another framework unless the current implementation cannot satisfy a required contract.

## Team topology

### ChatGPT — engineering lead / artifact owner

Owns:
- artifact registry and dependency graph;
- architecture/ADRs/contracts;
- hard debugging/review;
- acceptance/evaluation design;
- provider/recovery/security research;
- cross-lane integration decisions;
- independent artifact verification;
- next-packet generation.

The lead stays one artifact ahead of both Cursor lanes.

### Cursor Session A — Runtime / control plane / integration owner

Branch: cursor/v2-runtime-lane

Owns primarily:
- src/swarm/workers/**
- distributed worker persistence/protocol;
- mission/broker/runtime wiring required for control plane;
- src/swarm/db/** / migrations / deployment;
- recovery/site authority implementation;
- tests/workers/**, distributed/recovery integration tests;
- shared integration branch merges.

Session A is the **integration owner** for shared:
- src/swarm/api/store.py
- src/swarm/api/routes_v1.py
- src/swarm/api/schemas.py
- src/swarm/cli.py
- pyproject.toml / uv.lock
- migrations ordering
- common contracts when both lanes need them.

Session B should not directly edit those shared files unless Session A explicitly hands off ownership.

### Cursor Session B — Knowledge / tools / product / beta

Branch: cursor/v2-product-lane

Owns primarily:
- src/swarm/memory/**
- src/swarm/tools/**
- src/swarm/selfdev/**
- new extension/plugin modules
- apps/console/** where feature-specific
- tests/memory/**
- tests/tools/**
- tests/selfdev/**
- extension/install/beta tests.

When API/CLI wiring is required, Session B supplies the implementation module + contract/test and a small integration note; Session A wires shared surfaces.

### Integration

Branch: cursor/v2-integration

Session A integrates reviewed lane commits. No force-push. Preserve exact source/evidence refs.

## Critical artifact path to V2.0

### Lane A critical chain

A0. ART-V12-BROKER-CONTRACT
- close current generic ProductStore direct-local-chat bypass;
- all operational model calls must use governed project-scoped broker.

A1. ART-V15-LEASE-FENCING
- durable PostgreSQL worker/lease/attempt/result state;
- atomic claim + generation/cancellation/source fencing;
- restart-safe acceptance.

A2. ART-V15-MULTIHOST-EVIDENCE machinery
- worker client/poll/heartbeat/result protocol;
- two local/host aliases first, then actual separate hosts when available.

A3. ART-V18-SITE-EPOCH / backup manifest
- authoritative site epoch;
- backup/restore CLI;
- reconcile in-flight leases after restore.

A4. ART-V20-INTEGRATED-CANDIDATE
- integrate both lanes on one code tree;
- complete CI/migrations/install journey.

### Lane B critical chain

B0. ART-V13-TASK-POOL / reviewer benchmark
- freeze held-out/calibration manifests so G13 can progress while broader product work continues.

B1. ART-V16-PROVENANCE
- explicit knowledge classes, provenance, scope, expiry, supersession/tombstones.

B2. ART-V16-PERMISSION-RETRIEVAL
- permission filter before ranking/context;
- contradiction/supersession/deletion behavior.

B3. ART-V17-APPROVAL-BINDING
- unified ActionEnvelope/ApprovalGrant/ActionReceipt contracts.

B4. ART-V17-INTEGRATION-MANIFEST
- versioned adapters using the same gateway boundary.

B5. ART-V19-EXTENSION-CONTRACT / clean install
- stable extension interfaces;
- install/upgrade/support bundle;
- self-development non-demo path.

B6. ART-V20-SUPPORT-MATRIX / operator journeys
- honest supported/unsupported matrix and end-to-end UX evidence.

## Parallelism rule

A and B should rarely touch the same files. When a dependency crosses lanes:
1. define/update the artifact contract first;
2. producer lane implements behind that contract;
3. integration owner wires shared surfaces;
4. tests prove interface compatibility.

Do not solve conflicts by making both sessions edit shared monolithic files.

## Today success definition

Best-case today:
- current source blockers fixed;
- V1.5–V1.9 implementation artifacts are reviewable or verified;
- V2.0 integrated candidate is green;
- install/upgrade/recovery/selfdev/operator journeys can be executed;
- time-dependent live/remote/reliability artifacts are clearly blocked/running, not fabricated.

Do not require the wall clock to lie in order to call the implementation target successful.

## Lead parallel artifact work

While Cursor implements, ChatGPT advances:
- V1.5 lease/fencing ADR + DB schema;
- V1.6 provenance/retrieval schema;
- V1.7 approval/action envelope + adapter contract;
- V1.8 site epoch/backup/recovery manifest;
- V1.9 extension/clean-install acceptance contract;
- V2.0 acceptance/support/reliability matrix;
- V2.3 artifact skeleton;
- V3.0 objective/learning governance artifacts.

Every lead artifact should either remove worker ambiguity or define a future acceptance boundary.
