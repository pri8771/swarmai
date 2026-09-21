# ART-V20-RELIABILITY-PROTOCOL — integrated reliability observation

Status: drafting
Target: V2.0
Owner: ChatGPT lead

## Candidate freeze

Before reliability evidence counts:
- exact integration SHA;
- migration head;
- config/policy versions;
- route/qualification profile versions;
- extension manifests;
- knowledge schema/version;
- worker protocol version;
- site epoch/recovery version;
- supported-capability matrix.

Material runtime/security/routing changes restart affected observation evidence.

## Metrics

Per supported mission:
- final accepted/failed/blocked status;
- unexpected application exceptions;
- latency;
- model calls/tokens/cost or explicit unknown;
- retries/repair rounds;
- worker leases/reassignments;
- provider reservation/fallback;
- tool action/unknown/reconciliation;
- artifact integrity;
- knowledge retrieval counts/tokens/provenance;
- cancellation behavior.

System:
- control-plane restarts;
- worker heartbeat/lease expiry;
- DB/migration failures;
- queue backlog/age;
- duplicate accepted result/effect count;
- cross-project denial failures;
- stale-site rejection;
- backup age/RPO;
- resource use.

## Failure classification

Expected handled:
- unsupported task;
- quota exhaustion;
- denied permission;
- explicit cancellation;
- unqualified/unavailable route;
- intentionally injected worker/provider outage.

Unexpected:
- unhandled exception on supported path;
- data/authorization leak;
- duplicate accepted consequential effect;
- lost accepted mission/artifact without declared recovery limitation;
- false success/readiness;
- process deadlock requiring undocumented intervention.

## Required drills

- API/control restart with durable mission reopen;
- worker kill/reassignment/stale result;
- provider route loss/fallback or honest wait;
- tool response-loss reconciliation;
- backup/restore to clean target;
- stale-site/epoch rejection;
- knowledge deletion/supersession;
- extension incompatibility/disable;
- concurrency/backpressure under declared limits.

## Observation duration

The owner wants implementation speed, but elapsed reliability windows remain real time.

Use the existing roadmap's intended deployment observation as the final V2 acceptance window unless a later explicit owner/lead protocol changes it before the run. Do not post-hoc shorten after seeing results.

Today's target may be an implementation-complete candidate with this protocol frozen and drills runnable.

## Exit report

- candidate/config identities;
- start/end wall-clock;
- mission/drill inventory including failures/retries;
- unexpected-error inventory;
- known limitations;
- duplicate-effect count;
- security boundary violations;
- RPO/RTO observations;
- resource/cost observations;
- support-matrix changes.

No universal bug-free claim.
