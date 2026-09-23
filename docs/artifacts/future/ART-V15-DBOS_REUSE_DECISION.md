# ART-V15-DBOS-REUSE — durable execution/queue reuse decision

Status: drafting
Target: V1.7 milestone / V1.5 capability group
Owner: ChatGPT lead
Depends on: ART-V15-WORKER-PROTOCOL, ART-V15-LEASE-FENCING

## Decision

Use DBOS as an OPTIONAL/recommended durable execution and queue transport layer where it reduces custom scheduling/recovery code, while keeping SwarmAI's own control-plane task/lease/generation/cancellation/result-acceptance records authoritative.

Do not make DBOS workflow completion equivalent to SwarmAI result acceptance.

## Why reuse DBOS

Current DBOS Python supports:
- durable workflows that recover after process interruption;
- persistent queues backed by its system database;
- worker/global concurrency;
- partition concurrency/rate limits;
- queue-worker services separated from the web/control service;
- workflow IDs usable as execution idempotency keys.

This matches several mechanics SwarmAI would otherwise rebuild.

## Boundary

DBOS MAY own:
- durable execution of a worker attempt;
- queue persistence/polling;
- worker-process concurrency/rate limiting;
- workflow recovery from completed DBOS steps;
- execution handle/status.

SwarmAI MUST still own:
- project/tenant authorization;
- task graph/dependency state;
- task revision/input/source digests;
- worker registration/generation/trust;
- lease issuance/expiry/cancellation generation;
- provider/tool reservations;
- acceptance fences;
- accepted effect/result idempotency;
- stale-result rejection;
- evidence/artifact acceptance.

A DBOS workflow with status success is merely a completed attempt until SwarmAI acceptance succeeds.

## Integration pattern

1. SwarmAI transaction creates attempt + lease.
2. Enqueue DBOS workflow using a deterministic execution ID derived from attempt ID.
3. DBOS worker executes the attempt.
4. Workflow submits immutable result envelope to SwarmAI.
5. SwarmAI acceptance transaction applies all fences.
6. DBOS status and SwarmAI result state remain separately inspectable.

## Queue partitions

Potential partitions:
- project_id for fairness/isolation;
- capability/trust class for heterogeneous workers;
- local-vs-browser-vs-GPU worker classes.

Do not use a partition key as authorization; it is scheduling metadata only.

## Risks

- DBOS global concurrency may count pending workflows; configure carefully.
- Queue settings are database state and startup registration can update them; use explicit conflict policy and config/version evidence.
- DBOS executor/process identity is not SwarmAI worker identity.
- DBOS cancellation boundaries do not replace SwarmAI cancellation generation/effect fences.
- DBOS system tables do not remove need for product-schema backups/recovery manifests.

## Session A spike packet

V2A-003X / SP2:
- confirm actual installed DBOS version/API from lockfile;
- create a small isolated proof with queue worker + restart;
- prove attempt ID maps to one durable workflow;
- prove SwarmAI stale-generation acceptance still rejects an otherwise successful DBOS workflow result;
- compare code/operational complexity against custom polling.

If spike is clean, use DBOS queue execution behind the ART-V15 worker protocol. If not, retain the SwarmAI DB repository/poll implementation. Do not redesign acceptance semantics either way.

## Sources reviewed 2026-09-20

Official DBOS Python docs: durable workflows, queues, queue-worker service, concurrency/partition/rate-limit controls.
