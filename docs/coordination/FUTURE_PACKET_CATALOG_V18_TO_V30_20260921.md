# SwarmAI future worker packet catalog — V1.8 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY

These are bounded future packet definitions. They are not queued to the current V1.7 Cursor session.

Every packet begins with:
- reread ARTIFACT_REGISTRY;
- inspect current source and migrations;
- confirm dependency artifacts;
- preserve zero-spend/no-main-merge/no-public-deploy boundaries;
- do not self-accept.

## V18-01 — SiteEpoch authority core

Target:
ART-V18-SITE-EPOCH

Inputs:
- V1.5 durable lease/result semantics;
- V1.7 effect receipt semantics;
- ART-V18 recovery architecture.

Work:
- durable SiteAuthority/SiteEpoch model/repository;
- current-authority lookup;
- monotonic epoch transition;
- bind dispatch/result/effect authority;
- migration;
- fail-closed stale epoch errors.

Likely paths:
- db models/repositories/migration;
- controller scheduler;
- workers result acceptance;
- tools gateway/action boundary;
- new recovery/authority module.

Tests:
- stale dispatch;
- stale result;
- stale consequential effect;
- duplicate recovery activation;
- restart retains active epoch.

Exit:
reviewable source + migrations + deterministic/integration tests.

## V18-02 — Backup/restore/reconciliation

Targets:
ART-V18-DEPLOYMENT-MANIFEST
ART-V18-BACKUP-RESTORE

Work:
- redacted deployment manifest;
- backup manifest + integrity digests;
- DB/config state-class declaration;
- restore command/workflow;
- increment/fence authority epoch;
- reconcile in-flight leases;
- carry unknown effects forward without blind retry;
- operator summary.

Tests:
- corrupted backup;
- schema mismatch;
- partial restore;
- in-flight lease reconciliation;
- unknown effect preservation;
- secret exclusion.

## V18-03 — Split-brain and outage drill

Targets:
ART-V18-SPLIT-BRAIN-SAFETY
ART-V18-OUTAGE-DRILL

Work:
- automated local/integration drill harness;
- then real private drill when environment permits;
- RPO/RTO capture;
- old-site negative validation.

Exit:
harness complete even if live evidence is waiting.

---

## V19-01 — Extension contract/runtime

Target:
ART-V19-EXTENSION-CONTRACT

Work:
- ExtensionManifest;
- ProjectExtensionGrant;
- registry/lifecycle;
- project-scoped enable/drain/disable/uninstall;
- integrate adapter entrypoints through ToolGateway;
- compatibility/version/digest checks;
- no direct provider/tool bypass.

Tests:
- over-scoped grant;
- cross-project use;
- disabled/draining work;
- bad digest/version;
- broker/gateway bypass attempt.

## V19-02 — Install/upgrade/rollback

Target:
ART-V19-INSTALL-UPGRADE

Work:
- clean install path;
- environment doctor;
- migration preflight;
- upgrade plan;
- backup-before-upgrade;
- rollback;
- support bundle;
- deterministic nonsecret config manifest.

Tests:
- clean empty DB;
- previous supported schema;
- failed migration;
- rollback;
- missing dependency;
- secret redaction.

## V19-03 — External install evidence

Target:
ART-V19-EXTERNAL-INSTALLS

Work:
- frozen install instructions;
- execute on fresh supported environment(s);
- record exact OS/runtime/dependency versions;
- no pre-existing Swarm state.

Do not simulate "external."

## V19-04 — Real controlled selfdev

Target:
ART-V19-SELFDEV-PR-EVIDENCE

Work:
- choose bounded real repo issue;
- preregister task and tests;
- isolated branch/worktree;
- Swarm-assisted implementation;
- deterministic checks;
- independent review;
- produce PR candidate;
- forbid self-merge/release;
- retain failures.

---

## V20-01 — Integrated candidate freeze

Targets:
ART-V20-FOUNDATION-HARDENING
ART-V20-INTEGRATED-CANDIDATE

Work:
- integrate only reviewed source;
- resolve migration ordering;
- run complete configured test/lint/typecheck suite;
- create CandidateManifest;
- freeze exact source/config/schema/dependency/policy versions.

Exit:
one reproducible candidate identity.

## V20-02 — Support/install/rollback evidence

Targets:
ART-V20-SUPPORT-MATRIX
ART-V20-INSTALL-JOURNEY
ART-V20-UPGRADE-ROLLBACK

Work:
- populate support matrix from evidence only;
- execute clean install;
- execute upgrade;
- execute rollback;
- record unsupported/blocked honestly.

## V20-03 — Security/performance

Targets:
ART-V20-SECURITY-REVIEW
ART-V20-PERFORMANCE-BASELINE

Work:
- map threat model to exact candidate;
- run deterministic security negatives;
- benchmark agreed workloads;
- include orchestration/retry/review overhead;
- record CPU/RAM/DB/provider/resource use.

## V20-04 — Reliability campaign/release review

Targets:
ART-V20-RELIABILITY-PROTOCOL
ART-V20-RELEASE-REVIEW

Work:
- freeze protocol BEFORE campaign;
- run required real elapsed window;
- preserve outages/failures;
- invalidate/restart correctly if frozen protocol requires;
- independent release review.

No time compression/backfill.

---

## V23-01 — Durable multi-mission scheduler

Target:
ART-V23-MULTIMISSION-OPS

Work:
- persistent project scheduling state;
- fair-service algorithm;
- priority aging;
- deterministic tie-break;
- resource reservation intents;
- backpressure;
- cancellation/drain;
- epoch binding;
- decision receipts.

Important:
evolve existing AdaptiveScheduler; do not create second execution scheduler.

## V23-02 — Capability packs

Target:
ART-V23-CAPABILITY-PACKS

Work:
- versioned pack manifest;
- digest/provenance/trust;
- project enablement;
- lifecycle;
- tests/migrations;
- adapter/procedure/template references;
- explicit permissions.

Pack enablement must not change route qualification or permissions implicitly.

## V23-03 — Portability

Target:
ART-V23-PORTABILITY

Work:
- bundle manifest;
- export;
- secret stripping;
- import/reconciliation;
- version/migration handling;
- knowledge/provenance/pack/policy references.

## V23-04 — Observability

Target:
ART-V23-OBSERVABILITY

Work:
- normalized operational event model;
- scheduler/worker/provider/tool/recovery events;
- query/read surfaces;
- read-only dashboard semantics;
- any mutation routes through V1.7 action boundary.

## V23-05 — Fleet policy

Target:
ART-V23-FLEET-POLICY

Work:
- trust classes;
- locality/privacy placement;
- capability/provider/tool reachability;
- capacity;
- drain/migration;
- stale worker/site fencing;
- fleet decision receipts.

## V23-06 — V2.3 integrated evidence

Work:
- freeze scheduler/workload/tolerance protocol;
- run deterministic/pathological suite;
- run multi-process/private evidence;
- independent review.

---

## V30-01 — Persistent objectives

Target:
ART-V30-OBJECTIVE-CONTRACT

Work:
- objective/version repository;
- schedule/event/manual triggers;
- trigger receipts/dedupe;
- pause/revoke/expiry;
- stop conditions;
- MissionProposal;
- normal mission-admission bridge;
- authority intersection;
- rate/max-active.

Tests:
all canonical objective threat/negative cases.

## V30-02 — Governed learning

Target:
ART-V30-LEARNING-GOVERNANCE

Work:
- LearningProposal repository/state machine;
- observation/provenance capture;
- calibration;
- freeze;
- sealed held-out path;
- independent review;
- canary;
- rollback;
- drift/expiry/revalidation;
- immutable transition receipts.

## V30-03 — Resource allocator

Target:
ART-V30-RESOURCE-ALLOCATOR

Work:
- objective resource request policy;
- allocator generates inputs/reservations for V2.3 scheduler;
- preserve fairness/quota/privacy/cost;
- decision receipts.

Do not bypass scheduler.

## V30-04 — Controlled self-development

Target:
ART-V30-CONTROLLED-SELFDEV

Work:
- selfdev as governed LearningProposal subtype;
- isolated branch/worktree;
- code diff;
- tests/evals;
- independent reviewer;
- canary/rollback where applicable;
- no self-governance edit;
- no self-merge/release.

## V30-05 — Capability ecosystem

Target:
ART-V30-CAPABILITY-ECOSYSTEM

Work:
- trust/signature/provenance;
- registry/discovery;
- compatibility;
- permissions;
- revocation;
- migration;
- malicious/overscoped negative tests.

Build on V2.3 packs/V1.9 extensions.

## V30-06 — Fleet tenancy/audit

Target:
ART-V30-FLEET-TENANCY-AUDIT

Work:
- tenant-aware fleet placement;
- cross-project metadata/content/effect isolation;
- audit receipt linkage;
- exportable audit view without secrets;
- stale epoch/worker negatives.

## V30-07 — final integrated V3 campaign

Work:
- freeze candidate/policies/eval protocols;
- real objective schedule/event evidence;
- learning governance scenarios;
- canary rollback;
- multi-project resource/fleet evidence;
- controlled selfdev evidence;
- independent security/governance review.

Release remains operator-gated.
