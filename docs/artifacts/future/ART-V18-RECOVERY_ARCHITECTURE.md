# ART-V18-RECOVERY-ARCH — Cloud-first / local recovery architecture

Status: drafting
Target: V1.8
Owner: ChatGPT lead

## Goal

Run the SwarmAI control plane on an approved host when available while preserving a tested local recovery path and avoiding split-brain or silent billing.

## Distinguish three failures

1. Provider route failure — inference provider unavailable.
2. Worker failure — one execution node unavailable.
3. Site/control-plane failure — authoritative service/storage unavailable.

Do not call provider fallback "disaster recovery."

## Authority

Exactly one control plane may hold the active site lease/epoch.

Site record:
- site_id;
- epoch;
- lease holder;
- lease expiry;
- database generation;
- artifact generation/checkpoint;
- last backup;
- recovery mode.

A recovered local site cannot become writable until it acquires a new epoch/fencing authority. The old site becomes stale even if it reconnects later.

## Durable state classes

Critical:
- projects/identity scopes;
- missions/tasks/graphs;
- approvals/idempotency;
- reservations/quota ledger;
- accepted result pointers;
- artifact manifests;
- audit events.

Regenerable:
- caches;
- derived indexes;
- temporary worktrees;
- ephemeral model/session state.

Backups prioritize critical state and immutable artifacts.

## Recovery sequence

1. declare/verify primary unavailable;
2. freeze or fence old site via epoch mechanism where possible;
3. restore latest validated backup/checkpoint locally;
4. validate schema/migrations;
5. reconcile in-flight leases/reservations as uncertain/expired;
6. start control plane in recovery mode;
7. run integrity checks;
8. acquire new writable site epoch;
9. resume eligible work;
10. retain outage/recovery evidence.

## Metrics

Record:
- RPO: newest durable state timestamp recovered;
- RTO: time from declared recovery start to accepted writable service;
- number of uncertain/replayed tasks;
- lost/unavailable artifacts;
- duplicate-effect count (target zero);
- recovery resource/cost usage.

## V1.8 trial

Only after actual host entitlement/cost is verified:
- proposed 72-hour private trial;
- home worker off for a portion;
- cloud-eligible missions continue;
- actual site outage;
- local restore;
- complete recoverable work;
- prove stale old site cannot accept effects after recovery epoch changes.

No silent transition to a paid host.
