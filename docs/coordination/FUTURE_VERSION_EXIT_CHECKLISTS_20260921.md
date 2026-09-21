# SwarmAI future version exit checklists

Date: 2026-09-21
Status: PLANNING ONLY

These checklists distinguish implementation-complete from accepted.

## Mandatory claim checks at every exit

The generated packet catalog gives per-packet proof; master-plan section 0.2 defines the final private operator deliverable. Check implementation, operational wiring, live-local, real-world, independent review, external and elapsed states separately. A passing plan validator is not product evidence.

- V1.7: R17b/c durable operational path, R27d approval integrity, R28s real isolation, R25b knowledge/quality disposition, CP5 local and R33c-2 real external proof, CP6 identity crosswalk. Browser-specific registry requirements cannot be replaced by GitHub proof without explicit independent disposition.
- V1.8: actual outage/restore and externally verified old-site fencing, not merely incrementing a restored epoch.
- V1.9: real fresh install and own-runtime selfdev; supported OS only with actual environment evidence.
- V2.0: exact supported frozen candidate, real 168h observation and lower required artifact disposition; no implied publish/merge.
- V2.3: actual distinct nodes and non-fixture external resource under constrained capacity; pack/portability/operator readback.
- V3: all objective/learning/allocation/selfdev/ecosystem/tenancy artifacts, real elapsed trigger->mission->external effect and canary/rollback; full private runbook and independent review. A failed learning proposal is evidence, not promotion.

An external-pending row permits independent implementation, but never turns its required acceptance checkbox into a pass. Source support reductions/waivers require explicit versioned governance, not an executor's convenience.

## V1.8 implementation-complete

- [ ] SiteAuthority/SiteEpoch durable state exists.
- [ ] Dispatch is epoch-bound.
- [ ] Result acceptance is epoch-bound.
- [ ] Consequential effect acceptance is epoch-bound.
- [ ] Deployment manifest exists and is redacted.
- [ ] Backup manifest/integrity exists.
- [ ] Restore/reconciliation workflow exists.
- [ ] Split-brain negatives pass.
- [ ] Outage drill harness exists.
- [ ] Live outage/restore evidence is either completed or honestly pending.

Accepted only when every required V1.8 artifact reaches canonical accepted state.

## V1.9 implementation-complete

- [ ] Extension manifest/lifecycle exists.
- [ ] Project-scoped extension grant enforced.
- [ ] Extension cannot bypass broker/ToolGateway.
- [ ] Clean install process exists.
- [ ] Upgrade/migration process exists.
- [ ] Rollback process exists.
- [ ] Support bundle redacts secrets.
- [ ] Selfdev path creates isolated PR candidate.
- [ ] Selfdev cannot self-merge/release.
- [ ] Fresh/external install evidence completed or honestly pending.

## V2.0 implementation-complete candidate

- [ ] lower-version implementation source integrated;
- [ ] all migrations have one reviewed head;
- [ ] CandidateManifest frozen;
- [ ] configured deterministic CI green;
- [ ] support matrix evidence-grounded;
- [ ] install journey executable;
- [ ] upgrade/rollback executable;
- [ ] security review mapped to candidate;
- [ ] performance baseline executable/completed;
- [ ] reliability protocol frozen;
- [ ] required wall-clock campaign started/completed/pending honestly.

Accepted V2.0 additionally requires required elapsed/live evidence + independent release review.

## V2.3 implementation-complete

- [ ] scheduler state durable;
- [ ] project-level fairness defined;
- [ ] aging/priority deterministic;
- [ ] reservation intent is transactional/fail-closed;
- [ ] provider/worker/tool capacity integrated;
- [ ] backpressure bounded;
- [ ] cancellation/drain fenced;
- [ ] scheduler bound to SiteEpoch;
- [ ] decision receipts emitted;
- [ ] capability packs lifecycle complete;
- [ ] portability export/import complete;
- [ ] observability read surface complete;
- [ ] dashboard mutation uses action boundary;
- [ ] fleet placement/trust/locality complete;
- [ ] pathological deterministic suite passes;
- [ ] multi-process/private evidence complete or honestly pending.

## V3.0 implementation-complete

### Objectives
- [ ] immutable objective/version;
- [ ] trigger policies;
- [ ] dedupe;
- [ ] rate/max-active;
- [ ] pause/revoke/expiry;
- [ ] stop conditions;
- [ ] MissionProposal;
- [ ] normal mission admission bridge;
- [ ] authority intersection.

### Learning
- [ ] LearningProposal immutable versions;
- [ ] state machine enforced by software;
- [ ] calibration/held-out separation;
- [ ] candidate/protocol freeze;
- [ ] independent review;
- [ ] canary;
- [ ] deterministic rollback;
- [ ] drift/revalidation;
- [ ] contamination terminal state.

### Allocation/selfdev/ecosystem/fleet
- [ ] resource allocator uses V2.3 scheduler;
- [ ] fairness/privacy/quota/cost preserved;
- [ ] selfdev uses learning governance;
- [ ] selfdev cannot self-govern/self-merge;
- [ ] capability trust/signature/revocation;
- [ ] tenant-aware fleet/audit;
- [ ] cross-tenant negatives.

### Integrated evidence
- [ ] real schedule/event objective evidence;
- [ ] duplicate trigger evidence;
- [ ] canary rollback evidence;
- [ ] governed learning scenarios;
- [ ] multi-project allocation evidence;
- [ ] controlled selfdev evidence;
- [ ] independent security/governance review.

Public release remains a separate operator decision.
