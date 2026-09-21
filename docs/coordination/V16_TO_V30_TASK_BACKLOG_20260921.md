# SwarmAI future task backlog — V1.6 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY
No task here overrides the active V1.7 single-session execution scope or artifact registry.

Notation:
- D = design/contract
- I = implementation
- T = deterministic tests
- L = live/private evidence
- R = independent review

## V1.6

- V16-01 D — freeze KnowledgeItem/KnowledgeLink/Tombstone schema.
- V16-02 I — persistent versioned knowledge repository.
- V16-03 T — schema/version/migration tests.
- V16-04 I — project/tenant permission prefilter.
- V16-05 I — retrieval/ranking over authorized candidate set only.
- V16-06 I — bounded context assembler + retrieval receipt/token cost.
- V16-07 I — contradiction/supersession state machine.
- V16-08 I — deletion/tombstone + index/cache/summary/export invalidation.
- V16-09 I — conservative legacy MemoryStore adapter.
- V16-10 T — cross-project existence/content leak negatives.
- V16-11 T — stale/deleted/superseded retrieval negatives.
- V16-12 L — later-mission knowledge reuse.
- V16-13 L — fixed-set context savings/quality benchmark.
- V16-14 R — V1.6 evidence review.

Dependencies: V16-02 -> 04/07/08/09; 04 -> 05 -> 06; implementation -> tests -> live evidence -> review.

## V1.7

- V17-01 D — freeze ActionEnvelope/ApprovalGrant/ActionReceipt.
- V17-02 I — durable effect/approval persistence and migrations.
- V17-03 I — ToolGateway normalization/authorization/policy path.
- V17-04 I — exact approval binding validation.
- V17-05 I — effect reservation/idempotency/reconciliation.
- V17-06 I — adapter interface/version manifest.
- V17-07 I — local/sandbox adapter.
- V17-08 I — API/MCP-style adapter.
- V17-09 I — browser/session-aware adapter.
- V17-10 I — safe session recovery/destination restoration.
- V17-11 T — payload/destination mutation negatives.
- V17-12 T — expiry/revocation/cancellation/stale-generation negatives.
- V17-13 T — duplicate/unknown-outcome reconciliation.
- V17-14 L — three integration-class evidence.
- V17-15 R — V1.7 evidence review.

Dependencies: 01 -> 02/03/04; 03-05 -> adapters; adapters -> live evidence.

## V1.8

- V18-01 D — freeze authority/site epoch contract.
- V18-02 I — epoch persistence.
- V18-03 I — bind scheduler/dispatch to epoch.
- V18-04 I — bind worker result acceptance to epoch.
- V18-05 I — bind consequential effect acceptance to epoch.
- V18-06 D/I — deployment manifest generator.
- V18-07 D/I — backup format + consistency boundary.
- V18-08 I — restore/reconciliation workflow.
- V18-09 T — stale-site/split-brain negatives.
- V18-10 T — partial/corrupt restore negatives.
- V18-11 L — outage/restore drill.
- V18-12 L — stale old site cannot accept new work/effects.
- V18-13 R — recovery review.

Dependencies: V1.5 durable state and V1.7 effect boundary.

## V1.9

- V19-01 D — extension manifest/trust/permission contract.
- V19-02 I — extension registry/lifecycle.
- V19-03 I — project-scoped enable/drain/disable.
- V19-04 T — extension cannot widen permissions/provider eligibility.
- V19-05 D/I — install/upgrade/rollback machinery.
- V19-06 L — clean Linux/macOS install as supported.
- V19-07 L — actual Windows clean install when available.
- V19-08 L — external/fresh-environment install.
- V19-09 I — controlled self-development workflow.
- V19-10 L — one real self-development issue through isolated branch/tests/review.
- V19-11 R — beta acceptance review.

Dependencies: V1.7 unified action boundary before extension/selfdev.

## V2.0

- V20-01 I — finish foundation hardening list.
- V20-02 I — integrate only reviewed lower-version slices.
- V20-03 D — exact candidate freeze receipt.
- V20-04 I — evidence-grounded support matrix.
- V20-05 L — clean install journey.
- V20-06 L — upgrade/migrate/rollback journey.
- V20-07 R/T — security threat model mapped to candidate.
- V20-08 L/T — performance/resource baseline.
- V20-09 D/R — freeze reliability protocol.
- V20-10 L — real reliability campaign for required wall-clock duration.
- V20-11 R — independent release review.

No backfilled elapsed time.

## V2.1 optional internal increment

- V21-01 operator/admin UX for queue/workers/providers/effects.
- V21-02 support bundle + redacted diagnostics.
- V21-03 install/update UX polish.
- V21-04 observability event normalization.

Not a canonical acceptance version unless registry is amended.

## V2.2 optional internal increment

- V22-01 scheduler state schema precursor.
- V22-02 atomic reservation-intent substrate.
- V22-03 capability-pack package/manifest substrate.
- V22-04 portability schema stabilization.

Not a canonical acceptance version unless registry is amended.

## V2.3

### Multi-mission scheduler
- V23-S01 D — project/mission/task scheduling state.
- V23-S02 D — fairness/weight/aging policy.
- V23-S03 I — deterministic scheduler.
- V23-S04 I — atomic resource reservation intent/compensation.
- V23-S05 I — backpressure.
- V23-S06 I — cancel/drain.
- V23-S07 I — scheduler authority-epoch fencing.
- V23-S08 I — SchedulerDecisionReceipt/explainability.
- V23-S09 T — starvation/head-of-line/incompatible-worker negatives.
- V23-S10 L — multi-process scheduling evidence.

### Capability packs
- V23-C01 D — pack manifest/version/trust contract.
- V23-C02 I — install/enable/drain/disable lifecycle.
- V23-C03 T — unauthorized project use denied.
- V23-C04 T — pack cannot change model qualification/permissions implicitly.

### Portability
- V23-P01 D — export/import bundle contract.
- V23-P02 I — bundle exporter.
- V23-P03 I — importer/reconciliation.
- V23-P04 T — secret values excluded.
- V23-P05 L — export -> clean environment -> import -> run.

### Observability
- V23-O01 D — operational event model.
- V23-O02 I — read-only dashboard/API.
- V23-O03 I — authenticated mutation route via V1.7 action boundary.
- V23-O04 T — dashboard cannot bypass approval/policy.

### Fleet
- V23-F01 D — trust/locality/capability placement contract.
- V23-F02 I — placement evaluator.
- V23-F03 I — drain/migration.
- V23-F04 T — stale worker/site/cancel negatives.
- V23-F05 L — heterogeneous multi-host fleet evidence.

### Review
- V23-R01 freeze workloads/tolerances before counted evidence.
- V23-R02 independent V2.3 review.

## V3.0

### Persistent objectives
- V30-O01 D — objective schema/lifecycle.
- V30-O02 I — schedule/event trigger receipts.
- V30-O03 I — bounded MissionProposal generation.
- V30-O04 I — duplicate-trigger prevention/idempotency.
- V30-O05 I — pause/stop/expiry.
- V30-O06 T — objective cannot widen authority.
- V30-O07 L — real wall-clock schedule/event evidence.

### Governed learning
- V30-L01 D — LearningProposal schema/state machine.
- V30-L02 I — operational observation/provenance capture.
- V30-L03 I — candidate change isolation/versioning.
- V30-L04 I — calibration pipeline.
- V30-L05 I — sealed held-out evaluation path.
- V30-L06 I — deterministic/security/policy gates.
- V30-L07 I — canary rollout.
- V30-L08 I — rollback + stale worker/scheduler fencing.
- V30-L09 I — drift/expiry/revalidation.
- V30-L10 T — proposer cannot see held-out answers.
- V30-L11 T — learning cannot change its own governance in same proposal.
- V30-L12 L — competing proposals + frozen selection rule + retained loser evidence.
- V30-L13 L — accepted procedure later expires on dependency drift and revalidates.

### Resource allocator
- V30-R01 D — cross-objective resource policy.
- V30-R02 I — allocator atop V2.3 scheduler.
- V30-R03 T — fairness/quota/privacy/cost invariants.
- V30-R04 T — no hidden starvation/cost shifting.

### Controlled self-development
- V30-SD01 D — selfdev proposal contract.
- V30-SD02 I — isolated repo/worktree path.
- V30-SD03 I — independent test/eval/reviewer path.
- V30-SD04 I — canary/rollback.
- V30-SD05 T — cannot self-edit governance/evidence/reviewer in same proposal.
- V30-SD06 L — real bounded improvement proposal with independent acceptance or rejection.

### Capability ecosystem
- V30-C01 D — signed/versioned capability trust policy.
- V30-C02 I — registry/install/enable/revoke.
- V30-C03 T — malicious/over-scoped capability negative suite.

### Fleet tenancy/audit
- V30-F01 D — tenant/project audit schema.
- V30-F02 I — tenant-aware fleet placement.
- V30-F03 I — exportable audit receipts.
- V30-F04 T — cross-tenant leakage/effect negatives.
- V30-F05 L — multi-tenant private-live evidence.

### Final V3 review
- V30-X01 freeze exact candidate/config/policies.
- V30-X02 run deterministic + private-live acceptance.
- V30-X03 verify real wall-clock evidence where required.
- V30-X04 independent security/governance review.
- V30-X05 final release recommendation artifact; operator still decides release.
