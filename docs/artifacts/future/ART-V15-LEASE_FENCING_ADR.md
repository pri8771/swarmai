# ART-V15-LEASE-FENCING — durable worker/lease/result ADR

Status: drafting
Target: V1.7 milestone / V1.5 capability group
Owner: ChatGPT lead
Implements: ART-V15-WORKER-PROTOCOL

## Decision

Use the existing PostgreSQL + SQLAlchemy + Alembic stack as the first authoritative durable store for worker registrations, leases, attempts and result acceptance.

Do not add Kubernetes, Redis, or a second workflow database merely to implement V1.5.

DBOS remains an optional execution helper; it is not the authority for lease/fencing semantics unless a later ADR proves a concrete benefit.

## Required durable tables

### workers
- worker_id primary key
- project_id
- generation
- status
- trust_class
- capabilities_json
- resource_json
- software_version
- policy_version
- registered_at
- last_heartbeat_at
- drain_requested_at
- revoked_at

### task_attempts
- attempt_id primary key
- mission_id / task_id / project_id
- task_revision
- input_digest
- source_revision
- status
- created_at / terminal_at
- accepted_result_id nullable

### worker_leases
- lease_id primary key
- attempt_id unique active relation
- worker_id / worker_generation
- task_revision
- cancellation_generation
- issued_at / expires_at / renewable_until
- state
- reservation_refs_json
- effect_scope

### worker_results
- result_id primary key
- attempt_id / lease_id
- worker_id / worker_generation
- task_revision
- input_digest / source_revision
- result_status
- artifact_manifest_json
- checks_json
- usage_json
- effect_receipts_json
- submitted_at
- acceptance_state
- rejection_reason

## Atomic claim

Task claim must be a database transaction/CAS:
1. verify task is schedulable;
2. verify no live accepted/active attempt conflicts;
3. create new attempt;
4. create lease tied to worker generation and current task/source/cancellation revisions;
5. commit before returning work.

Two workers racing must produce exactly one winning active lease.

## Acceptance transaction

Result acceptance atomically proves:
- project ownership;
- active/current lease;
- generation match;
- task/source/input revisions;
- cancellation generation;
- required reservations reconciled;
- validation/review passes;
- no accepted result/effect already exists.

Then set attempt accepted + accepted_result_id. All stale/duplicate results remain durable non-accepted records.

## Restart behavior

On control-plane restart:
- rebuild active workers/leases from DB;
- expire leases only by server-side timestamps/policy;
- never infer ownership from local process memory;
- do not release a consequential effect merely because a worker heartbeat is missing.

## Implementation packets

Session A:
- V2A-003a SP2: migrations/models/repository layer.
- V2A-003b SP2: atomic claim/renew/expire API.
- V2A-003c SP2: result submission + acceptance fence.
- V2A-003d SP2: restart/race/stale-result tests.

Acceptance evidence:
- two claimers race: one lease;
- restart preserves lease;
- expired lease reassigns;
- old result rejected;
- cancellation/source revision fences;
- duplicate result idempotent;
- two projects isolated.
