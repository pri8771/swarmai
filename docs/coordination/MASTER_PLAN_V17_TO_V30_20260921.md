# SwarmAI master plan — V1.7 core platform -> V3.0

Date: 2026-09-21
Status: PLANNING ONLY

## Product through-line

SwarmAI should evolve by extending one authority model, not by layering unrelated frameworks:

```
V1.7
durable workers + scoped knowledge + unified tool/effect boundary
  |
  v
V1.8
site authority + backup/restore + split-brain safety
  |
  v
V1.9
installability + extensions + bounded self-development
  |
  v
V2.0
one integrated, supportable, reliability-tested product candidate
  |
  v
V2.3
multi-mission operations + capability packs + portability + observability + fleet policy
  |
  v
V3.0
persistent authorized objectives + governed learning + controlled self-development
```

No later layer may bypass lower-layer:
- project/tenant authorization;
- provider eligibility;
- budgets/quotas/reservations;
- worker/result fencing;
- tool approval/effect fencing;
- site/authority epoch;
- independent evidence requirements.

## V1.7 milestone — core execution platform

Assumed capability target:
- real mission runtime;
- governed inference;
- qualified routing;
- elastic task graph;
- durable distributed worker protocol;
- scoped reusable knowledge;
- unified ActionEnvelope/ApprovalGrant/ActionReceipt boundary.

V1.7 is the substrate for everything after it.

## V1.8 — authoritative recovery

### Product outcome
The system survives control-plane/site failure without duplicate dispatch, duplicate consequential effects, stale result acceptance, or split-brain authority.

### Build order
1. Define durable SiteAuthority / SiteEpoch.
2. Bind new dispatch to current epoch.
3. Bind lease/result acceptance to current epoch.
4. Bind consequential effect acceptance to current epoch.
5. Add deployment manifest.
6. Add consistent backup format/metadata.
7. Add restore + reconciliation workflow.
8. Add split-brain/stale-site negatives.
9. Run outage/recovery drill and measure RPO/RTO.

### Exit
Implementation is complete when backup/restore/reconciliation can be executed and all authority fences are testable. Acceptance still requires real outage/recovery evidence where the canonical artifact says so.

## V1.9 — installable/extensible beta

### Product outcome
A fresh environment can install SwarmAI, extensions can be enabled per project without hidden authority, and SwarmAI can prepare code improvements without approving/merging itself.

### Build order
1. Freeze extension manifest + compatibility/permission model.
2. Extension registry and project-scoped lifecycle.
3. Integrate extensions through the V1.7 tool/action boundary.
4. Add install doctor + clean-install manifest.
5. Add upgrade/migration/rollback orchestration.
6. Create support/diagnostic bundle with secret redaction.
7. Run fresh-environment install(s).
8. Run one real bounded self-development issue to PR candidate.
9. Preserve independent review boundary.

### Exit
Fresh install/upgrade/rollback and extension lifecycle are deterministic and testable; external environment evidence remains separate from implementation-complete.

## V2.0 — integrated product candidate

### Product outcome
All V1.x groups operate as one product, not a collection of isolated features.

### Candidate freeze
Freeze:
- source SHA;
- migrations/schema version;
- dependency lock;
- runtime/deployment manifest;
- provider/tool/extension versions used for evidence;
- policy versions;
- test/evaluation protocol versions.

### Work
1. Finish hardening defects.
2. Integrate only reviewed source.
3. Run migrations from clean state and upgrade state.
4. Populate support matrix only from evidence.
5. Run install journey.
6. Run upgrade/rollback journey.
7. Run threat/security review.
8. Run performance/resource baseline.
9. Freeze reliability protocol.
10. Run real elapsed reliability campaign.
11. Independent release review.

### Exit
"Implementation-complete candidate" can exist before elapsed evidence completes.
"Accepted V2.0" cannot.

## V2.1 / V2.2 — optional internal implementation increments

The canonical registry does not currently define V2.1 or V2.2 artifact sets.

Use them only as internal checkpoints if useful:

### V2.1 suggested scope
- operator/admin UX;
- normalized telemetry;
- support diagnostics;
- install/update polish;
- no new authority model.

### V2.2 suggested scope
- scheduler persistence/reservation primitives;
- capability-pack substrate;
- portability schema stabilization;
- no claim of separate product acceptance milestone.

Do not create acceptance claims until the registry explicitly defines them.

## V2.3 — operational platform

### Product outcome
SwarmAI can run many projects/missions concurrently and fairly across heterogeneous workers/providers/tools without widening authority.

### Scheduler
Replace/extend process-local fairness state with durable project/mission scheduling state.

Must provide:
- project-level fair service;
- mission/task priority and aging;
- deterministic tie-break;
- resource reservation intent;
- provider quota reservation;
- worker capacity reservation;
- tool/effect capacity where relevant;
- backpressure;
- cancellation/drain;
- site-epoch fencing;
- explainable SchedulerDecisionReceipt.

### Capability packs
Formalize versioned packages containing bounded:
- procedures;
- adapters;
- schemas;
- prompts/templates;
- capability declarations;
- tests/migrations.

Pack enablement is project-scoped and cannot implicitly widen tool/provider/data permissions or model qualification.

### Portability
Export/import bundle should include versioned metadata and references, never secret values:
- project configuration;
- accepted reusable knowledge/provenance;
- capability pack config;
- policy refs;
- artifact/evidence refs;
- migration/version manifest.

### Observability
One event model for:
- mission/task;
- scheduler;
- worker;
- provider reservation/settlement;
- tool/effect;
- extension;
- recovery;
- failure/reconciliation.

Read surfaces are read-only. Any mutation from UI/API still goes through the same action/approval boundary.

### Fleet
Placement considers:
- trust class;
- project/tenant;
- capability;
- privacy/locality;
- tool/provider reachability;
- worker/site epoch;
- resource capacity;
- drain state.

### Exit
Deterministic scheduler tests plus multi-process/private live evidence on a frozen candidate.

## V3.0 — persistent governed operation

### Product outcome
SwarmAI can operate continuing objectives and improve procedures/code over time without acquiring self-permission.

### Persistent objectives
An ObjectiveContract is an authorization envelope + goal + trigger policy, not a free-form infinite agent.

Each trigger creates a bounded MissionProposal that goes through normal mission admission.

Required:
- versioned immutable objectives;
- schedule/event/manual triggers;
- trigger dedupe;
- rate/max-active bounds;
- allowed mission templates;
- tool/data/provider/spend envelope;
- pause/revoke/expiry;
- stop conditions;
- audit trace.

### Governed learning
Learning is versioned proposal promotion, not live memory mutating production behavior.

Pipeline:
1. observe;
2. propose one bounded change;
3. static/policy/security validation;
4. calibration;
5. freeze;
6. sealed held-out evaluation;
7. independent review;
8. bounded canary;
9. accept or rollback;
10. drift/revalidation.

Protected authority cannot be autonomously learned:
- permissions;
- spend;
- secrets;
- project boundaries;
- release/merge/deploy authority;
- grader/evidence rules.

### Resource allocator
V3 allocator operates on top of V2.3 scheduler and cannot bypass it.

It may optimize:
- objective scheduling priority within authorized bounds;
- capacity assignment;
- provider/worker mix;
- deadlines.

It may not gain throughput by hidden starvation, quota evasion, privacy relaxation, or hidden cost shift.

### Controlled self-development
Self-development is a LearningProposal subtype:
- isolated branch/worktree;
- bounded diff;
- deterministic tests/evals;
- independent reviewer;
- canary where appropriate;
- rollback;
- no self-merge/release;
- cannot modify its own governance/evaluation/reviewer rules in same proposal.

### Capability ecosystem
Signed/versioned capability artifacts with:
- publisher/provenance;
- permissions;
- compatibility;
- migrations;
- tests;
- revocation.

No unrestricted arbitrary-code marketplace.

### Fleet tenancy/audit
All objective/learning/fleet operations remain tenant/project scoped with exportable receipts and cross-tenant negative tests.

## Critical path after V1.7

1. SiteEpoch + result/effect fencing.
2. Backup/restore/reconcile.
3. Extension boundary.
4. Install/upgrade/rollback.
5. Integrate/freeze V2.0 candidate.
6. Security/performance/install evidence.
7. Start required reliability wall clock early.
8. Durable multi-mission scheduler.
9. Resource reservations/backpressure/fairness.
10. Capability packs + portability + observability + fleet.
11. Objective contract and trigger receipts.
12. Learning proposal/eval/canary/rollback.
13. Resource allocator + controlled selfdev.
14. V3 integrated private-live acceptance.

## Prep principle

Before each phase starts, have these already frozen:
- input schema;
- state machine;
- owned source paths;
- negative-test list;
- evidence format;
- exit condition;
- explicit non-goals.

That is the primary mechanism for keeping the worker fast and preventing redesign loops.
