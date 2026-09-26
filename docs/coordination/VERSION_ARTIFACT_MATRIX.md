# Version / artifact matrix

Artifact registry is canonical. This file is the compact human view.

## Major milestones

### V1.7 — core platform milestone
Includes the accepted/reviewable artifact sets for:
- V1.4 elastic swarm foundation;
- V1.5 distributed workers;
- V1.6 scoped reusable knowledge;
- V1.7 unified tools/browser permissions/session recovery.

### V2.0 — immediate implementation target
Adds:
- V1.8 recovery/backup/site authority;
- V1.9 extensions/beta/controlled self-development;
- integrated V2.0 candidate/install/support/reliability/review artifacts.

Implementation-complete and accepted are distinct. Time-bound acceptance may finish later.

### V2.3 — next major milestone
Planned artifact families:
- ART-V23-MULTIMISSION-OPS
- ART-V23-CAPABILITY-PACKS
- ART-V23-PORTABILITY
- ART-V23-OBSERVABILITY
- ART-V23-FLEET-POLICY

### V3.0 — persistent learning operations
Planned artifact families:
- ART-V30-OBJECTIVE-CONTRACT
- ART-V30-LEARNING-GOVERNANCE
- ART-V30-RESOURCE-ALLOCATOR
- ART-V30-CONTROLLED-SELFDEV
- ART-V30-CAPABILITY-ECOSYSTEM
- ART-V30-FLEET-TENANCY-AUDIT

## Current through V1.4

### V1.0 repair
Required:
- ART-V10-CANDIDATE
- ART-V10-SECURITY
- ART-V10-EVIDENCE-CONTRACT
- ART-V10-RUNTIME-TRUTH
- ART-V10-WORKER-HEARTBEAT

### V1.1 generic mission
Required:
- ART-V11-MISSION-PATH
- ART-V11-MULTISURFACE-EVIDENCE
- ART-V11-CONTROL-EVIDENCE
- ART-V11-RESTART-EVIDENCE
- ART-V11-APPLY-BOUNDARY

### V1.2 inference
Required:
- ART-V12-BROKER-CONTRACT
- ART-V12-PROVIDER-ELIGIBILITY
- ART-V12-REMOTE-OVERLAP
- ART-V12-LOCAL-FALLBACK
- ART-V12-ADMISSION-RECONCILIATION

### V1.3 qualification
Required:
- ART-V13-QUAL-PROTOCOL
- ART-V13-TASK-POOL
- ART-V13-SCREENING-MATRIX
- ART-V13-QUALIFIED-MATRIX
- ART-V13-OVERHEAD-REPORT
- ART-V13-REVIEWER-QUALIFICATION

### V1.4 elastic swarm
Required:
- ART-V14-GRAPH-CONTRACT
- ART-V14-ROLE-MANIFEST
- ART-V14-LIVE-ADAPTIVE-PROOF
- ART-V14-LOAD-10-50-100
- ART-V14-MODE-COMPARISON
- ART-LIVE142-PROTOCOL
- ART-LIVE142-CAMPAIGN
- ART-LIVE142-FINAL-REPORT

## V1.5 capability group — distributed workers
- ART-V15-ARCH
- ART-V15-WORKER-PROTOCOL
- ART-V15-LEASE-FENCING
- ART-V15-MULTIHOST-EVIDENCE
- ART-V15-RECOVERY-EVIDENCE

## V1.6 capability group — scoped knowledge
- ART-V16-KNOWLEDGE-CONTRACT
- ART-V16-PROVENANCE
- ART-V16-PERMISSION-RETRIEVAL
- ART-V16-SUPERSESSION
- ART-V16-CONTEXT-BUDGET-EVIDENCE

## V1.7 capability group — tools/browser
- ART-V17-TOOL-CONTRACT
- ART-V17-APPROVAL-BINDING
- ART-V17-INTEGRATION-MANIFEST
- ART-V17-SESSION-RECOVERY
- ART-V17-PERMISSION-NEGATIVES

## V1.8 capability group — recovery
- ART-V18-RECOVERY-ARCH
- ART-V18-SITE-EPOCH
- ART-V18-DEPLOYMENT-MANIFEST
- ART-V18-BACKUP-RESTORE
- ART-V18-SPLIT-BRAIN-SAFETY
- ART-V18-OUTAGE-DRILL

## V1.9 capability group — beta/extensions/self-development
- ART-V19-BETA-ACCEPTANCE
- ART-V19-EXTENSION-CONTRACT
- ART-V19-INSTALL-UPGRADE
- ART-V19-EXTERNAL-INSTALLS
- ART-V19-SELFDEV-PR-EVIDENCE

## V2.0 integrated product candidate
- ART-V20-INTEGRATED-CANDIDATE
- ART-V20-SUPPORT-MATRIX
- ART-V20-INSTALL-JOURNEY
- ART-V20-UPGRADE-ROLLBACK
- ART-V20-RELIABILITY-PROTOCOL
- ART-V20-SECURITY-REVIEW
- ART-V20-PERFORMANCE-BASELINE
- ART-V20-RELEASE-REVIEW

## Lane ownership

Session A / runtime:
- V1.2 broker closure
- V1.5 distributed workers
- V1.8 recovery
- shared integration and V2.0 candidate

Session B / product:
- V1.3 task/reviewer artifacts
- V1.6 knowledge
- V1.7 tools/browser
- V1.9 beta/extensions
- product-side V2.0 install/support journeys

ChatGPT:
- architecture/ADR/acceptance/security/research artifacts across all versions
- artifact verification and dependency graph
- V2.3/V3.0 design work ahead of implementation


## V2.3 execution plan (2026-09-26)

The V2.3 rows above are executed by `docs/plans/v2.3/PLAN.md` (26 sessions in waves W0–W4 and X, plus 6 merge prompts) on `cursor/sw-v23-integration-460c`. It is gated with inference_server through sync points SP1–SP6 (PLAN §5.2). The target is "V2.3 implementation-complete" with multi-process/private evidence complete or honestly pending. Acceptance still needs Codex review and the owner's merge.
