# ART-V15-WORKER-PROTOCOL — distributed worker enrollment, leasing and result protocol

Status: drafting  
Target: V1.5  
Owner: ChatGPT lead  
Depends on: `ART-V15-ARCH`  
Scope: future architecture/interface contract only. **No V1.5 implementation is authorized by this artifact.**

## Objective

Define a transport-independent contract that lets an authorized host join SwarmAI, advertise bounded capability, obtain a durable task lease, heartbeat/renew it, return immutable attempt evidence and drain safely without creating duplicate accepted effects.

The protocol deliberately separates:

1. **registration** — who/what the worker is allowed to claim;
2. **admission** — whether this worker may run this task now;
3. **lease ownership** — the temporary right to execute one attempt;
4. **result submission** — an immutable claim about work performed;
5. **result acceptance** — authoritative control-plane decision, never worker self-acceptance.

Transport may later be HTTP polling, a durable queue, DBOS-backed workflow or another approved mechanism. These state transitions and fencing fields remain stable regardless of transport.

## Worker lifecycle state machine

`unregistered -> active -> draining -> offline`

Additional control state: `quarantined`.

### `unregistered`

No work may be leased. A discovered host or process is not a worker until registration is accepted.

### `active`

May request/receive eligible leases within its declared project/trust/capability/resource envelope.

### `draining`

No new lease may be created. Existing leases may complete until their deadline or be explicitly cancelled/released. Drain completion transitions to `offline`.

### `offline`

No new work. Existing unexpired leases are reconciled according to lease policy; offline status alone does not immediately make an old lease safe to duplicate.

### `quarantined`

No new leases. Existing result submissions are retained for audit but require explicit control-plane disposition. Use for trust violation, repeated protocol mismatch, stale software/config, invalid artifact hashes or suspicious endpoint/capability claims.

## Registration request

Required fields:

```json
{
  "protocol_version": "1.x",
  "worker_nonce": "client-generated-random-id",
  "host_alias": "opaque-operator-safe-alias",
  "software": {
    "swarm_version": "...",
    "worker_build_sha": "...",
    "protocol_schema_version": "..."
  },
  "scopes_requested": ["project:..."],
  "capabilities": ["repo_read", "local_command"],
  "trust_class": "compute_only|code_write|browser_session|operator_local",
  "resources": {
    "worker_slots": 1,
    "local_inference_slots": 0,
    "memory_mb": null,
    "gpu_classes": [],
    "named_local_routes": []
  },
  "artifact_transport": {
    "schemes": ["control_upload"],
    "max_inline_bytes": 65536
  }
}
```

Forbidden registration content:
- raw provider API keys;
- browser cookies/session storage;
- passwords/MFA/recovery material;
- project data used merely to prove identity;
- arbitrary worker-supplied provider endpoint treated as trusted by default.

## Registration response

```json
{
  "worker_id": "wrk_...",
  "generation": 1,
  "membership_token_ref": "secret-returned-once-or-secure-reference",
  "scopes_granted": ["project:..."],
  "capabilities_granted": ["repo_read", "local_command"],
  "trust_class": "compute_only",
  "heartbeat_interval_seconds": 30,
  "lease_defaults": {
    "duration_seconds": 120,
    "renew_after_seconds": 45,
    "max_total_lease_seconds": 1800
  },
  "server_protocol_version": "1.x",
  "policy_version": "..."
}
```

The control plane may grant a strict subset of requested scope/capability. A registration response must never silently broaden authority.

## Generation semantics

`generation` is a monotonically increasing fencing number for a worker identity.

Increase generation when:
- worker is explicitly re-enrolled after credentials/session reset;
- host identity is deliberately rebound;
- control plane invalidates all prior worker leases/results for that identity.

A result from generation N is not eligible for acceptance after generation N+1 becomes authoritative, even if its old lease ID still exists in logs.

Routine process restart need not increase generation if the control plane can prove the same enrollment identity and no invalidation occurred; implementation must document this decision explicitly.

## Heartbeat envelope

```json
{
  "worker_id": "wrk_...",
  "generation": 1,
  "observed_at": "RFC3339",
  "worker_state": "active|draining",
  "active_lease_ids": ["lease_..."],
  "available": {
    "worker_slots": 1,
    "local_inference_slots": 0
  },
  "health": {
    "executor": "ready|degraded|blocked",
    "artifact_transport": "ready|degraded|blocked"
  },
  "capability_changes": []
}
```

Heartbeat is not a claim that work succeeded. The server records receipt time independently; worker-provided clock is evidence only.

## Lease request / dispatch

A worker may poll for eligible work or receive a pushed offer, but the **lease becomes real only after a durable compare-and-set in the control plane**.

Eligibility must check before lease creation:
- worker active and generation current;
- project/tenant scope;
- task required capabilities and trust class;
- data/privacy scopes;
- graph/dependency readiness;
- cancellation state;
- worker slot/resource capacity;
- model/provider/tool reservations needed by the task;
- no active mutually exclusive lease/effect lock;
- task input/source/config version still current.

## Lease record

```json
{
  "lease_id": "lease_...",
  "task_id": "tsk_...",
  "mission_id": "mission_...",
  "project_id": "proj_...",
  "attempt_id": "attempt_...",
  "worker_id": "wrk_...",
  "worker_generation": 1,
  "task_revision": 4,
  "input_digest": "sha256:...",
  "source_revision": "...",
  "policy_version": "...",
  "reservation_refs": ["resv_..."],
  "issued_at": "RFC3339",
  "expires_at": "RFC3339",
  "renewable_until": "RFC3339",
  "cancellation_generation": 0,
  "effect_scope": "none|read_only|idempotent|approval_bound"
}
```

The worker must treat the lease as immutable. Any changed input, source revision, policy, required tool permission or acceptance contract requires a new task revision/attempt/lease.

## Lease renewal

Renewal request includes:
- lease ID;
- worker ID/generation;
- last known task revision;
- progress class (`running`, `waiting_local_tool`, `waiting_artifact_upload`);
- bounded requested extension;
- current reservation state refs.

Renewal is denied if:
- task/mission cancelled;
- worker generation stale;
- task revision/input digest changed;
- policy revoked relevant authority;
- accepted result already exists;
- max total lease duration reached;
- required reservation is no longer valid.

A denied renewal means **stop producing new effects**. Computation already completed may be submitted as a fenced/late result for audit, but the worker cannot assume it is acceptable.

## Lease expiry and reassignment

Expiry sequence:

1. lease passes server-side expiry without valid renewal;
2. lease state becomes `expired` durably;
3. resource reservations are reconciled/released according to their own provider/tool semantics;
4. task becomes retryable only if cancellation/attempt policy permits;
5. new attempt receives a new attempt ID and lease ID;
6. prior result submissions remain auditable but fail the active-lease fence.

Do not reassign solely because one heartbeat was delayed if the lease itself is still valid.

## Result submission envelope

```json
{
  "protocol_version": "1.x",
  "attempt_id": "attempt_...",
  "lease_id": "lease_...",
  "task_id": "tsk_...",
  "mission_id": "mission_...",
  "project_id": "proj_...",
  "worker_id": "wrk_...",
  "worker_generation": 1,
  "task_revision": 4,
  "input_digest": "sha256:...",
  "source_revision": "...",
  "started_at": "RFC3339",
  "finished_at": "RFC3339",
  "status": "succeeded|failed|cancelled|blocked",
  "summary": "bounded non-secret summary",
  "artifact_refs": [
    {"artifact_id": "...", "sha256": "...", "size_bytes": 0, "media_type": "..."}
  ],
  "checks": {},
  "usage": {
    "model_attempt_refs": [],
    "tool_attempt_refs": [],
    "reservation_refs": []
  },
  "side_effect_receipts": [],
  "error": null
}
```

Large outputs stay in the artifact plane. Inline response content is bounded and scrubbed.

## Acceptance fence

A result may transition to `accepted` only through an atomic control-plane operation that proves all of:

1. result project matches task/mission project;
2. worker ID/generation match the active lease;
3. lease/attempt is still the task's eligible attempt or is explicitly permitted by a deterministic race-resolution rule;
4. task revision/input/source/config hashes match current acceptance target;
5. task was not cancelled before the relevant result/effect boundary;
6. required reservations/usage reconciliation is complete or explicitly pending in a non-accepting state;
7. required deterministic/independent review checks pass;
8. artifact hashes/authorization are valid;
9. no accepted result/effect already exists for the same acceptance/effect key;
10. any consequential action receipts match an approved idempotency/effect scope.

If any fence fails, store result as `rejected_stale`, `rejected_policy`, `rejected_duplicate`, `rejected_validation` or another explicit non-accepted terminal status. Never discard silently.

## Exactly-once accepted effect model

SwarmAI cannot guarantee an external service executed a side effect exactly once unless that service exposes compatible idempotency/transaction semantics. The product guarantee is narrower and testable:

- **at most one SwarmAI accepted effect receipt per effect key**;
- worker must use the approved idempotency/effect key when the tool supports it;
- retries do not generate a fresh effect key for the same intended effect;
- if external outcome is uncertain after network failure, task moves to reconciliation, not blind retry;
- a stale worker can never promote its own external action to accepted state.

## Drain protocol

1. control plane marks worker `draining`;
2. no new leases;
3. worker reports current leases/effects;
4. safe read/compute leases may finish within configured deadline;
5. policy may cancel/reassign specific leases;
6. outstanding uncertain side effects are reconciled;
7. worker transitions offline only after leases are terminal/released or operator forces quarantine/offline with explicit residual state.

## Cancellation protocol

Mission/task cancellation increments the durable cancellation generation before worker notification. A worker heartbeat/result carrying an older cancellation generation is fenced. Cancellation notification is advisory for speed; durable generation is authoritative.

## Capability changes

Workers cannot expand their own authority by heartbeat. New capabilities/trust/scopes require a control-plane policy decision and normally a new registration generation. Workers may voluntarily reduce available capacity/capabilities immediately.

## Compatibility/versioning

- additive optional fields: minor protocol revision;
- changed required semantics/fencing: major protocol revision;
- control plane declares supported range;
- unsupported worker protocol is denied enrollment, not best-effort interpreted;
- task/result artifacts record exact protocol/policy/schema versions.

## Minimum negative test matrix for future implementation

- two workers race for same task: only one durable lease wins;
- stale generation submits result: retained, never accepted;
- old lease result arrives after reassignment: retained, never accepted;
- cancellation races completion: deterministic boundary enforced;
- input revision changes mid-lease: old result fenced;
- worker lies about capability: admission rejects or quarantine follows validation failure;
- duplicate result submit: idempotent receipt, no duplicate acceptance;
- external action response lost: reconciliation, no blind repeat;
- drain during work: no new lease and deterministic existing-lease disposition;
- control-plane restart: durable leases reconstruct without relying on worker process memory;
- two projects: worker/project scopes cannot cross;
- provider reservation expires while task continues: model/tool call cannot bypass broker admission.

## Open ADRs derived from this protocol

1. **ART-V15-ADR-DISPATCH:** pull/long-poll versus queue/push transport.
2. **ART-V15-ADR-DURABILITY:** DBOS/PostgreSQL versus another existing durable primitive for lease CAS/state transitions.
3. **ART-V15-ADR-ARTIFACT-STORE:** local/shared object storage interface and authorization.
4. **ART-V15-ADR-LEASE-TIMING:** default durations/renewal strategy by task family, including clock-skew tolerance.

These are lead design artifacts. They must not trigger V1.5 source implementation until the owner authorizes that tranche.
