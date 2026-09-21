# ART-V20-FOUNDATION-HARDENING — inherited-risk punch list

Status: drafting
Target: V2.0 integrated candidate
Owner: ChatGPT lead + Cursor lanes
Source audit: V1.4 base application tree

Purpose: prevent V2.0 from integrating known legacy assumptions as new platform contracts.

## H1 — memory project isolation — HIGH

Observed:
- `retrieve_context()` iterates `store.list_all()` with no required project filter.
- `performance_memory_for_routing()` likewise aggregates model observations across the store.
- `resume_mission(..., memory=...)` writes recovery memory using hard-coded `project_id="proj_local"`.

Risk:
cross-project content/routing signal leakage or misattribution.

Owner: Session B
Artifacts: ART-V16-PROVENANCE / ART-V16-PERMISSION-RETRIEVAL

Required:
- project/actor scope required before candidate retrieval;
- no ranking over unauthorized records;
- routing memory scoped at least by project;
- recovery derives project ID from durable mission/project state;
- two-project tests prove no content, count, model-preference or existence leak.

## H2 — worker durable credentials — HIGH

Observed:
WorkerRegistry stores membership token as raw string in WorkerRecord/_tokens.

Risk:
persisting current shape to DB would create reusable raw membership credentials.

Owner: Session A
Artifact: ART-V15-LEASE-FENCING / WORKER-PROTOCOL

Required:
- durable store contains token hash/identifier or secure secret reference, not raw token;
- returned-once token cannot be reconstructed from DB;
- token rotation/revocation increments or fences appropriate generation;
- tests assert raw token absent from durable row/serialized inspection.

## H3 — worker queue head-of-line blocking — MEDIUM

Observed:
`claim_dispatch` pops the first task; capability/privacy mismatch reinserts at index 0 and returns None.

Risk:
one incompatible task can block a worker from claiming compatible tasks later in the queue.

Owner: Session A
Artifact: V1.5 worker protocol / V2.3 scheduler precursor

Required:
- durable claim query chooses an eligible task without consuming/reordering unauthorized work incorrectly;
- fairness documented;
- incompatible task does not starve compatible tasks.

## H4 — tool demo-project default — HIGH

Observed:
`make_approval(... project_id="proj_demo")` has a known fixture project default.

Risk:
future operational callers that omit project may silently bind an approval to demo scope.

Owner: Session B
Artifact: ART-V17-APPROVAL-BINDING

Required:
- project_id mandatory for operational approval creation;
- fixture helper, if retained, explicit/test-only;
- ActionEnvelope/ApprovalGrant bind project + actor + operation + destination + payload/effect key.

## H5 — tool idempotency scope — MEDIUM/HIGH

Observed:
ToolGateway in-memory duplicate protection keys only on `operation_id` within one gateway instance.

Risk:
not a durable cross-process effect fence; operation ID semantics may not bind project/effect intent.

Owner: Session B contract + Session A durable integration
Artifacts: ART-V17-APPROVAL-BINDING, ART-V15-LEASE-FENCING

Required:
- durable accepted effect key scoped to project/operation/destination/payload or explicit effect key;
- uncertain external outcomes reconcile rather than blind retry;
- restart cannot duplicate accepted consequential action.

## H6 — deployment default credentials/config — HIGH

Observed:
- standalone/recovery compose embed `swarm:swarm` database credentials;
- `.env.example` defaults `SWARM_EXECUTION_MODE=mock`;
- operator docs present mock/demo commands as ordinary first-run fallback.

Risk:
violates clean-install/no-known-default/no-operational-mock V2 posture.

Owner: Session A for compose/runtime; Session B for install/operator docs
Artifacts: ART-V18-DEPLOYMENT-MANIFEST, ART-V19-INSTALL-UPGRADE, ART-V20-INSTALL-JOURNEY

Required:
- no fixed known DB password in normal deployment artifact;
- generated/operator-supplied secret reference;
- operational empty/unconfigured is default;
- mock mode only explicit dev/test;
- clean install refuses unsafe/missing required secret rather than silently mock-running.

## H7 — container API bind verification — MEDIUM

Observed:
compose publishes host loopback 8765:8765 and declares `SWARM_BIND_HOST=127.0.0.1`; current CLI serve default is 127.0.0.1 and the inspected compose does not show the service command.

Risk:
depending on image entrypoint, API may bind container loopback and be unreachable through Docker port publishing, or env may be ignored.

Owner: Session A
Artifact: ART-V18-DEPLOYMENT-MANIFEST

Required:
- explicit container command/entrypoint behavior;
- API binds container interface needed for Docker networking while host publish stays loopback/private;
- real compose smoke proves host loopback health works and non-loopback exposure is absent.

## H8 — recovery verifier is declarative — HIGH

Observed:
`recovery_verify()` marks side-effect freeze, old-primary fence, restore and duplicate prevention true from documented intent; sample manifest contains placeholder hashes.

Risk:
false recovery evidence.

Owner: Session A
Artifacts: ART-V18-BACKUP-RESTORE / SPLIT-BRAIN-SAFETY / OUTAGE-DRILL

Required:
- create real backup/digests;
- restore into empty DB/artifact target;
- validate integrity;
- reconcile in-flight leases/reservations;
- prove stale epoch rejected;
- report actual RPO/RTO;
- never count sample manifest/booleans as live drill proof.

## H9 — self-development demo coupling — HIGH for V1.9

Observed:
mock runner contains supplied `GOOD_FIX`; live dogfood targets `sandbox/selfdev_issue/parser_helper.py` and may deliberately write a failing fixture before mission execution.

Risk:
cannot satisfy independent non-demo self-development artifact.

Owner: Session B
Artifacts: ART-V19-BETA-ACCEPTANCE / ART-V19-SELFDEV-PR-EVIDENCE

Required:
- retain fixture runner only for isolated regression tests;
- V1.9 path takes a preselected real issue/repository without supplied solution;
- worker does not receive hidden patch;
- isolated change + independent tests/reviewer + PR/diff candidate;
- no self-merge/release/permission changes.

## H10 — documentation/version truth — MEDIUM

Observed:
README/operator docs still describe mock demos and older V0.9/V1 RC posture.

Risk:
clean-install users/operators get stale product semantics.

Owner: Session B
Artifacts: ART-V19-INSTALL-UPGRADE / ART-V20-SUPPORT-MATRIX

Required:
- update only once integrated behavior exists;
- accurately label supported/experimental/blocked;
- no demo instruction as production recovery path.

## Exit

ART-V20-FOUNDATION-HARDENING becomes reviewable when each item is either:
- fixed with exact source/tests/evidence; or
- explicitly out of V2 supported scope with a fail-closed behavior and support-matrix entry.

No item may disappear simply because a new implementation bypasses the old module; dead operational paths should be removed or explicitly fixture-gated.
