# SwarmAI future acceptance case IDs

Date: 2026-09-21
Status: PLANNING ONLY

Purpose: stable names for tests/evidence so source, CI, live receipts and reviews can refer to the same scenario.

## V1.8

- V18-AUTH-001 current epoch dispatch succeeds.
- V18-AUTH-002 stale epoch dispatch denied.
- V18-AUTH-003 stale epoch lease/result denied.
- V18-AUTH-004 stale epoch consequential effect denied.
- V18-AUTH-005 duplicate authority activation denied/reconciled.
- V18-BACKUP-001 backup manifest excludes secret values.
- V18-BACKUP-002 backup integrity corruption detected.
- V18-RESTORE-001 restore creates/activates new epoch.
- V18-RESTORE-002 in-flight lease reconciliation is deterministic.
- V18-RESTORE-003 unknown effect remains unknown/fenced.
- V18-SPLIT-001 old site cannot accept new work after recovery.
- V18-DRILL-001 real outage/restore produces measured RPO/RTO.

## V1.9

- V19-EXT-001 valid extension install.
- V19-EXT-002 incompatible version rejected.
- V19-EXT-003 invalid digest/signature rejected when trust policy applies.
- V19-EXT-004 project grant cannot exceed manifest/global policy.
- V19-EXT-005 cross-project extension use denied.
- V19-EXT-006 extension direct provider/tool bypass denied.
- V19-EXT-007 draining extension receives no new work.
- V19-INSTALL-001 clean empty install.
- V19-INSTALL-002 install starts with empty product state.
- V19-UPGRADE-001 supported predecessor upgrade.
- V19-UPGRADE-002 failed migration is recoverable/fail-closed.
- V19-ROLLBACK-001 rollback restores supported usable state.
- V19-SUPPORT-001 support bundle contains no secrets.
- V19-SELFDEV-001 bounded issue creates isolated candidate.
- V19-SELFDEV-002 selfdev cannot self-merge/release.
- V19-SELFDEV-003 failed attempt retained.

## V2.0

- V20-CAND-001 CandidateManifest binds exact source/schema/dependencies/policies.
- V20-CAND-002 material candidate change invalidates prior evidence as protocol requires.
- V20-SUPPORT-001 every "supported" matrix cell has evidence.
- V20-SUPPORT-002 unavailable/unsupported remains explicit.
- V20-INSTALL-001 frozen candidate clean install.
- V20-UPGRADE-001 frozen candidate upgrade.
- V20-ROLLBACK-001 frozen candidate rollback.
- V20-SEC-001 zero unapproved consequential effects in negative suite.
- V20-PERF-001 benchmark reports total orchestration overhead.
- V20-REL-001 reliability campaign starts from frozen protocol/candidate.
- V20-REL-002 missed/failed interval remains evidence.
- V20-REL-003 elapsed window not backfilled.
- V20-REVIEW-001 independent release review references exact candidate/evidence.

## V2.3 Scheduler

- V23-SCHED-001 deterministic same-state tie-break.
- V23-SCHED-002 project A cannot starve B/C indefinitely.
- V23-SCHED-003 multiple missions do not multiply project fair share.
- V23-SCHED-004 priority aging provides bounded service floor.
- V23-SCHED-005 incompatible head task does not block later eligible task.
- V23-SCHED-006 denied privacy/provider/tool constraint is not relaxed.
- V23-RES-001 all required reservation components ready before dispatch.
- V23-RES-002 partial reservation failure compensates/releases.
- V23-RES-003 crash in preparing reconciles before redispatch.
- V23-RES-004 unknown external resource/effect state blocks unsafe retry.
- V23-BP-001 overload creates bounded backpressure.
- V23-CANCEL-001 cancellation fences future dispatch.
- V23-DRAIN-001 worker/project drain fences future work.
- V23-EPOCH-001 stale scheduler epoch cannot authorize dispatch.
- V23-RECEIPT-001 decision receipt explains choice without private raw content.

## V2.3 Packs/portability/observability/fleet

- V23-PACK-001 install versioned pack.
- V23-PACK-002 enable only for authorized project.
- V23-PACK-003 pack cannot widen permission/model qualification implicitly.
- V23-PACK-004 drain/disable blocks new use.
- V23-PORT-001 export contains no secret values.
- V23-PORT-002 import reconciles versions deterministically.
- V23-PORT-003 deleted/unauthorized knowledge absent after import.
- V23-OBS-001 read-only observability cannot mutate state.
- V23-OBS-002 dashboard mutation passes normal action/approval boundary.
- V23-FLEET-001 placement respects trust/locality/privacy.
- V23-FLEET-002 stale/drained worker receives no work.
- V23-FLEET-003 restart preserves coherent placement/fairness state.

## V3.0 Objectives

- V30-OBJ-001 duplicate event -> one authoritative proposal.
- V30-OBJ-002 schedule occurrence survives restart without duplicate.
- V30-OBJ-003 missed-run policy deterministic.
- V30-OBJ-004 burst obeys rate/max-active.
- V30-OBJ-005 pause blocks new proposals.
- V30-OBJ-006 revoke irreversible for objective version.
- V30-OBJ-007 edit creates immutable new version.
- V30-OBJ-008 authority revoked after trigger fences proposal before mission admission.
- V30-OBJ-009 cross-project trigger leaks no content/count/existence.
- V30-OBJ-010 multiple objectives do not multiply project fair share.
- V30-OBJ-011 stale objective version trigger rejected.
- V30-OBJ-012 real schedule evidence uses actual wall clock.

## V3.0 Learning

- V30-LEARN-001 protected authority change blocked before held-out.
- V30-LEARN-002 calibration data cannot count as held-out.
- V30-LEARN-003 held-out contamination terminal.
- V30-LEARN-004 frozen metric/scorer/sample/stop rule cannot change mid-run.
- V30-LEARN-005 quality win + cost guardrail loss -> rejected.
- V30-LEARN-006 competing candidates use frozen selection rule; loser retained.
- V30-LEARN-007 canary regression triggers deterministic rollback.
- V30-LEARN-008 stale candidate execution fenced after rollback.
- V30-LEARN-009 dependency drift expires learned version.
- V30-LEARN-010 failed attempts retained.
- V30-LEARN-011 selfdev cannot edit own governance/reviewer/evidence contract.
- V30-LEARN-012 selfdev cannot self-merge/release.

## V3.0 Allocator/ecosystem/fleet

- V30-ALLOC-001 allocator cannot bypass V2.3 scheduler.
- V30-ALLOC-002 fair share preserved.
- V30-ALLOC-003 provider quota/budget preserved.
- V30-ALLOC-004 privacy/locality preserved.
- V30-ALLOC-005 hidden starvation/cost shifting fails guardrail.
- V30-CAP-001 over-scoped/malicious capability denied.
- V30-CAP-002 revoked capability cannot execute new work.
- V30-TENANT-001 cross-tenant content/effect access denied.
- V30-TENANT-002 audit export contains no secrets.
- V30-AUDIT-001 trigger -> proposal -> mission -> scheduler -> execution/effect trace reconstructible.

## Naming recommendation

Unit/integration tests should include the case ID in test name/docstring/parameter ID where practical.
Live evidence should include `case_ids` in its manifest.
Review records should state which case IDs were actually witnessed versus only implemented.
