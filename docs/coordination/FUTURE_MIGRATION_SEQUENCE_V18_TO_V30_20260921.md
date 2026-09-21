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
