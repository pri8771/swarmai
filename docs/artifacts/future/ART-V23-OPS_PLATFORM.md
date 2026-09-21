# ART-V23-OPS-PLATFORM — V2.3 operational platform architecture

Status: drafting
Target milestone: V2.3
Owner: ChatGPT lead

## Purpose

Bridge the V2.0 single-mission product to V3 persistent objectives without prematurely giving the system self-directed authority.

V2.3 should make many concurrent user-authorized missions manageable, observable, portable and extensible.

## Artifact families

### ART-V23-MULTIMISSION-OPS

Control plane supports multiple active missions with:
- project priority;
- deadlines;
- bounded concurrency;
- shared provider/worker/tool budgets;
- fair reservation scheduling;
- explicit cancellation/drain;
- per-mission isolation.

No mission may starve all others by recursively spawning agents.

### ART-V23-CAPABILITY-PACKS

Versioned capability packs bundle:
- task handlers;
- tool adapters;
- evaluator/scorer;
- prompts/procedures;
- permissions;
- compatibility constraints;
- tests;
- signature/digest.

Installing a pack does not automatically grant its requested permissions or mark its models/routes qualified.

### ART-V23-PORTABILITY

Export/import:
- project config without secrets;
- artifact manifests;
- accepted knowledge/provenance;
- mission history;
- capability manifests;
- compatibility versions.

Import cannot silently restore expired approvals, credentials, active leases or stale site authority.

### ART-V23-OBSERVABILITY

One operational view for:
- missions/tasks;
- workers;
- providers/reservations;
- tool effects;
- artifact graph;
- knowledge retrieval;
- costs/unknown costs;
- errors/retries;
- acceptance state.

Trace IDs connect user action -> mission -> task -> inference/tool attempts -> artifacts -> acceptance.

### ART-V23-FLEET-POLICY

Define:
- worker trust classes;
- site/node labels;
- project affinity;
- data locality;
- capability policy;
- maintenance/drain;
- resource priority.

This is policy, not yet V3 cross-project autonomous allocation.

## Milestone exit

V2.3 should demonstrate:
- multiple concurrent missions with fair shared limits;
- one mission cannot bypass another's reservations;
- install/disable a capability pack safely;
- export/import a project without secrets or live authority;
- operator can trace one accepted result end-to-end;
- workers/sites can drain without corrupting active missions.

## Decomposition direction

Keep implementation packets SP1-SP3:
- scheduler/fairness policy;
- trace schema;
- pack manifest/validator;
- export bundle schema;
- admin/observability API;
- console views;
- negative isolation tests.

Do not implement persistent objectives here; that is V3.
