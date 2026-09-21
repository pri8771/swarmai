# SwarmAI execution plan through V3.0

Status: closure-sweep proposal on `fable/v3-planning`; final Fable audit and independent lead review remain. This document does not accept product artifacts or promote itself into coordination.

## 0. Finish planning in two sweeps

The user wants this sweep plus one final Fable sweep to complete the plan. “Planning complete” means the executable roadmap below has no missing architecture decisions, packet contracts, dependency edges, evidence gates or ownership rules. It does not mean implementation or elapsed campaigns have happened.

**This sweep:** reconcile live state, repair unsafe/incomplete packet semantics, detail all V1.8–V3.0 execution nodes, define terminal deliverables, and make human/JSON plans mechanically agree. **Final Fable sweep:** adversarially check those contracts against current source, split remaining broad packets, close contradictions in place, run the closure checks and return a reviewable commit. No third general planning pass is intended; future changes are bounded defect/source-drift amendments.

### 0.1 Observed baseline and intent

- Repo: `pri8771/swarmai`. Source inspected: `cursor/v17-single-session@f2b8d5f7dfd65530e73c63438c229b9fa428f922`.
- Coordination observed: `4764087c19d3fb0e0ea26b3eded9c1d1807afcd7`; heartbeat at `2026-09-21T22:02:36Z`, packet R27, last meaningful activity `20:05:50Z`. Its scalar says working while next-action text says paused on blockers. Treat that as liveness, not implementation progress.
- Planning baseline: `390ab1def9b3596fecb3c13b3501774770aa89ef`. Read the **independent** review at `coordination/swarm-control:docs/coordination/reviews/FABLE_V3_PLANNING_INDEPENDENT_LEAD_REVIEW_20260921.md`; the older similarly named worker-authored review is superseded on coordination.
- Registry: 86 artifacts, `updated_at=2026-09-21T17:08:54Z`; its states have not been advanced by this sweep. Source/history corroborates library-to-runtime wiring gaps and in-memory action receipts. No new product test pass is claimed.
- Product intent recovered from prior context: several bounded crews cooperate on a shared goal across isolated projects; one kernel controls execution, resources and acceptance. Durable artifacts/evidence, efficient scoped context and genuine SwarmAI self-development are the product, with private self-hosted operation first.

### 0.2 What “the end” delivers

The V3.0 private operational candidate must let an operator install, create scoped projects, declare a bounded objective and then observe authenticated schedule/event triggers producing normally admitted missions. Those missions use qualified zero-spend routes, fair shared capacity, durable workers, scoped knowledge and the single action/approval boundary. Restart, worker loss, restore, cancellation and unknown remote outcomes preserve safety and evidence. Learning can propose/evaluate/canary/roll back a version; self-development can produce an isolated independently reviewed candidate. Packs and audit exports remain tenant scoped.

The operator receives versioned deployment/install/upgrade/rollback/restore runbooks, a support matrix, source/lock/schema/config manifests, artifact/evidence crosswalk and open incident/gate report. No required artifact or safety defect may disappear behind an overall percentage. Public distribution/marketplace, paid fallback, production rollout, main merge and autonomous governance changes remain separate operator decisions.

**End-state predicates:** (a) source implementation and operational wiring complete; (b) required deterministic/DB/adversarial tests passed with no hidden required skips; (c) actual real-world checkpoints completed; (d) all required elapsed windows observed on compatible candidates; (e) independent review and registry acceptance for every required artifact, or an explicit versioned waiver by authorized governance; (f) private operator handoff verified. If (c)–(e) are externally blocked, report exactly which predicates remain false rather than “done.”

### 0.3 Evidence and execution state model

| Dimension | Evidence required | Authority |
|---|---|---|
| Implemented | exact pushed source and focused tests | worker report |
| Wired | operational API/CLI/mission invokes the service, receipt trace | worker report |
| Live-local | real DB/process/fixture mechanics, correctly labeled | worker report |
| Real-world | relevant real service/physical host/outage/fresh install | independent checkpoint review |
| Verified | independent source/evidence review | lead |
| Accepted | every required role/criterion satisfied | registry governance |
| External-pending | named owner, action, blocked claim and next runnable work | operator/lead |
| Wall-clock-pending | actual start/end/identity/monitor continuity | observed time + reviewer |

Packet `depends` are executable prerequisites. `basis` is historical audit provenance. `entry_gates` prevent starting that packet until evidenced; `exit_gates` prevent the corresponding claim, while allowing independent implementation. Split/remediation parents complete only when their children complete. Review holds are explicit gates. Readiness printed from the planning branch is conditional on reviewed adoption, never dispatch authorization.

### 0.4 Detailed delivery sequence

| Stage | Exact work and dependency path | Deliverable and completion proof |
|---|---|---|
| 0 — stabilize execution truth | OPS-CI-01; R02a; R17a; R30a are independent foundations. Keep source/review/CI infrastructure failures separate. | CI churn corrected before account restoration; pre-patch defect proof; complete CP3 negatives; reproducible HTTP fault fixture. |
| 1 — durable effects | R27a→R27b→R27c; independent transaction review; R27d→R27e; independent crash review; R28a→R28b. | Ordered durable receipts, exact payload binding, one execution admission, atomic approval use, current lease/cancel checks, unknown outcomes never blindly replayed. |
| 2 — operational wiring | R28c→R29a; R17a+R28b→R17b; R17b+R29a+R28s→R28d; R17b→R17c; R28d→R25a→R25b. | One adapter registry, true leased worker path, sandboxed task effects, durable worker API, scoped knowledge on real prompts. No static/in-memory operational authority fallback. |
| 3 — V1.7 proof | R30a+R29a+R28a→R30b and R31a→R31b; R32a→R33a→R33b. R33c-1 typed GitHub adapter; R33c-2 real issue/comment/close. R02a→R02b authentic mission. R34a→R34b integrated CP6 matrix. | CP1/CP3/CP4/CP5/CP5-REALWORLD/CP6 each tied to candidate; CP2 and lower acceptance gates listed honestly. Implementation can finish while real-world gate remains pending, but “working” cannot. |
| 4 — V1.8 recovery | 18-00 reviewed handoff; 18-00a freeze supported fencing profile; 18-01/02 authority contracts+storage; 18-03/04 dispatch/result/effect fences; 18-05/06 manifest+backup; 18-07 restore; 18-08 negative matrix; 18-09 actual outage. | Restore starts read-only, old site externally fenced before new writes, unknown effects preserved, measured RPO/RTO. Restored DB epoch alone never establishes authority. |
| 5 — V1.9 productization | 19-00 beta criteria; 19-01/02/03 manifests+grant lifecycle+gateway; 19-04/05/06 install/upgrade/rollback+diagnostics; 19-07 own-runtime selfdev; 19-08 combined CP19; 19-09 external install, 19-10 real Windows. | Fresh operator can run/recover a mission; extension cannot widen authority; selfdev yields independently reviewable isolated candidate. Support only evidenced environments. |
| 6 — V2.0 candidate | 20-01 integration/hardening; 20-02 candidate freeze; 20-03 exact checks; 20-04–07 install/rollback/security/performance. 20-08a frozen protocol; 20-08b start after reviewed preflight; 20-08c seven-day completion; 20-09 independent release review. | One supported integrated private candidate; 168h compatible observation, required drills and lower acceptance gates. No release/merge implied by review. |
| 7 — V2.3 operations | 23-01–03 durable fair selection; 23-04/05 reservations/recovery; 23-06 drain/cancel; 23-07 single scheduler restart; 23-08 explain UI; 23-09 packs; 23-10 portability; 23-11 trust/locality placement; 23-12 frozen fairness; 23-13 real fleet CP23; 23-14 review. | At least two physically distinct nodes, constrained capacity, non-fixture external action/provider, restart/drain/reassignment, zero tenant leakage. No second scheduler or budget authority. |
| 8 — V3 objectives | V30A-001–008: immutable versions, explicit missed-run policy, authenticated events, idempotent proposals, normal admission, stop/revoke, shared fairness, governed version bridge and operator views. | Real recurring/event objective is bounded and observable; no trigger grants new authority or duplicates a mission. |
| 9 — V3 learning and ecosystem | V30B-001–005 validation/calibration/freeze/sealed eval/review/canary/rollback/drift; V30C allocator inputs; V30D own-runtime selfdev; V30E private publisher/revocation; V30F scoped causal audit. | Promotion uses independent evidence and deterministic rollback; learning cannot change permissions/spend/reviewer/evidence rules. Existing packs/grants/scheduler reused. |
| 10 — V3 closure | V30X-001 freeze workload and thresholds; V30X-002 real elapsed objective+external effect+canary/rollback; V30X-003 independent all-artifact audit and operator handoff. | All six V3 artifacts, lower-version gates, exact candidate evidence, runbooks and required elapsed evidence reconciled. No self-acceptance. |

Every future row is decomposed into individual contracts in `FUTURE_PACKET_CATALOG_V18_TO_V30_20260921.md`, generated from the two future JSON files. Those **71 contracts** contain source surfaces, exact behavior, negative cases, evidence and exit conditions. Near-term V1.7 detail stays in `packets/`. No packet is executed from this overview alone.

### 0.5 Start clocks early without invalidating them

- LIVE-142: start after frozen G10–G14 prerequisites and lead start review. It needs **24 actual hours**. G12/G13 eligibility/qualification are the upstream operator levers; a passing local tool fixture does not remove those requirements.
- V2.0: prepare 20-08a while V1.7 implementation proceeds; start 20-08b at the earliest point the frozen protocol/start review permits. It needs **168 actual consecutive hours**. Compatible drills may overlap; identity/behavior changes follow invalidation rules. Remove the prior unsupported assertion that early failed starts cost nothing.
- Keep campaign source/config immutable on a deployment snapshot. The same single implementation worker can continue later-version code in its authorized checkout; that must not mutate the running campaign. One campaign monitor is not a second implementation worker/heartbeat producer.
- V3: freeze target-specific canary count/duration/guardrails before the canary and schedule observation. No invented universal learning threshold or fake elapsed time. Failed/contaminated learning is preserved and cannot be relabeled as promotion.

### 0.6 Architecture freeze and boundaries

The required decisions now have implementation defaults in `FUTURE_OPEN_DECISIONS_FREEZE_POINTS_20260921.md` and transaction algorithms in `FUTURE_TRANSACTION_ALGORITHMS_V18_TO_V30_20260921.md`. Final Fable must confirm these are implementable on the actual source.

1. PostgreSQL/SQLAlchemy/Alembic retain all runtime authority; receipts and artifact refs carry provenance. No new scheduler, authority DB, permission system or generic framework.
2. Attempts and receipt sequence are different identities. Late execution completion cannot replace a newer attempt. A timeout stops waiting, not necessarily a thread/remote action; unknown blocks retry absent definitive safe-retry evidence.
3. Every mutating operational action, including idempotent writes, uses durable authority. Test commands run untrusted code only through the R28s enforced sandbox; a prefix allowlist is insufficient. Credentialed GitHub is a narrow typed control-plane adapter, never arbitrary `proc.run`.
4. The observed sandbox runner only invokes host subprocess; R28s adds actual private-development container enforcement, with environment availability gated. Leases must validate identity, status, expiry, revisions and generations. Authenticated actor context is not a string supplied by the worker. Cancellation serializes execution admission, without promising rollback of an already-issued external effect.
5. Knowledge is untrusted data in prompts, permission-filtered before ranking; imported/learned content never becomes system authority. No denied-item count leakage.
6. Recovery defaults to externally fenced manual activation after restore. Automatic multi-site failover/public publisher trust are explicitly unsupported until separately designed/approved; their interfaces are preserved without pretending proof exists.
7. Fairness credits accrue once per persisted round, not once per poll. DispatchIntent reserves existing capacities and reconciles conservatively. Packs reuse extension lifecycle; candidate manifests use existing artifacts rather than gratuitous new tables.
8. Objective proposals enter existing mission admission. Learning/selfdev preserve protected policy and independent review. A private digest-pinned ecosystem is the first V3 completion scope; public marketplace/signature distribution remains separate.

### 0.7 Remaining human/environment inputs

| Input | Owner | Blocks | Work proceeds meanwhile |
|---|---|---|---|
| Actions account availability | operator | exact-tip hosted CI claims | OPS-CI-01, local source/tests |
| Authentic sealed references and corpus review disposition | lead/evaluator | counted G13, downstream adaptive/learning evidence | evaluator mechanics and other implementation |
| >=2 admitted zero-charge remote routes | operator + eligibility probes | G12 overlap and G14/LIVE-142 prerequisite | local qualified execution and tool wiring |
| Second physical node / real Windows / fresh install environment | operator | R18, CP23, environment support claims | durable worker and packaging code |
| Existing GitHub identity + exact real action approvals | authorized runtime/operator | R33c-2 and CP30 real effect | adapter mechanics and local fault tests |
| Deployment fencing, backup retention/encryption/key ownership, RPO/RTO targets | operator + lead | counted recovery deployment | fail-closed interfaces, local dry run |
| Independent reviews and frozen fairness/learning thresholds | independent lead | named review/counting gates | dependency-independent packets |
| Actual elapsed 24h / 168h / declared canary/schedule duration | observed clock | respective accepted claims | later implementation on unchanged campaign base |

Defaults never fabricate these inputs. Each pending input has an owner/action in JSON. Lead must disposition contradictory G13 Windows language without silently editing the artifact registry here.

### 0.8 Final Fable audit — finite completion checklist

- [ ] Re-fetch exact coordination/planning/implementation tips; distinguish source drift from heartbeat-only commits. Read independent lead review, not obsolete worker-authored approval.
- [ ] Trace near-term operational entrypoints end-to-end and confirm every proposed service exists or is explicitly introduced by an upstream packet.
- [ ] Adversarially audit effect/hash/replay, timeout/late-writer, atomic approval, lease expiry/revocation, sandbox/credential isolation and Github unknown-outcome semantics.
- [ ] Confirm receipt schema, migration ownership, lock order and rollback are mutually consistent. Split source packets >3 production files unless a documented inseparable transaction is independently reviewed.
- [ ] Ensure all 71 future contracts have executable artifact/dependency/surface/behavior/negative/evidence/exit definitions; fill thin contracts rather than adding roadmaps. Preserve stable IDs via split aggregates where required.
- [ ] Match every required registry artifact to producing packets, required checkpoint/review/gates and terminal claim; fix missing dependencies such as objective-learning integration before CP30.
- [ ] Check real-world proof at CP5/18/19/20/23/30 and wall-clock start/restart rules; no fixture substitution.
- [ ] Run plan validator and its negative tests; render catalog and prove no drift. Review diff against planning base: no source, worker state, registry acceptance or canonical writes.
- [ ] Commit/push only `fable/v3-planning`; return exact SHA, remaining external inputs, first executable queue, and per-check closure evidence. No self-approval/promotion.

Final status: `PLAN_COMPLETE_REVIEW_PENDING` only when every checklist item is supported and no unowned architecture gap remains; still finish `READY_FOR_LEAD_REVIEW`. If a genuine new architectural blocker remains, name it and its exact dependency instead of requesting another vague sweep.

### 0.9 First executable handoff and validation

Candidate-ready now, after reviewed adoption: **OPS-CI-01, R27a, R30a, R17a, R02a**. Prefer the R27 durability chain; while an independent review is pending, use the other ready foundations. After R28b, leased runtime R17b must precede operational R28d; do not restore the former circular/static-fence shortcut. R27d and separate-process R17c are mandatory CP6 implementation inputs. R33c is mandatory for working/real-world claims.

```sh
python3 docs/coordination/tools/validate_plan.py --ready
python3 -m unittest discover -s docs/coordination/tools -p 'test_validate_plan.py' -v
# After a reviewed JSON contract edit:
python3 docs/coordination/tools/validate_plan.py --render
```

Counts in this revision: **70 V1.7 nodes** (historical/aggregate included), **47 V1.8–V2.3**, **24 V3 execution contracts**, **24 coarse groups**, **25 gates**, **86 registry artifacts**. Counts are inventory, not progress. Model routing is guidance: Sonnet 4.6 medium for bounded routine code; high effort plus independent review for state/security/recovery; lower tier for read-only indexing and evidence packaging. Fable's last sweep is planning only.

### 0.10 This sweep's retained evidence

- Initial coordination snapshot was 96eb563; refresh to 4764087 contained heartbeat/status/progress plus LEAD-20260921-041 only. Source remains f2b8d5f; planning base remains 390ab1d; main remains b9141fa3150f853586dede0334a47b344571bc16. The active canonical packet is still broad R27; this proposed queue has not dispatched or replaced Cursor's assignment.
- Source inspections: durable effect repository/gateway, worker result fence, mission runtime/controller/store, worker transport and sandbox runner. The host subprocess runner's environment scrubbing does not enforce network/filesystem isolation; R28s is the missing prerequisite.
- Standalone Python timeout experiment: cancellation of wait_for(to_thread(...)) returned timeout while the underlying thread later performed its effect. This is language-behavior evidence, not SwarmAI runtime validation; R27e/R28a require managed execution and conservative remote-outcome handling.
- Plan validation: dependency and split/remediation DAGs, artifact coverage, defined typed gates, catalog digest and 14 negative tests pass. git diff --check passes. These checks validate planning consistency only; no product suite or real-world checkpoint was run in this sweep.
- Scope: planning documents and their validation tools only. Cursor source/state, registry acceptance, historical reviews and canonical coordination are unchanged by this sweep. Independent baseline approval does not approve this revision.

The older product-through-line below remains context. Packet JSON/specs and this closure section replace conflicting execution-order prose. Registry acceptance and the independent real-world policy are not weakened.

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
