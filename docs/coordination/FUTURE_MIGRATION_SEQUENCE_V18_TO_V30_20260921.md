# SwarmAI future migration sequence — V1.8 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY

Purpose: pre-plan durable table/schema order so future packets do not fight migration ownership.

Workers must inspect current migrations first and choose actual revision IDs at implementation time.

## General rules

- one linear reviewed migration sequence on the integration branch;
- no two future packets independently create conflicting heads;
- schema migration and repository code land together;
- destructive column/table removal is deferred until compatibility window is explicitly closed;
- new authority/fencing fields default fail-closed where possible;
- backfill must be deterministic and auditable;
- migrations never fabricate historical evidence.

## Current chain and the V1.7 remainder (audited at `f2b8d5f`)

Linear chain, one head: `9eb193b10f4e` (p02 initial) → `a15lease003a0001` (V1.5 lease fencing) → `a16know003a0001` (V1.6 knowledge) → `a17effect004a0001` (V1.7 approvals + `action_effects`).

| Order | Revision | Packet | Content |
|---|---|---|---|
| M17-02 | `a17effect004b0001` | R27a | `action_receipts` (immutable, `UNIQUE(effect_id, attempt_number)`); `action_effects` + `state_reason`, `attempt_count`, `executor_id`, `approval_consumed_at` |

That is the only migration V1.7 still needs. R27b–R34b add none; R31b stores session-recovery state in `action_effects.reconciliation`; R17b/R17c reuse the V1.5 tables; R25a reuses the V1.6 tables. Any packet that believes it needs another V1.7 migration must stop and split.

Ordering after V1.7: M18-01 → M18-02 → M19-01 → (V2.0 candidate tables) → M23-01 → M23-02 → M23-03 → M23-04 → M30-01 → M30-02 → M30-03 → M30-04, each `down_revision` = the previous head, each landing with its repository code in the packet named in the queue (`18-02`, `18-05`, `19-02`, `20-02`, `23-01`, `23-04`, `23-09`, `23-10`, `V30A-001`, `V30B-001`, `V30C-001`, `V30E-001`). `18-04` adds `site_epoch` to `action_effects`, `task_leases` and `worker_results` as NULLable columns; NULL means "pre-epoch, historical, never fresh authority".

## V1.8 migration group

### M18-01 SiteAuthority
Candidate durable records:
- site_authority
- authority_transition_receipt

Add `site_epoch` / authority binding to whichever durable records represent:
- dispatch/lease;
- accepted result;
- consequential action/effect reservation/receipt.

Compatibility:
- pre-epoch records are historical/legacy and cannot automatically become fresh authority.

### M18-02 Recovery metadata
Candidate:
- backup_manifest metadata refs;
- recovery_run / reconciliation receipt.

Backup binary/database artifacts remain external references/digests rather than huge DB blobs.

## V1.9 migration group

### M19-01 Extensions
Candidate:
- extension_manifest
- extension_install
- project_extension_grant
- extension_transition_receipt

Unique constraints:
- extension_id + version;
- project + extension/version grant identity.

No secret values in manifest/grant tables.

## V2.0 migration group

Avoid new product feature schema unless needed for:
- candidate manifest;
- support/evidence binding.

Candidate:
- product_candidate
- candidate_evidence_binding

The artifact registry may remain file-governed; do not silently move acceptance authority into runtime DB.

## V2.3 migration group

### M23-01 Scheduler durable state
Candidate:
- scheduler_policy
- project_scheduling_state
- mission_scheduling_state where needed
- scheduler_decision_receipt or append-only event reference

### M23-02 Resource reservation intents
Candidate:
- resource_reservation_intent
- resource_reservation_component

Unique/fencing:
- one active authoritative intent per dispatch/attempt scope as contract defines.

### M23-03 Capability packs
Candidate:
- capability_pack_manifest
- installed_capability_pack
- project_capability_pack_grant

Prefer sharing extension trust/lifecycle tables where semantics align rather than duplicating.

### M23-04 Portability/audit metadata
Candidate:
- export_bundle_manifest
- import_run / reconciliation receipt

Large exported payloads should be artifact refs/digests, not necessarily relational rows.

## V3.0 migration group

### M30-01 Objectives
- objective
- objective_version
- trigger_receipt
- mission_proposal

Critical unique constraints:
- objective/version immutable identity;
- trigger dedupe scope/key;
- proposal idempotency scope.

### M30-02 Learning
- learning_proposal
- learning_transition_receipt
- learning_evaluation_run
- learning_canary_run

Do not store held-out answer plaintext on worker-visible/general runtime rows. Store sealed refs/digests/access policy.

### M30-03 Allocation
Prefer using V2.3 scheduler reservation/decision tables.
Add objective allocation metadata only when it cannot be represented as scheduler inputs/receipts.

### M30-04 Capability trust/audit
Extend pack/extension tables for:
- publisher trust;
- signature;
- revocation;
- tenancy/audit refs.

Avoid duplicate ecosystems.

## Migration test matrix per group

Every migration group should prove:
1. clean upgrade from immediately supported predecessor;
2. upgrade with representative existing data;
3. restart after migration;
4. current application reads/writes new schema;
5. downgrade/rollback strategy where supported;
6. failed migration leaves documented recoverable state;
7. no secrets introduced;
8. constraints reject duplicate/stale authority cases;
9. migration state included in CandidateManifest.

## Candidate invalidation

Any migration after a V2/V3 candidate freeze invalidates that candidate unless the frozen acceptance protocol explicitly classifies it as non-affecting and independent review confirms.
