# ART-V20-RELIABILITY-PROTOCOL — integrated V2 observation plan

Status: drafting
Target: V2.0
Owner: ChatGPT lead

## Candidate freeze

Before time-bound observation:
- exact integration SHA;
- schema/migration revision;
- dependency lock;
- provider route/admission versions;
- model qualification profile;
- extension manifests;
- worker protocol version;
- knowledge/tool/recovery policy versions;
- support matrix.

Material runtime/security/routing changes restart affected observation evidence.

## Metrics

For each supported mission/journey:
- attempted/completed/accepted/failed;
- expected denial vs unexpected exception;
- wall time;
- model/tool attempts and retries;
- inference tokens/usage/cost or unknown;
- worker lease churn;
- provider fallback;
- knowledge retrieval token cost;
- tool effects/reconciliation;
- artifact counts;
- restart/recovery events.

Global:
- unexpected application exception count;
- duplicate accepted effect count;
- cross-project violation count;
- secret leakage count;
- unapproved spend count;
- stuck mission/lease count;
- stale result accepted count.

Targets for accepted candidate:
- zero cross-project violations;
- zero secret leaks;
- zero unapproved charges;
- zero duplicate accepted consequential effects;
- zero stale worker/site results accepted;
- zero known unresolved defects in declared supported workflows;
- unexpected app errors triaged/fixed/rerun before acceptance.

## Fault drills

During observation include:
- provider route unavailable;
- worker process killed;
- control-plane restart;
- lease expiry/reassignment;
- knowledge item superseded/deleted;
- approval expires/changes;
- extension disabled/incompatible;
- backup/restore recovery drill.

## Observation truth

Implementation-complete V2.0 may exist before this wall-clock protocol finishes.

Never backdate, compress or infer elapsed stability from unit tests.

The exact accepted duration is an owner/lead release artifact and should be frozen before final observation begins; until then report implementation candidate, not accepted stable release.
