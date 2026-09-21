# SwarmAI V1.7 -> V2.3 cemented execution plan

Status: FUTURE PLAN — DO NOT START UNTIL V1.7 RECOVERY SCOPE IS COMPLETE/AUTHORIZED
Date: 2026-09-21

## Purpose

Make the path after V1.7 implementation predictable, artifact-oriented, and small-packet.

This plan supersedes broad future prose where it conflicts on packet granularity, but does not override ARTIFACT_REGISTRY acceptance state.

## Cemented architecture decisions

1. PostgreSQL/SQLAlchemy/Alembic remain authoritative durable state.
2. Existing controller scheduler evolves into V2.3 scheduler. No second scheduler.
3. Existing ToolGateway/action boundary remains the only consequential tool/effect path.
4. Existing worker/result fencing is extended, not replaced.
5. DBOS is bounded workflow durability only, never authority.
6. Extension/capability packs cannot bypass broker/ToolGateway/project policy.
7. Observability is read-only by default; mutations re-enter V1.7 action boundary.
8. OpenTelemetry, if adopted, is optional export, never audit authority.
9. Portability exports references/digests and current authorized content; never secret values.
10. V2.1/V2.2 are optional internal implementation checkpoints only unless canonical registry defines artifacts.

## Deliberately NOT frozen yet

- concrete cross-site SiteEpoch fencing authority mechanism;
- backup storage provider;
- final supported OS matrix;
- public capability signature/trust mechanism;
- V2.3 normalized service-cost weights;
- final counted fairness tolerance.

These must be frozen before their counted evidence, not guessed now.

# Milestone M18 — V1.8 recovery/site authority

## 18-00 V1.7 candidate handoff
Input: exact V1.7 CP6 source/evidence.
Output: V1.8 base manifest.
No code.

## 18-01 SiteAuthority contracts
Artifact: ART-V18-SITE-EPOCH
Small scope:
- SiteAuthority/SiteEpoch contract;
- AuthorityBinding;
- transition receipt;
- failure enums.
No wiring.

## 18-02 SiteAuthority persistence
Depends: 18-01
- DB rows/repository;
- Alembic migration;
- active/recovery/stale transitions;
- monotonic local versioning.
No dispatch/effect wiring yet.

## 18-03 dispatch epoch fence
Depends: 18-02
- scheduler/dispatch loads current authority;
- new dispatch carries binding;
- stale/absent authority fails closed;
- focused tests only.

## 18-04 result/effect epoch fence
Depends: 18-02
- result acceptance validates authority binding;
- consequential effect reserve/execute/accept validates binding;
- stale result/effect negatives.

## 18-05 deployment + backup manifest
Artifacts: ART-V18-DEPLOYMENT-MANIFEST, ART-V18-BACKUP-RESTORE
- redacted deployment manifest;
- BackupManifest;
- DB/artifact/config digests;
- secret refs only.

## 18-06 backup command
Depends: 18-05
- create;
- verify;
- corruption detection;
- high-water marks.

## 18-07 restore/reconcile
Depends: 18-04,18-06
- recovery-mode startup;
- restore validation;
- migration/integrity;
- in-flight lease/reservation reconciliation;
- unknown effects preserved;
- new authority acquisition interface.

## 18-08 split-brain negatives
Artifact: ART-V18-SPLIT-BRAIN-SAFETY
- stale site dispatch denied;
- stale result denied;
- stale effect denied;
- duplicate authority activation denied.

## 18-09 live recovery checkpoint
Artifact: ART-V18-OUTAGE-DRILL
Run CP18:
backup -> outage -> restore -> new authority -> old authority negative -> RPO/RTO.
If concrete cross-site authority mechanism is unavailable, local drill can be reviewable but formal split-site acceptance stays blocked.

# Milestone M19 — V1.9 install/extensions/selfdev

## 19-01 ExtensionManifest contracts
Artifact: ART-V19-EXTENSION-CONTRACT
- manifest;
- compatibility;
- capabilities/scopes;
- risk/trust refs.

## 19-02 project extension grants
Depends: 19-01
- durable install/grant state;
- effective permission intersection;
- install/enable/drain/disable/uninstall state machine.

## 19-03 ToolGateway extension bridge
Depends: 19-02
- extension operations execute only via normal adapters/gateway;
- no provider/tool direct bypass;
- cross-project negative.

## 19-04 clean install
Artifact: ART-V19-INSTALL-UPGRADE
- install doctor;
- empty DB;
- migrations;
- no seeded product state;
- deterministic first supported mission.

## 19-05 upgrade
Depends: 19-04
- preflight;
- backup requirement;
- migration;
- version compatibility;
- failure handling.

## 19-06 rollback + support bundle
Depends: 19-05
- supported rollback semantics;
- redacted diagnostics;
- secret scan.

## 19-07 controlled selfdev source path
Artifact: ART-V19-SELFDEV-PR-EVIDENCE
- bounded issue;
- isolated branch/worktree;
- test/eval;
- independent review hook;
- no self-merge/release.

## 19-08 live productization checkpoint
CP19:
- fresh install;
- extension project A allow / project B deny;
- drain/disable;
- upgrade/rollback;
- one real selfdev PR candidate.
Actual Windows/fresh external environment evidence remains separate if not available.

# Milestone M20 — V2.0 integrated candidate

## 20-01 integrate reviewed slices
Artifacts: ART-V20-FOUNDATION-HARDENING, ART-V20-INTEGRATED-CANDIDATE
- one migration head;
- no unreviewed donor merges;
- resolve compatibility.

## 20-02 CandidateManifest freeze
Depends: 20-01
Freeze:
source SHA, schema/migration heads, dependency lock, deployment manifest, policies, providers/tools/extensions used for evidence, test/eval protocol versions.

## 20-03 exact-tip deterministic matrix
Depends: 20-02
- full configured Ruff/mypy/offline/integration where environment supports;
- migrations clean + supported upgrade;
- no hidden skip reclassified as pass.

## 20-04 support matrix + install journey
Artifacts: ART-V20-SUPPORT-MATRIX, ART-V20-INSTALL-JOURNEY
Populate from evidence only.

## 20-05 upgrade/rollback journey
Artifact: ART-V20-UPGRADE-ROLLBACK
Execute against exact CandidateManifest.

## 20-06 security review
Artifact: ART-V20-SECURITY-REVIEW
Map threat cases to exact source/tests/live negatives.

## 20-07 performance baseline
Artifact: ART-V20-PERFORMANCE-BASELINE
Include total orchestration/retry/review overhead, not just model latency.

## 20-08 freeze/start reliability
Artifact: ART-V20-RELIABILITY-PROTOCOL
Freeze protocol before start.
Start wall-clock campaign immediately.
Implementation may continue to V2.3 prep only if owner authorizes while campaign runs.

## 20-09 release review
Artifact: ART-V20-RELEASE-REVIEW
After required elapsed evidence:
independent candidate-bound review.
No public release implied.

# Milestone M23 — V2.3 operational platform

## 23-01 scheduler durable state
Artifact: ART-V23-MULTIMISSION-OPS
- SchedulerPolicy;
- ProjectQueueState;
- MissionQueueState refs;
- decision receipt schema;
- DB migration.

## 23-02 weighted deficit project selector
Depends: 23-01
- project-level fair share;
- bounded priority/aging;
- deterministic tie-break;
- no permission/resource bypass.

## 23-03 mission/task selector
Depends: 23-02
- dependency/generation/revision/cancel eligibility;
- locality/capability availability;
- anti-head-of-line blocking.

## 23-04 DispatchIntent
Depends: 23-03
- preparing/ready/dispatched/compensating/released/completed;
- worker/provider/tool/effect reservation components;
- idempotent compensation;
- no execution before ready.

## 23-05 crash/unknown reconciliation
Depends: 23-04
- preparing crash;
- partial reservation;
- unknown provider/effect;
- expiry/recovery.

## 23-06 backpressure/cancel/drain
Depends: 23-03
- per-project/global queue bounds;
- fanout bounds;
- cancel generation;
- project pause/drain;
- worker/site drain.

## 23-07 scheduler epoch/restart
Depends: 23-01,23-04
- single dispatch authority;
- restart reconciles reservations;
- preserves bounded fairness credit;
- stale scheduler denied.

## 23-08 decision receipts/observability read model
Artifacts: ART-V23-OBSERVABILITY
- every dispatched/deferred/blocked decision explainable;
- no private raw task/prompt content.

## 23-09 capability packs
Artifact: ART-V23-CAPABILITY-PACKS
Build on V1.9 extensions:
- pack manifest;
- version/digest/provenance;
- install/enable/drain/disable;
- no implicit permission/model qualification change.

## 23-10 portability
Artifact: ART-V23-PORTABILITY
- bundle manifest;
- export current authorized knowledge/config/pack/policy refs;
- no secrets;
- import/reconcile.

## 23-11 fleet policy
Artifact: ART-V23-FLEET-POLICY
- trust classes;
- capability/locality/privacy/provider/tool reachability;
- capacity;
- drain/migration;
- stale worker/site fencing.

## 23-12 deterministic pathological workload
Freeze benchmark protocol first.
Cases:
- equal/weighted fairness;
- spawn gaming;
- priority starvation;
- incompatible queue head;
- partial reservation;
- crash during prepare;
- unknown outcome;
- dual scheduler epoch;
- cancellation/drain.

## 23-13 live operational checkpoint
CP23:
- >=2 projects;
- multiple missions;
- heterogeneous worker capabilities;
- constrained resource pool;
- scheduler restart;
- capability pack enable/deny/drain;
- portability export/import;
- fleet placement;
- decision receipts.

## 23-14 V2.3 integrated audit
Artifact-by-artifact independent review.
Formal acceptance only from canonical registry.

# Checkpoint philosophy

Every milestone has:
- source artifact packets;
- deterministic negative packets;
- one live checkpoint packet;
- independent review.

Do not call a milestone complete merely because code exists.
