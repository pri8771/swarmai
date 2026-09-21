# V2 foundation hardening packets

Derived from ART-V20-FOUNDATION-HARDENING. These are normal worker packets, not a third implementation lane.

## Session A additions

### V2A-H2 — durable worker credential handling — SP1
Artifact: ART-V20-FOUNDATION-HARDENING / ART-V15-LEASE-FENCING
Bundle with V2A-003a if possible.
- durable worker row stores token hash/ref, never raw token;
- returned token is shown once;
- serialized inspection/evidence excludes raw token;
- revocation/rotation test.

### V2A-H3 — eligible-task claim / head-of-line fix — SP2
Artifact: ART-V20-FOUNDATION-HARDENING / ART-V15-LEASE-FENCING
Bundle with V2A-003b.
- atomic durable claim selects an eligible task;
- incompatible head task cannot block later eligible task;
- preserve fairness;
- two-worker race regression.

### V2A-H6A — deployment secret + runtime-mode hardening — SP2
Artifacts: ART-V18-DEPLOYMENT-MANIFEST / ART-V19-INSTALL-UPGRADE
- remove fixed DB password from normal compose;
- secret comes from explicit generated/operator config/ref;
- operational empty/unconfigured is default;
- container API binding is explicit and host exposure remains loopback/private;
- real compose health smoke.

### V2A-H8 — real backup/restore proof infrastructure — SP3
Artifacts: ART-V18-BACKUP-RESTORE / ART-V18-SPLIT-BRAIN-SAFETY
- replace sample-placeholder recovery truth with generated backup manifest/digests;
- restore clean DB/artifacts;
- reconcile leases/reservations;
- stale epoch reject;
- RPO/RTO actual timestamps.

## Session B additions

### V2B-H1 — memory project isolation migration — SP2
Artifacts: ART-V16-PROVENANCE / ART-V16-PERMISSION-RETRIEVAL
Bundle into V2B-003a/b.
- retrieval requires project_id/actor scope;
- routing memory project-scoped;
- recovery memory derives durable mission project ID, no hard-coded proj_local;
- two-project tests prove no content/count/preference/existence leak.

### V2B-H4 — remove demo approval defaults — SP1
Artifact: ART-V17-APPROVAL-BINDING
Bundle into V2B-004a.
- project_id mandatory operationally;
- fixture helper explicit/test-only;
- no proj_demo default on production helper.

### V2B-H5 — durable effect-key semantics contract/tests — SP2
Artifact: ART-V17-APPROVAL-BINDING
- effect key/project/operation/destination/payload binding;
- restart/duplicate/unknown-outcome scenarios;
- Session A later wires durable repository.

### V2B-H9 — non-demo selfdev path — SP3
Artifacts: ART-V19-BETA-ACCEPTANCE / ART-V19-SELFDEV-PR-EVIDENCE
- real preselected issue/repository, no supplied fix;
- isolated changes;
- independent tests/reviewer;
- PR/diff artifact only;
- old GOOD_FIX/demo path remains fixture/test-only.

### V2B-H10 — operator/install truth cleanup — SP1
Artifacts: ART-V19-INSTALL-UPGRADE / ART-V20-SUPPORT-MATRIX
After runtime behavior exists:
- remove normal-path recommendation to fall back to mock;
- update stale V0.9/RC labels;
- support matrix distinguishes dev fixture from operational mode.

## Lead review

Do not mark ART-V20-FOUNDATION-HARDENING reviewable until every H item has exact source/test evidence or an explicit fail-closed unsupported decision in the V2 support matrix.
