# ART-V20-RELIABILITY-PROTOCOL — integrated reliability observation

Status: drafting
Target: V2.0
Owner: ChatGPT lead
Last advanced: 2026-09-21

This protocol is a pre-run contract. It does not claim the V2.0 candidate exists or that any wall-clock observation has elapsed.

## 1. Purpose and relationship to implementation-complete V2.0

The immediate engineering target may be an implementation/artifact-complete V2.0 candidate before all elapsed-time evidence finishes. **Accepted V2.0 is later:** its integrated candidate must satisfy this reliability protocol plus the security, install/upgrade, support-matrix, performance and independent-release-review artifacts.

A passing unit/integration suite, a green CI run, or a short smoke cannot substitute for the real observation window. Earlier V1.4 / LIVE-142 evidence also remains independently required by its own protocol; do not backfill or reuse elapsed time without explicit protocol compatibility.

## 2. Candidate freeze

Before reliability evidence counts, publish one immutable candidate manifest containing:
- exact `cursor/v2-integration` code/tree SHA;
- dependency/lockfile identity and Python/Node/runtime versions;
- Alembic migration head and database engine/version;
- config/policy schema versions and a secret-safe configuration digest;
- broker/resource-policy version;
- exact admitted route/account aliases, model IDs/configs and qualification-profile versions;
- worker protocol / lease-fencing schema version;
- knowledge/provenance schema and retrieval-policy version;
- tool/action/approval contract version and enabled adapter manifest;
- extension manifest/compatibility versions;
- site epoch / backup / restore protocol version;
- supported-capability matrix version;
- test/evidence bundle hashes and the start command/profile used for observation.

The manifest contains aliases/digests, never credentials, cookies, browser state or private identity mappings.

### Invalidating change rule

Any material change to runtime behavior, authorization, durable schema/migration, broker/admission, model qualification/routing, worker fencing, knowledge permission logic, consequential tool/effect semantics, extension loading, backup/restore or site-epoch fencing invalidates the affected observation evidence. Record:
1. change SHA;
2. affected invariants/metrics/drills;
3. whether the full observation clock restarts or only a bounded drill must rerun;
4. lead review of that decision **before** new evidence is counted.

Do not decide after seeing favorable results that a material change was non-material.

## 3. Observation clock

V2.0 final reliability observation is **7 consecutive wall-clock days**, inherited from the approved roadmap unless an explicit owner/lead protocol amendment is committed before the campaign begins.

Record UTC `started_at` only when the frozen candidate is actually running. Record `ended_at` from observed wall-clock time. Downtime, host unavailability and monitoring gaps remain part of the record; never simulate, accelerate or backdate them.

The campaign may continue across expected process/worker/provider failures if recovery behavior is itself under test. A material candidate-invalidating source/config change creates a new campaign identity according to the invalidation rule above.

## 4. Evidence collection model

Every mission/drill receives an immutable run ID and evidence record with:
- candidate SHA + config manifest digest;
- start/end timestamps;
- project/mission/task IDs using non-sensitive aliases;
- entry surface (console/API/CLI/worker);
- planned scenario / expected failure class;
- actual final state;
- model routes/calls/tokens/cost or explicit `unknown`;
- worker lease/attempt/result receipts;
- tool/action/approval/effect receipts where applicable;
- graph changes and retries;
- evidence/artifact hashes;
- unexpected exceptions and operator intervention;
- result disposition: valid / invalidated / under-review.

Keep failures and retries. Do not overwrite a failed attempt with a later pass or report only successful missions.

## 5. Mission-level metrics

For every supported mission record:
- final accepted / failed / blocked / cancelled status;
- whether final state matches the declared contract;
- unexpected application exceptions;
- end-to-end latency and active execution time where measurable;
- model calls, input/output tokens and cost or explicit unknown;
- retries / repair rounds / reviewer challenges;
- worker leases, renewals, expiries, reassignments and stale-result denials;
- provider reservations, settlements, route loss and fallback/wait behavior;
- tool approvals/actions/effect-key reconciliation and duplicate attempts;
- output artifact integrity and acceptance checks;
- knowledge retrieval count/tokens/provenance/permission filtering;
- cancellation/deadline propagation;
- human intervention and exact reason.

## 6. System-level metrics

Capture at least daily and around every injected/real failure:
- API/control-plane restarts and readiness transitions;
- worker heartbeat age, lease expiry and reassignment count;
- durable queue depth, oldest-ready age and blocked-task count;
- DB connection/migration/storage failures;
- accepted-result duplicate count;
- consequential-effect duplicate count;
- cross-project authorization-denial failures;
- stale-site/site-epoch rejection count;
- backup age and last verified restore age;
- provider quota/reservation reconciliation status;
- local/remote worker resource utilization when available;
- explicit monitoring gaps.

No unavailable metric may be silently treated as zero.

## 7. Failure classification

### Expected and correctly handled
- unsupported task or unsupported capability;
- quota exhaustion / zero remaining allowance;
- denied project/tool/provider permission;
- explicit cancellation or deadline;
- unqualified, unavailable or price-unknown route denied fail-closed;
- intentionally injected worker/provider/process outage;
- stale worker generation, lease, task revision, source revision, cancellation generation or site epoch rejected;
- invalid extension/config rejected before unsafe execution.

These are successful **safety outcomes** only if the specified denial/recovery behavior occurs. They are not successful business missions.

### Unexpected / release-blocking until triaged
- unhandled exception on a declared supported path;
- authorization/project-data leak;
- credential/secret leakage;
- paid/unknown-cost route called without admission;
- known-answer/mock-success/runtime-fixture fallback on operational path;
- duplicate accepted result or consequential effect;
- stale worker/site result accepted;
- accepted mission/artifact lost beyond a declared recovery limitation;
- false success/readiness/qualification claim;
- deadlock, stuck lease or queue requiring undocumented manual mutation;
- recovery restoring inconsistent authority/state;
- hidden monitoring/evidence gap large enough to make a claimed invariant unobservable.

Every unexpected event receives a defect ID, severity, root-cause status and candidate-impact decision. Do not exclude it from campaign totals because it was later fixed.

## 8. Mandatory drill matrix

Each drill is preregistered before execution with expected observable outcome.

1. **Control restart:** real service stop/start; durable mission reopens through a different process.
2. **Worker death:** kill a real worker holding a durable lease; lease expires/reassigns; stale result is denied.
3. **Duplicate delivery/result:** repeated completion attempt produces exactly one accepted result.
4. **Provider loss:** admitted route becomes unavailable; permitted qualified alternative actually executes or mission waits/blocks honestly.
5. **Quota exhaustion:** shared allowance reaches zero; subsequent admission fails without paid fallback or double reservation.
6. **Tool response-loss reconciliation:** ambiguous consequential action is reconciled by durable effect key/receipt rather than blindly repeated.
7. **Cancellation race:** cancel during active execution; later worker/model/tool completion cannot revive the mission/task or create an unauthorized effect.
8. **Knowledge authorization:** two projects contain similar material; permission filtering occurs before ranking/context and no cross-project content leaks.
9. **Knowledge supersession/deletion:** superseded/deleted fact stops appearing as current knowledge while provenance/audit remains correct.
10. **Extension incompatibility:** incompatible or unsigned/unapproved extension fails before execution and does not corrupt state.
11. **Backup/restore:** restore frozen candidate data/artifacts to a clean target and reconcile expected state/hash.
12. **Stale-site epoch:** restored/old site with stale epoch cannot accept a consequential effect or fresh worker result.
13. **Concurrency/backpressure:** run within declared worker/provider limits; admission remains atomic and backlog drains without quota bypass.
14. **Migration/upgrade/rollback:** execute the V2 install/upgrade protocol on representative persisted state; rollback/restore follows the declared safe boundary.

## 9. Release-level invariants

For V2.0 acceptance, the campaign must finish with:
- **zero** observed cross-project/authorization leaks;
- **zero** leaked credentials or private browser/session material;
- **zero** unauthorized paid/unknown-cost calls;
- **zero** duplicate accepted consequential effects;
- **zero** accepted stale-worker/stale-site results;
- **zero** mock/known-answer/fabricated-success events on operational paths;
- all mandatory drills executed with their expected result or an explicit release-blocking defect;
- every unexpected application error triaged and no known unresolved release-blocking defect in the supported V2.0 matrix;
- support matrix reduced honestly where a capability cannot satisfy its contract rather than relabeled as working.

No universal bug-free claim is made.

## 10. Evidence integrity / monitoring rules

- observation telemetry is append-only/versioned;
- preserve raw sanitized run summaries plus derived aggregates;
- bind all aggregates to input run IDs/hashes;
- do not remove outliers/failures without a documented invalid-evidence reason independent of outcome favorability;
- operator/manual interventions are recorded with timestamp and reason;
- heartbeat/liveness data is not treated as proof that useful work occurred;
- CI/offline tests are supporting evidence, not replacements for live/private drills;
- `unknown` remains unknown until directly measured.

## 11. Exit report

`ART-V20-RELEASE-REVIEW` consumes a reliability report containing:
- candidate/config manifest identities;
- exact start/end wall-clock timestamps and elapsed duration;
- monitoring-gap inventory;
- complete mission/drill inventory including failed/retried attempts;
- expected-vs-unexpected failure classification;
- unresolved defect/limitation matrix;
- duplicate-result/effect counts;
- security-boundary violation counts;
- provider/worker recovery observations;
- backup/restore RPO/RTO observations;
- resource/token/cost observations with unknowns explicit;
- support-matrix changes caused by campaign evidence;
- independent lead disposition: accept reliability artifact / changes required / blocked.

Today's engineering target may stop at an implementation-complete candidate with this protocol frozen and drills runnable. Do not call V2.0 accepted until the real observation and all other required acceptance artifacts complete.

## 12. Campaign identity and reset matrix

Every reliability attempt has a stable `campaign_id` and an immutable `campaign_manifest_sha256`. A new candidate SHA, material configuration digest, durable schema authority, admitted-route policy, worker fencing authority, knowledge-permission policy, tool/effect authority, extension trust policy or site epoch creates a **new campaign identity** unless the lead has preregistered that the field is intentionally variable for a specific drill.

Before the first counted minute, classify every change category in a reset matrix:

| Change class | Default effect on 7-day clock | Required follow-up |
|---|---|---|
| Runtime/source behavior | Full restart | New campaign manifest + all affected drills |
| Auth/project isolation/effect fencing | Full restart | Security negatives + affected drills |
| Durable schema/migration semantics | Full restart | Migration/restore + recovery drills |
| Broker/admission/qualification policy | Full restart | Route/quota/fallback drills |
| Knowledge permission/supersession logic | Full restart | Knowledge authorization/deletion drills |
| Tool/approval/receipt semantics | Full restart | Tool response-loss/cancellation/duplicate drills |
| Site epoch/backup/restore authority | Full restart | Backup/restore + stale-site drills |
| Observability-only change proven behavior-neutral | Clock may continue after lead review | Rebind telemetry version; rerun visibility check |
| Documentation-only change | No reset | Record commit and behavior-neutral rationale |
| Test-only change outside shipped runtime | No reset by default | Record test change; rerun affected offline check |

A narrower decision than the default requires a written lead decision **before** post-change reliability evidence is counted. The decision names the exact old/new SHA, why behavior is unaffected, and which evidence remains valid. This prevents retroactive preservation of a favorable clock.

Campaign time is never spliced across incompatible identities. A failed campaign remains preserved as evidence and may inform defect repair, but its elapsed time cannot be transferred to a successor campaign.

## 13. Checkpoints, gaps and campaign completion

During the 7-day campaign, publish one immutable checkpoint at least every 24 wall-clock hours and at every mandatory drill or unexpected failure. Each checkpoint binds:
- `campaign_id` and candidate/config manifest hash;
- covered UTC interval;
- service/worker availability observations;
- monitoring coverage and explicit gaps;
- missions/drills added since the prior checkpoint;
- new unexpected events/defect IDs;
- resource/provider accounting status including unknowns;
- backup age / restore verification status;
- whether the campaign is `counting`, `paused_for_unobservable_state`, `invalidated`, or `complete_candidate`.

A monitoring gap does not automatically invalidate a campaign, but a gap that makes a release invariant unobservable cannot count toward that invariant. The lead must classify the gap before final acceptance. If the gap prevents establishing continuity of a required safety property, start a successor campaign rather than estimating or backfilling the missing interval.

The seven-day clock completes only when `ended_at - started_at >= 168 hours` for one compatible campaign identity and the evidence ledger covers the required interval honestly. Scheduled-job timestamps, heartbeat cadence, CI duration, repeated short runs or manually edited dates cannot substitute for elapsed wall-clock time.

Completion of the clock only makes the reliability artifact reviewable. It does not itself accept V2.0: all required drills, zero-tolerance invariants, defect disposition, support-matrix reconciliation, security review and independent release review must still pass.
