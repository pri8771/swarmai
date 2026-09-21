# SwarmAI forward architecture plan — V1.6 through V3.0

> **SUPERSEDED (2026-09-21, proposed by Fable planning pass):** history only. Canonical: `MASTER_PLAN_V17_TO_V30_20260921.md` and the queue/graph JSON files. See `DOC_ROUTER.md`.

Date: 2026-09-21
Status: FUTURE PLANNING ONLY
Authority: does not change artifact acceptance or authorize V1.8+ implementation in the current Cursor run.

Canonical registry remains `ARTIFACT_REGISTRY.json`.

## Architecture through-line

There should be ONE coherent authority model:

V1.5 durable leases/results
-> V1.6 scoped knowledge
-> V1.7 unified actions/approvals/effects
-> V1.8 recovery/site authority
-> V1.9 install/extensions/controlled self-development
-> V2.0 integrated product candidate
-> V2.3 multi-mission operational platform
-> V3.0 persistent objectives + governed learning/self-development

Later layers may extend authority, but may not bypass lower-layer fencing.

---

# V1.6 — scoped reusable knowledge

## Product outcome
SwarmAI can reuse verified facts/procedures across missions without loading whole histories or leaking cross-project data.

## Architecture
- versioned KnowledgeItem/KnowledgeLink/Tombstone domain;
- provenance and content/source digests;
- explicit observation/hypothesis/accepted_fact/procedure distinctions;
- permission-first retrieval;
- contradiction/supersession lifecycle;
- deletion invalidation across index/cache/summary/export;
- retrieval receipts and token accounting;
- adapter from existing mission MemoryStore.

## Evidence
- later mission reuses accepted knowledge;
- hypothesis is never silently promoted;
- cross-project leak negatives;
- supersession/deletion immediately alter future retrieval;
- measured bounded-context savings.

## Dependency
Durable schema base and stable G13/eval path.

---

# V1.7 — unified tools/browser permissions and effect safety

## Product outcome
Every local tool, API/MCP/app, and browser action enters one auditable policy/approval/effect boundary.

## Architecture
- ActionEnvelope;
- ApprovalGrant;
- ActionReceipt;
- exact payload/destination/operation binding;
- effect reservation/idempotency;
- ToolGateway;
- adapter interface/version manifest;
- browser session refs without secret material;
- unknown-outcome reconciliation.

## Evidence
Three real integration classes:
1. local/sandbox;
2. API/MCP;
3. browser/session-aware.

Negative proof for wrong scope, changed payload, expiry/revocation, cancel, stale generation, duplicate retry and login recovery.

---

# V1.8 — recovery, backup and site authority

## Product outcome
A failed site/control plane can be recovered without split brain, duplicate dispatch, or stale effect acceptance.

## Architecture tasks
1. Durable site/authority epoch.
2. Bind dispatch, worker lease, result acceptance and effect acceptance to authority epoch.
3. Deployment manifest with actual runtime/dependency identities.
4. Backup format and consistency boundary.
5. Restore/reconciliation procedure.
6. Split-brain fencing.
7. Outage/recovery drill harness.
8. RPO/RTO measurement from real drills.

## Required negatives
- stale old site cannot dispatch;
- stale old site cannot accept results/effects;
- duplicate recovery attempt fails closed;
- partial restore does not silently look healthy.

---

# V1.9 — beta, extensions, installability, controlled self-development

## Product outcome
A fresh user can install SwarmAI, enable bounded extensions, and run controlled self-development without giving plugins or SwarmAI itself hidden authority.

## Architecture tasks
1. Extension manifest/version/signature/hash contract.
2. Capability/scopes declared before enablement.
3. Extension lifecycle: install -> enable for project -> drain -> disable -> uninstall.
4. Clean install/upgrade/rollback path.
5. External install evidence on fresh environments.
6. One real self-development issue:
   - bounded issue;
   - isolated branch/worktree;
   - implementation;
   - tests;
   - independent review;
   - no self-merge/self-release;
   - failed attempts retained.

## Security
Extension permissions cannot exceed project/user policy and cannot silently modify acceptance/evidence rules.

---

# V2.0 — integrated product candidate

## Product outcome
All V1.x capability groups operate as one installable, supportable, observable product candidate.

## Workstreams
1. Foundation hardening completion.
2. Reviewed-slice integration only.
3. Integrated candidate freeze with exact source/config/dependency identities.
4. Capability/support matrix grounded only in evidence.
5. Clean install journey.
6. Upgrade/migration/rollback.
7. Security/threat review.
8. Performance/resource baseline.
9. Real reliability campaign under frozen protocol.
10. Independent release review.

## Evidence rule
Implementation-complete != accepted.
Wall-clock evidence cannot be backfilled.

---

# V2.1 / V2.2 — internal maturation increments

There are currently no canonical standalone artifact families for 2.1/2.2.

Use these only as optional implementation increments if needed, not as invented acceptance milestones.

Suggested decomposition:
- V2.1: operator/admin UX, observability plumbing, install/upgrade polish, support diagnostics.
- V2.2: multi-mission scheduler implementation precursor, capability-pack substrate, portability schema stabilization.

Do not change canonical versioning until registry/roadmap explicitly defines these versions.

---

# V2.3 — multi-mission operational platform

## Product outcome
Many authorized missions/projects run concurrently with fair resource allocation, portable capability packs, fleet policy, observability and no hidden authority widening.

## Workstreams

### Multi-mission scheduler
- project/mission/task hierarchy;
- fairness/weights/aging;
- deterministic tie-breaking;
- durable scheduler policy version;
- atomic resource reservation intent;
- backpressure;
- cancellation/drain;
- single authority epoch for dispatch;
- explainable SchedulerDecisionReceipt.

### Capability packs
- versioned pack manifest;
- code/config/schema/tool/integration declarations;
- explicit project enablement;
- drain/disable;
- no implicit permission/model-qualification change.

### Portability
- export/import bundle;
- schema/version manifest;
- knowledge/provenance;
- capability configs;
- accepted artifact/evidence refs where portable;
- secret references, not secret values.

### Observability
- read-only operational views by default;
- any dashboard mutation must pass the same authenticated action/approval path;
- queue, resource, worker, provider, effect and failure visibility.

### Fleet policy
- worker trust classes;
- placement constraints;
- locality/privacy/provider/tool reachability;
- quotas/fairness;
- drain/migration;
- stale worker/site fencing.

## Acceptance
Deterministic scheduler tests PLUS private/live multi-process evidence.
Simulation never substitutes for required live evidence.

---

# V3.0 — persistent objectives, governed learning and controlled self-development

## Product outcome
SwarmAI can operate continuing authorized objectives, create bounded missions over time, learn from outcomes, allocate resources and improve procedures/code under independent governance.

Persistent objectives are NOT permanent self-permission.

## Workstreams

### Persistent objective contract
- objective ID/version;
- owner/project;
- desired outcome;
- bounded authority/scope;
- budget/resource policy;
- schedule/event triggers;
- pause/stop conditions;
- mission proposal receipts;
- duplicate trigger prevention;
- objective audit trail.

### Governed learning
- versioned LearningProposal;
- provenance/source mission IDs;
- one bounded hypothesis/change per proposal when attribution requires it;
- calibration vs held-out separation;
- proposer cannot see held-out answers used to accept itself;
- deterministic/security/policy checks;
- canary;
- independent acceptance/rejection;
- reproducible rollback;
- drift/expiry/revalidation.

### Resource allocator
- allocate workers/provider/tool capacity across persistent objectives;
- preserve V2.3 fairness, quota, privacy, cost and permission invariants;
- no throughput "win" from hidden starvation/cost shifting.

### Controlled self-development
- self-development proposal cannot modify its own governance/reviewer/evidence contract in the same proposal;
- isolated branch/worktree;
- tests/evals;
- independent review;
- canary;
- no self-merge/release;
- rollback and stale-worker fencing.

### Capability ecosystem
- signed/versioned capability packages;
- trust/provenance;
- permission declarations;
- compatibility;
- install/enable/drain/disable;
- review/revocation.

### Fleet tenancy/audit
- project/tenant isolation;
- authority epoch;
- worker trust/placement;
- audit receipts;
- exportable compliance evidence;
- cross-tenant negative tests.

## V3 acceptance principle
Models can propose. Deterministic software + frozen policy + independent evidence decides.
No learning path may erase failures, hide cost, widen permissions, bypass provider policy, or self-accept.

---

# Suggested sequencing after V1.7

1. V1.8 site epoch/fencing before complex recovery.
2. V1.9 extension boundary before capability ecosystem work.
3. V2.0 integrated candidate + install/security/performance.
4. Freeze/run real reliability campaign.
5. V2.3 scheduler first, then packs/portability/observability/fleet.
6. V3 objective contract + learning governance in parallel at design level.
7. Implement V3 resource allocator only after V2.3 scheduler/fleet evidence.
8. Implement controlled self-development only after V2 release/eval pipeline is stable.
