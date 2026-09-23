# ART-V15-DURABLE-SCHEMA-DELTA — extend existing DB, do not duplicate it

Status: accepted lead design
Target: V1.7 milestone / V1.5 capability group
Owner: ChatGPT lead
Depends on: ART-V15-LEASE-FENCING, ART-V15-WORKER-PROTOCOL

## Existing schema to reuse

Current `src/swarm/db/models.py` already contains:
- MissionRow
- TaskRow
- TaskAttemptRow
- WorkerLeaseRow
- ReservationRow
- AttemptReceiptRow
- ApprovalRow
- EventRow
- OutboxRow
- provider/route/quota/capability tables

Therefore V1.5 implementation MUST extend/reuse this schema. Do not create a second task-attempt system, second outbox, or second worker identity table unless a migration ADR proves necessary.

## Existing naming caveat

`WorkerLeaseRow` currently behaves more like a **worker registration/current generation row**:
- primary key = worker_id
- node identity / runtime / capacity
- generation / heartbeat / status
- labels/capabilities

It is not a per-task lease.

For the current acceleration tranche, avoid a risky rename solely for aesthetics. Treat the existing table as the durable worker-state row and add a new per-attempt lease table.

A later migration may rename the table only if the compatibility benefit outweighs migration risk.

## Delta A — extend existing WorkerLeaseRow

Add:
- project_id: String(64), indexed, non-null for operational rows
- trust_class: String(32)
- token_hash: String(128), nullable only for migrated/non-auth legacy rows
- token_id: String(64) or opaque public identifier
- registered_at
- updated_at
- drain_requested_at nullable
- revoked_at nullable
- policy_version
- software_version/build_sha
- privacy_classes JSONB
- resource_payload JSONB

Never persist raw membership token.

Recommended unique/index:
- index(project_id, status)
- optional unique token_hash if one token maps to one current registration

## Delta B — extend TaskAttemptRow

Existing TaskAttemptRow is authoritative attempt identity. Add:
- project_id (denormalized for authorization/query safety)
- mission_id (denormalized/indexed)
- task_revision
- input_digest
- source_revision
- cancellation_generation
- accepted_result_id nullable
- created_at if not already represented by started_at semantics
- terminal_at or reuse completed_at

Do not create a second attempt table.

## Delta C — new TaskLeaseRow

New table: `task_leases`

Fields:
- lease_id PK
- attempt_id FK -> task_attempts.attempt_id
- task_id FK -> tasks.id
- mission_id FK -> missions.id
- project_id index
- worker_id
- worker_generation
- task_revision
- input_digest
- source_revision
- cancellation_generation
- state: active|renewed|expired|released|cancelled
- issued_at
- expires_at
- renewable_until
- reservation_refs JSONB
- effect_scope
- policy_version
- updated_at

Constraints:
- at most one active lease per attempt;
- lease ID immutable;
- no result acceptance from a non-current lease unless a versioned explicit race-resolution policy says otherwise.

PostgreSQL partial unique index is preferred if supported cleanly:
unique active attempt where state in ('active','renewed').

If migration tooling makes that brittle, enforce with SELECT ... FOR UPDATE transaction + ordinary indexed state and prove race behavior in integration tests.

## Delta D — new WorkerResultRow

New table: `worker_results`

Fields:
- result_id PK
- attempt_id index/FK
- lease_id index/FK
- task_id / mission_id / project_id
- worker_id / worker_generation
- task_revision
- input_digest
- source_revision
- result_status
- artifact_manifest JSONB
- checks JSONB
- usage JSONB
- effect_receipts JSONB
- submitted_at
- acceptance_state: submitted|accepted|rejected_stale|rejected_policy|rejected_validation|rejected_duplicate|rejected_cancelled
- rejection_reason nullable
- accepted_at nullable

Result rows are immutable except acceptance disposition metadata.

## Delta E — use existing OutboxRow for DBOS/worker execution publication

Current OutboxRow already has:
- stable_workflow_id unique
- aggregate type/id
- event type
- payload
- status/attempts/error
- timestamps

Use it as the transaction boundary:
1. transaction creates/updates attempt + TaskLeaseRow;
2. same transaction inserts outbox event with stable workflow ID derived from attempt ID;
3. publisher enqueues DBOS/custom worker workflow;
4. outbox becomes published only after enqueue acknowledgement;
5. duplicate publish uses stable workflow ID/idempotency and does not create duplicate SwarmAI attempts.

Do not enqueue the distributed workflow before the lease transaction commits.

## Atomic claim transaction

Pseudo-sequence:

1. SELECT eligible task FOR UPDATE SKIP LOCKED (or equivalent safe pattern).
2. verify current task/mission/cancellation/source state.
3. verify worker registration/generation/project/trust/capability.
4. create TaskAttemptRow.
5. create TaskLeaseRow.
6. reserve local product-side capacity/effect metadata required before dispatch.
7. create OutboxRow.
8. COMMIT.
9. asynchronous publisher enqueues attempt execution.

If no eligible task exists, transaction does not mutate queue/task state.

## Acceptance transaction

1. lock result + attempt + current lease/task/mission rows.
2. verify project.
3. verify lease/worker generation.
4. verify task revision/input/source/cancellation.
5. verify task/mission not already accepted/cancelled incompatibly.
6. verify required reservation/effect reconciliation.
7. run/verify acceptance receipt/reviewer decision.
8. atomically:
   - set result accepted;
   - set attempt accepted_result_id/status;
   - update task terminal state;
   - emit event/outbox.
9. stale/duplicate invalid result is retained with explicit rejected disposition.

## Migration compatibility

Migration must preserve current rows.

For new non-null fields:
- add nullable;
- backfill from related Task/Mission or explicit legacy sentinel only when semantics are safe;
- validate;
- then enforce non-null for new operational paths where appropriate.

Do not fabricate project ownership during backfill. Unknown legacy ownership remains quarantined/unavailable until reconciled.

## Tests Session A must include

V2A-003a:
- migration up on empty DB;
- migration up with representative legacy rows;
- raw membership token absent from stored worker row;
- existing TaskAttemptRow API remains usable.

V2A-003b:
- two claim transactions race, exactly one wins task/attempt lease;
- incompatible task does not head-of-line block eligible task;
- lease renew/expire persistence survives new session/process.

V2A-003c:
- stale generation result rejected;
- expired/reassigned lease result rejected;
- cancellation generation race deterministic;
- changed source/input revision rejected;
- duplicate submission idempotent;
- only one accepted_result_id.

V2A-003X:
- if DBOS used, outbox stable_workflow_id prevents duplicate workflow execution publication while SwarmAI acceptance fence remains independently testable.

## Additional hardening discovered

Current `src/swarm/db/engine.py` and `alembic.ini` contain a known default `swarm:swarm` DSN. V2A-H6A must remove unsafe operational reliance on that default. Tests may use explicit fixture DSNs; normal runtime must require/generated-configure a secret-backed DSN.
