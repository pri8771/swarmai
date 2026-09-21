# SwarmAI V1.7 recovery plan — artifact-first, small packets

Status: ACTIVE RECOVERY PLAN
Date: 2026-09-21
Implementation session: exactly one Cursor session
Implementation branch: cursor/v17-single-session
Heartbeat: exactly one producer

## Operating change

The previous instruction "continue to V1.7" is too broad.

New rule:
ONE small packet -> tests/evidence -> commit -> push -> heartbeat -> next dependency-ready packet.

Target packet size:
- ideally 1 artifact concern;
- 1-3 production files;
- 1 focused test file;
- <= ~200 net source lines when practical;
- no broad refactor mixed with evidence work.

A packet may be smaller than this.

Do not bundle "implement V1.6" or "implement V1.7" into one commit.

## Truth rules

- ARTIFACT_REGISTRY remains canonical.
- Current code/evidence audit is V17_CODE_AUDIT_20260921_1432.md.
- v14-real-005 is CHANGES REQUIRED under independent review.
- old donor branches are reusable source, not accepted current implementation.
- no self-acceptance.
- no main merge/public deploy/additional spend.
- SWARM_ALLOW_PAID=false.
- no mock/live substitution.

## Stage 0 — stabilize truth and test execution

### R00 — CI startup classification
Artifact: cross-version verification
Goal: determine why GitHub Actions current-branch jobs fail before step 1.

Do:
- inspect latest failed run with gh locally;
- record whether cause is Actions quota/account/runner/workflow/config;
- if external, create exact USER_ACTION blocker and stop retry spam;
- run CP0 local deterministic checks and package results.

Do not change product source unless workflow config is actually defective.

### R01 — V14 reviewer grounding guard
Artifact: ART-V14-REAL-E2E

Add a small deterministic reviewer guard:
- review must reference actual changed file/diff;
- unrelated target/symbol text invalidates review;
- claimed defect requires a focused regression/check or explicit deterministic semantic check;
- broad unrelated test suite alone is insufficient.

Add focused tests for stale/unrelated review rejection.

### R02 — V14 new live mission
Artifact: ART-V14-REAL-E2E
Depends: R01

Preregister a NEW bounded subsystem different from failed ledger/worktree attempts.
Run genuine mission.
Require CP1.
Preserve failure honestly.
At most two new attempts before stopping to repair a concrete new runtime defect.

## Stage 1 — bring V1.3/V1.4 prerequisite code onto current branch

### R03 — import G13 pool implementation
Artifact: ART-V13-TASK-POOL

Selectively transplant reviewed source/data/tests from product donor tip 534476393257794c4e8ebf8d65f44fd090ab28eb.
Do not transplant legacy autonomous-runner/heartbeat topology.

Files should be limited to G13 corpus/freeze/verification code and tests.

### R04 — current-topology G13 verification
Artifact: ART-V13-TASK-POOL
Depends: R03

Run exact generator/verifier + Ruff + mypy + focused/offline pytest on current session host and bind digests.

The prior HOST-WIN-DEV ownership requirement was topology-specific. Current single-session product-semantic verification is platform-neutral unless a test is actually platform-specific.
Windows portability evidence belongs to later install/support artifacts, not semantic corpus truth.

Any canonical blocker text should be corrected by lead governance, not bypassed silently.

### R05 — reviewer calibration contract
Artifact: ART-V13-REVIEWER-QUALIFICATION
Depends: R04

Implement only:
- reviewer input contract;
- calibration dataset path;
- scorer;
- contamination guard;
- calibration result receipt.

No held-out answers visible.

### R06 — sealed-reference binding
Artifact: ART-V13-QUALIFIED-MATRIX
Depends: R04
Lead/evidence-sensitive.

Bind real sealed references to frozen input IDs without exposing answers on worker-visible paths.
If human/lead-only material is needed, emit exact blocker and continue dependency-independent packets.

### R07 — counted qualification runner
Artifact: ART-V13-QUALIFIED-MATRIX
Depends: R05,R06

Run in small 5-observation batches.
Record model/route/config, all attempts, scorer version, overhead.
Do not retune on held-out.

### R08 — overhead report
Artifact: ART-V13-OVERHEAD-REPORT
Depends: R07

Compute planning/coordination/retry/review/model overhead from actual receipts.

## Stage 2 — remote/adaptive V1.4 gates

### R09 — account-specific remote admission
Artifact: ART-V12-REMOTE-OVERLAP

Inspect available configured provider accounts.
Attempt exact zero-charge admission for at least two routes.
No paid fallback.

If credentials/account entitlement are missing:
- emit USER_ACTION with exact provider/account/secret-ref needed;
- continue R12+ while waiting.

### R10 — remote overlap live
Depends: R09

Run concurrent governed calls on admitted routes.
Prove quota reservation/settlement and route disable -> allowed alternate.

### R11 — live adaptive proof
Artifact: ART-V14-LIVE-ADAPTIVE-PROOF
Depends: R07,R10

Run preregistered adaptive mission:
- multiple tasks;
- qualified route/roles;
- evidence-driven graph change;
- reviewer;
- bounded stop/contraction;
- exact receipts.

### R12 — start required wall-clock V1.4 campaign
Artifact: ART-LIVE142-CAMPAIGN
Depends: canonical LIVE-142 prerequisites

Start immediately once legal.
Do not wait to finish before implementing V1.5-V1.7.
Never backfill time.

## Stage 3 — V1.5 durable workers

Reuse donor source instead of rewriting validated foundations.

### R13 — transplant durable lease schema
Artifact: ART-V15-LEASE-FENCING

Selectively port source from donor commits:
- 630ab780 foundation;
- 92f59faf foundation repair.

Exclude old coordination/autonomous topology.

Run migration + schema focused tests.

### R14 — transplant claim/renew/expire
Depends: R13

Port:
- 7dcefe4c;
- e764834a;
- 685810cc;
only source/test pieces relevant to lease authority.

Run focused claim/renew/expiry tests.

### R15 — durable result acceptance fence
Artifact: ART-V15-LEASE-FENCING
Depends: R14

Small implementation only:
bind result acceptance to:
- project;
- task;
- attempt;
- source/graph revision;
- worker/enrollment generation;
- lease generation;
- cancellation generation;
- reservation/settlement state;
- accepted-result uniqueness.

Tests:
wrong project/task/source/gen/lease/cancel + duplicate/race.

### R16 — worker protocol service
Artifact: ART-V15-WORKER-PROTOCOL
Depends: R15

Implement enrollment/capability/claim/renew/drain/cancel/result submission over durable repositories.
No provider secrets on worker.

### R17 — local restart/reassignment live checkpoint
Artifact: ART-V15-RECOVERY-EVIDENCE
Depends: R16

Run CP3 using separate worker process(es):
register -> claim -> kill -> expire/reassign -> stale result -> valid result -> exactly one accept.

### R18 — physical multi-host proof
Artifact: ART-V15-MULTIHOST-EVIDENCE
Depends: R16

If an actual second host is accessible, execute same protocol across hosts.
If not, preserve exact external blocker; do not fake with aliases.

## Stage 4 — V1.6 scoped knowledge

### R19 — KnowledgeItem contracts
Artifact: ART-V16-PROVENANCE

Implement versioned contracts only:
KnowledgeItem, KnowledgeLink, Tombstone, acceptance state, digests, permission labels.

### R20 — durable knowledge repository
Depends: R19

CRUD/versioning by project/tenant.
Model output defaults observation/hypothesis, never accepted_fact.

### R21 — permission prefilter
Artifact: ART-V16-PERMISSION-RETRIEVAL
Depends: R20

Implement authorization candidate filtering BEFORE ranking.
Test no cross-project content/existence leakage.

### R22 — ranking/context/retrieval receipt
Depends: R21

Rank only permitted candidates.
Emit selected IDs/versions/provenance/token cost/staleness flags.

### R23 — lifecycle
Artifact: ART-V16-SUPERSESSION
Depends: R20

Implement contradiction, supersession, tombstone/deletion and dependent summary/cache/index invalidation.

### R24 — legacy MemoryStore adapter
Depends: R20,R23

Migrate/adapt conservatively.
Never convert generated historical memory into accepted_fact automatically.

### R25 — live knowledge checkpoint
Artifact: ART-V16-CONTEXT-BUDGET-EVIDENCE
Depends: R21,R22,R23,R24

Run CP4 exactly.

## Stage 5 — V1.7 unified actions/tools/session

### R26 — V1.7 action contracts
Artifacts: ART-V17-TOOL-CONTRACT, ART-V17-APPROVAL-BINDING

Add ActionEnvelope, ApprovalGrant, ActionReceipt v1.7 fields:
project/actor/integration/version/operation/destination/payload/effect key/lease gen/cancel gen/policy/timestamps.

Do not wire execution yet.

### R27 — durable approval/effect repository
Depends: R26

Persist approval grants, effect reservations and action receipts.
Unique idempotency/effect scope.

### R28 — migrate ToolGateway to V1.7 boundary
Depends: R27

Order:
normalize -> project/resource authorize -> risk/policy -> exact approval -> effect reserve -> execute -> observe -> reconcile -> expose.

Remove process-local _seen_ops as authoritative exactly-once mechanism.

### R29 — adapter interface + local adapter
Artifact: ART-V17-INTEGRATION-MANIFEST
Depends: R28

Implement adapter contract and version manifest.
Port one local/sandbox tool.

### R30 — API/MCP-style adapter
Depends: R29

Implement one real read/write API-style integration through the same envelope.
Use a controlled local/live service if external credentials would make the test non-reproducible.

### R31 — session-aware web adapter/recovery
Artifact: ART-V17-SESSION-RECOVERY
Depends: R29

Implement session reference, expired/signed-out state, destination preservation, explicit re-auth requirement, resume-to-destination without automatic submission.

Use an actual live local HTTP/session service for checkpoint if external login is unavailable.

### R32 — permission/effect negative suite
Artifact: ART-V17-PERMISSION-NEGATIVES
Depends: R28,R31

Wrong project, payload, destination, expiry, revocation, stale lease, stale cancel, duplicate retry, unknown outcome, unsafe redirect.

### R33 — V1.7 live three-integration checkpoint
Depends: R29,R30,R31,R32

Run CP5.
All three integrations must use the same envelope/approval/effect boundary.

## Stage 6 — integrated checkpoint

### R34 — exact-tip V1.7 audit
Depends: R15,R25,R33 plus all canonical lower gates needed for formal acceptance.

Run CP6.
Create artifact-by-artifact report.
Do not self-accept.

If wall-clock/provider/multi-host evidence is still pending, label:
V1.7 IMPLEMENTATION-COMPLETE / LIVE-CHECKPOINTED / FORMAL-ACCEPTANCE-PENDING.

Only call ACCEPTED V1.7 after every canonical required artifact is accepted.

## Execution behavior

If a packet is blocked on human/external input:
1. write a blocker artifact;
2. heartbeat it;
3. move to the next dependency-independent packet.

Do not sit idle.

If a packet grows beyond its scope:
split it before coding more.

---

# Revision 2 — proposed by the Fable planning pass (2026-09-21T20:30Z, pending lead review)

Basis: `V17_CODE_AUDIT_20260921_2030_FABLE.md`. Stages 0–6 above stay as history. The machine-readable queue (`V17_RECOVERY_PACKET_QUEUE.json`, schema 1.1) and the specs in `packets/` are the executable form; if this prose and the queue disagree, the queue wins.

## What changed and why

1. **R13–R16 and R19–R27 are `evidence_only`.** Their commits changed no source. They re-verified code landed earlier in six broad commits. R17 (CP3), R25 (CP4), R26 and R27 are `gaps_found`.
2. **Library ≠ wired.** Durable workers, scoped knowledge and the V1.7 boundary are not called by the mission path. New wiring packets: `R28d` (actions), `R25a` (knowledge), `R17b`/`R17c` (leased execution, single worker-state authority).
3. **R27 is re-opened as `R27a`–`R27e`** for durable receipts, atomic reserve/execute, repository-owned transactions, approval integrity and the crash window.
4. **R28–R34 are split** into `R28a`–`R28d`, `R29a`, `R30a`–`R30b`, `R31a`–`R31b`, `R32a`, `R33a`–`R33b`, `R34a`–`R34b`. The two simulators are replaced by real-HTTP adapters against a local fixture process, so CP5 can be live.
5. **R02 gets a runtime repair before a third mission:** `R02a` (red→green defect proof), then `R02b` (`v14-real-008`).
6. **`OPS-CI-01` goes first.** Heartbeat commits were triggering about 1,000 CI runs per day; restoring Actions billing before this lands would exhaust it again.

## Order for the single worker

`OPS-CI-01` → `R27a` → `R27b` → `R27c` → `R27d`/`R27e` → `R28a` → `R28b` → `R28c` → `R29a` → `R28d` → `R30b` → `R31a` → `R31b` → `R32a` → `R33a` → `R33b` → `R25a` → `R25b` → `R17b` → `R17c` → `R34a` → `R34b`.
Dependency-free fillers whenever the chain is waiting on a lead diff review: `R30a`, `R17a`, `R02a` → `R02b`.

## Unchanged rules

One packet per commit; tests and evidence produced by that packet's own run; failures preserved; no self-acceptance; `SWARM_ALLOW_PAID=false`; no main merge.
