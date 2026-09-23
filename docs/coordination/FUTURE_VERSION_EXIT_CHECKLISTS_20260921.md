# SwarmAI future version exit checklists

Date: 2026-09-21
Status: PLANNING ONLY

These checklists distinguish implementation-complete from accepted.

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
