# SwarmAI master plan — V1.7 core platform -> V3.0

Date: 2026-09-21
Status: PLANNING ONLY — section 0 revised by the Fable planning pass (proposed, pending lead review)

## 0. Execution system — audited truth and how work flows (Fable planning pass, 2026-09-21T20:30Z, PROPOSED — pending lead review)

This section is the single human entry point for planning. Machine-readable truth lives in three DAG files checked by `tools/validate_plan.py`; this section summarizes them and must not contradict them.

### 0.1 Audited position (implementation tip `f2b8d5f`, coordination `eebd59a`)

- No version ≥ 1.0 is formally accepted. The highest fully `verified` required set is V1.1.
- The operational product path is V1.4-in-repair: real `$0` brokered missions run; `v14-real-005` and `-007` both failed independent review.
- V1.5, V1.6 and V1.7 exist as **standalone libraries**. The mission path calls none of them. The V1.7 effect boundary has fail-open defects. Packets R13–R16 and R19–R27 were docs-only re-verification.
- Live checkpoints: CP0 local-only (CI blocked), CP1 failed review, CP3 7/9, CP2/CP4/CP5/CP6 absent.
- Full findings: `V17_CODE_AUDIT_20260921_2030_FABLE.md`.

### 0.2 Claim ladder (never collapse these)

| Rung | Meaning | Who sets it |
|---|---|---|
| `implementation` | source + deterministic/real-DB negatives pushed | worker (`impl_complete`) |
| `wired` | reachable from the operational path (API/CLI/mission), not only from tests | worker, proven by an AST or receipt check |
| `live_checkpoint` | CPx run on the pushed tip with real processes/DB/HTTP/inference, failures preserved | worker (`live_checkpointed`) |
| `independent_review` | lead reviewed source + evidence | lead (`verified`) |
| `external_gate` | human/external input outstanding (`EXT-*`) | operator/lead |
| `wall_clock_gate` | real elapsed time outstanding (`WC-*`) | clock; never backfilled |
| `accepted` | artifact fills its milestone role | lead, in `ARTIFACT_REGISTRY.json` only |

A version label is a summary of accepted artifact sets. "V1.7 implementation-complete + live-checkpointed" means rungs 1–3 for every V1.5–V1.7 required artifact, with rungs 4–7 reported as open.

### 0.3 Critical paths

**To V1.7 implementation-complete + live-checkpointed** (27 packets, 5 ready now):
`OPS-CI-01` → `R27a → R27b → R27c → {R27d, R27e}` → `R28a → R28b → R28c → R29a → R28d` → (`R30a` ∥) `{R30b, R31a → R31b}` → `R32a` → `R33a → R33b (CP5)`; in parallel lanes of the same single worker: `R17a (CP3)`, `R02a → R02b (CP1)`; then `R25a → R25b (CP4)`, `R17b → R17c`, `R34a → R34b (CP6)`.
Longest chain: R27a … R28d … R33b … R34b. Nothing on it needs an external gate. Formal V1.7 *acceptance* additionally needs every `EXT-*`/`WC-*` gate below.

**To V2.3:** `R34b` → `18-00 … 18-09 (CP18)` and `19-01 … 19-08 (CP19)` → `20-01 → 20-02 → 20-03` → start `WC-V20-RELIABILITY-168H` at `20-08b` **immediately**, run `20-04 … 20-07` during the clock → `23-01 … 23-12` on a descendant branch while the clock runs (owner authorization required) → `23-13 (CP23)` → `23-14`; `20-09` after 168 real hours.

**To V3.0:** `23-14` → `V30A-001 … V30A-008` ∥ `V30B-001 … V30B-005` → `V30C/D/E/F` → `V30X-001` (freeze) → `V30X-002` (wall clock) → `V30X-003`.

### 0.4 Gates (machine-readable in the `gates` arrays)

| Gate | Owner | Unblocks | Note |
|---|---|---|---|
| `EXT-ACTIONS-BILLING` | operator | exact-tip CI | **only after `OPS-CI-01`** — heartbeat commits caused ~1,000 runs/day |
| `EXT-V14-LEAD-REVIEW` | lead | ART-V14-REAL-E2E, CP1 | after `R02b` |
| `EXT-G13-WIN-VERIFY` | operator or lead | ART-V13-TASK-POOL | Windows run, or a governance decision that corpus verification is platform-neutral |
| `EXT-G13-SEALED-DIGEST` | lead | R06 → R07 → R08, R11 | |
| `EXT-G12-REMOTE-ROUTES` | operator | R09 → R10 → R11 → R12 | ≥ 2 zero-charge providers |
| `EXT-V15-SECOND-HOST` | operator | R18 | physical host |
| `EXT-V10-WORKER-HEARTBEAT` | lead | V1.0-repair acceptance | decide what evidence still counts |
| `WC-LIVE142-24H` | lead/clock | V1.4 acceptance | blocked behind G12 + G13 gates — **the earliest lever is operator action on those two gates now** |
| `EXT-D18-01`, `EXT-D18-02` | operator + lead | split-site V1.8 acceptance, counted recovery evidence | local drill does not wait |
| `EXT-V19-FRESH-ENVIRONMENTS`, `EXT-V19-WINDOWS-HOST` | operator | 19-09, 19-10, support-matrix rows | |
| `WC-V20-RELIABILITY-168H` | lead/clock | 20-08c → 20-09 | protocol freeze `20-08a` can be done today |
| `EXT-D23-FAIRNESS` | lead | 23-12 counted evidence | freeze before counting |
| `WC-V30-CANARY`, `WC-V30-SCHEDULE` | lead/clock | V30B-004, V30X-002 | |

### 0.5 Model routing and delegation

| Work | Tier | Notes |
|---|---|---|
| SP1–SP2 packets with a full spec (`small`/`mid` in the queue) | Sonnet 4.6-class, medium effort | the benchmark worker; spec gives names, error strings, tests |
| SP3 and concurrency/transaction packets (`high`: R27c, R27e, R17b, R34b) | Sonnet 4.6 at high effort, or Opus-class | lead reviews the diff before dependants start |
| Evidence packaging, SHA binding, matrix bookkeeping, file/ID audits | Haiku-class, low effort | never for fence, approval or transaction code |
| Architecture, security review, acceptance design, distributed-state debugging, planning passes | Fable/Opus-class or the ChatGPT lead | output is specs and reviews, not packet code |

Topology is unchanged: one implementation worker, one heartbeat producer. Sub-agents inside that session are for read-only audits only.

### 0.6 Counts

Packets: 62 in the V1.7 queue (35 historical + 27 new; 21 fully specified, 6 medium detail), 47 for V1.8–V2.3, 24 coarse phase groups, 24 V3.0 fine packets (8 canonical `V30A-*`, 16 proposed). Registry artifacts: 86. Gates: 16. Run `python3 docs/coordination/tools/validate_plan.py --ready` for live numbers.

### 0.7 Document map (consolidation)

| Need | Canonical file |
|---|---|
| start a session | `SESSION_START.md` → `DOC_ROUTER.md` |
| artifact state | `ARTIFACT_REGISTRY.json` (lead only) |
| what to do next, V1.7 | `V17_RECOVERY_PACKET_QUEUE.json` + `packets/<ID>.md` |
| what to do next, V1.8–V2.3 | `V17_TO_V23_PACKET_QUEUE.json` + `V17_TO_V23_CEMENTED_EXECUTION_PLAN.md` |
| V3.0 packets and invariants | `FUTURE_EXECUTION_GRAPH_V18_TO_V30.json` (`v30_packets`, `v3_invariants`) |
| why / product sequence | this file |
| live gates | `V17_LIVE_CHECKPOINT_PROTOCOL.md`, `V17_TO_V23_LIVE_CHECKPOINTS.md` |
| schemas, migrations, code map, tests, decisions | the five `FUTURE_*` reference files named in `DOC_ROUTER.md` |
| superseded, do not load | `V16_TO_V30_FORWARD_PLAN_20260921.md`, `V16_TO_V30_TASK_BACKLOG_20260921.md`, `WORKER_PACKET_BACKLOG.md`, `V2_EXECUTION_PLAN.md`, two-lane prompts (`TWO_CURSOR_TEAM.md`, `CURSOR_SESSION_*`, `CURSOR_*_PROMPT.md`) |

Proposed registry deltas for the lead (this pass did not edit the registry): refresh `updated_at`; point `governance.worker_backlog`/`execution_plan` at the two queue files; give `ART-V17-INTEGRATION-MANIFEST`, `ART-V17-SESSION-RECOVERY`, `ART-V17-PERMISSION-NEGATIVES` a `path_or_source_ref` (their specs are `packets/R29a.md`, `R31a.md`+`R31b.md`, `R32a.md`); add the claim-ladder fields of 0.2 per artifact.

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
