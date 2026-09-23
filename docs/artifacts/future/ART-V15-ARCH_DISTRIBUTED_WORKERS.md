# ART-V15-ARCH — Distributed worker architecture

Status: drafting
Target: V1.5
Owner: ChatGPT lead
Purpose: architecture artifact usable before implementation begins.

## Goal

Allow SwarmAI missions to execute eligible work across multiple independent hosts while preserving exactly-once accepted effects, durable progress, bounded resource admission, project isolation and recoverability.

## Architectural split

### Control plane
Authoritative durable state:
- mission/task graph;
- worker registrations;
- worker leases and generations;
- resource reservations;
- result acceptance/fencing;
- cancellation state;
- artifact pointers;
- audit/event log.

### Worker plane
Each worker host:
- registers capabilities/resources/trust class;
- receives only authorized work;
- holds a time-bounded lease;
- heartbeats independently;
- executes inside the permitted local sandbox/tool boundary;
- submits immutable attempt/result envelopes;
- never decides final acceptance of its own stale attempt.

### Artifact plane
Large outputs do not travel inside control messages. Workers upload immutable/versioned artifacts and submit hashes/refs.

## Core contracts

Worker identity:
- worker_id;
- host alias;
- project/tenant scope;
- capability set;
- trust class;
- resource envelope;
- generation;
- registration timestamp;
- last heartbeat;
- draining flag.

Lease:
- lease_id;
- task_id;
- worker_id;
- generation;
- acquired_at;
- expires_at;
- attempt_id;
- reservation refs.

Result:
- attempt_id;
- task_id;
- lease_id;
- worker generation;
- source/input version;
- artifact refs/hashes;
- deterministic checks;
- model/tool usage;
- completion timestamp.

## Fencing rule

A result is eligible for acceptance only when:
- its lease is still the active lease for that task/attempt;
- worker generation matches;
- task was not cancelled before the result boundary;
- input/source version still matches;
- no already-accepted result exists;
- required evidence/permission checks pass.

Late results remain auditable but cannot create accepted effects.

## Failure handling

Worker lost:
1. heartbeat expires;
2. active leases move to expired;
3. reservations reconcile;
4. task becomes schedulable after bounded delay;
5. a new worker receives a new lease/generation;
6. old worker result is fenced if it later returns.

Control-plane restart:
- reconstruct schedulable state only from durable records;
- never infer active lease merely from worker process existence.

Network partition:
- worker may finish computation but cannot claim acceptance locally;
- central acceptance/fencing decides after reconnection.

## Multi-host minimum V1.5 proof

Use at least two actual hosts.
- both register independently;
- adding host increases eligible capacity;
- drain/remove one host and observe capacity reduction;
- kill one executing worker;
- reassign same task from persisted state;
- demonstrate stale result rejection;
- run two missions sharing one quota pool without double allocation;
- preserve project/trust boundaries.

## Technology preference

Reuse proven durable storage/queue primitives already present in SwarmAI before adding distributed infrastructure. Avoid introducing Kubernetes solely for V1.5. Start with a control-plane database + explicit worker RPC/poll/queue contract that can run on the user's current Mac/Windows/Unraid nodes.

Transport is replaceable; the durable lease/fencing contract is not.

## Security

- workers receive scoped credentials/references, not control-plane master secrets;
- registration does not imply access to every project;
- browser/session-capable workers are a higher trust class;
- artifacts are authorized before retrieval;
- worker-provided provider endpoints are not automatically trusted/routable.

## Open design questions for implementation artifact

- push vs pull worker dispatch;
- exact durable queue library;
- artifact store for multi-host use;
- clock-skew tolerance;
- lease default/renewal timing by task family;
- Windows/macOS/Linux sandbox parity.

These should be resolved as ADRs before the corresponding code packet, not inside one giant implementation task.
