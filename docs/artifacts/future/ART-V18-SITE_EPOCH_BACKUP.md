# ART-V18-SITE-EPOCH — site authority, backup and restore contract

Status: drafting
Target: V2.0 candidate / V1.8 capability group
Owner: ChatGPT lead
Depends on: ART-V18-RECOVERY-ARCH

## Authority model

Persist SiteAuthority:
- site_id
- epoch monotonically increasing
- role: active|recovery|stale
- acquired_at
- lease_expires_at
- database_generation
- artifact_checkpoint_id

Only the active current epoch may accept new consequential effects.

A restored site begins read-only/recovery. It becomes writable only after acquiring a new epoch according to the configured authority mechanism.

## BackupManifest

- backup_id
- created_at
- source_site_id/epoch
- schema_revision
- database_snapshot_ref + digest
- artifact_manifest_ref + digest
- config_manifest_digest (no secrets)
- mission high-water marks
- event-log high-water mark
- encryption/storage policy ref
- validation status

## Restore sequence

1. validate manifest/digests;
2. restore database;
3. restore/verify artifact manifest;
4. run migrations/integrity checks;
5. mark in-flight leases/reservations uncertain/expired according to policy;
6. start recovery-mode control plane;
7. acquire new site epoch;
8. enable writes;
9. reject old-site/stale-epoch effects.

## Session A implementation packets

- V2A-018a SP2: site authority model + guard.
- V2A-018b SP2: backup manifest + local DB/artifact backup CLI.
- V2A-018c SP3: restore/reconcile CLI.
- V2A-018d SP2: stale epoch/split-brain negatives.

## Evidence

- backup validates;
- restore to clean local state;
- durable mission/artifact IDs preserved;
- in-flight lease reconciled safely;
- stale site result/effect rejected;
- RPO/RTO reported from real drill.
