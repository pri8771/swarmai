# SwarmAI worker packet backlog

Updated: 2026-09-21T01:12:30Z. `ARTIFACT_REGISTRY.json` is canonical. Packets only advance artifacts; story points describe complexity/risk, never hours. Workers do not self-accept artifacts.

## Latest lead reviews

- **V2A-001 / ART-V12-BROKER-CONTRACT / SP2 — lead verified.** `c3df96ef074568e7a92dd2f6c6bfd070fe5374f3`, CI `35548643473` green. ProductStore generic execution is broker-required/fail-closed; direct local fallback cannot bypass admission.
- **V2A-002 / ART-V11-RESTART-EVIDENCE / SP1 — lead verified.** Implementation `48a02e3daae13f8fb569225e2d030097229f4780`, evidence `ee5a06612aa2e4409fa8bbfd1969225c16887615`, CI `35549111809` green. Real uvicorn process exit/restart and same durable mission reopened through HTTP and separate CLI.
- **V2A-003a / ART-V15-LEASE-FENCING / SP2 — changes required.** Source `630ab780ab45858c5dad4075be143cfa145e975f`, evidence tip `37f95fe63a1bf451f5d513855a7fcf1bb37d3d9b`, CI `35549624046` green. Schema/repositories are useful, but the accepted schema contract's representative-legacy-row migration proof is not actually exercised; V2A-H2 revocation/rotation evidence is absent; token-sensitive free-form metadata needs a recursive/typed boundary. Artifact stays drafting.
- Legacy intent packets `W-122A` and `W-111C` are superseded by V2A-001/V2A-002; do not double-count.

## Session A — runtime/control-plane/integration

Owns `cursor/v2-runtime-lane` and `cursor/v2-integration`; owns shared API/store/routes/schemas/CLI/lockfile/migrations.

### READY A0 — V2A-003a-R — repair durable worker foundation
- Artifact: `ART-V15-LEASE-FENCING` + `ART-V20-FOUNDATION-HARDENING`
- SP1
- Intended artifact state: remain `drafting`; produce a reviewable **foundation slice**, not full fencing acceptance.
- Base: current runtime lane descendant of `37f95fe63a1bf451f5d513855a7fcf1bb37d3d9b`.
- Required changes:
  1. Add a true Alembic migration-up test: bring an isolated Postgres DB to down-revision `9eb193b10f4e`, insert representative legacy `worker_leases` and `task_attempts` rows using that old schema, then upgrade to head and prove rows/legacy semantics remain intact. Do not fabricate unknown project ownership during backfill.
  2. Complete V2A-H2 token lifecycle: durable rotate + revoke semantics, previous token invalid after rotation/revocation, hash/ref only on disk, raw token never serialized into inspection/evidence.
  3. Make the token-sensitive metadata boundary recursive/typed so nested `token`/`membership_token`-style keys cannot be persisted inside free-form resource metadata.
- Acceptance: focused tests plus full current-tip CI; exact migration revisions/commands; no API route wiring or lease-claim behavior silently added to this repair.

### READY A1 — V2A-H6A — deployment secret/runtime-mode hardening
- Artifacts: `ART-V20-FOUNDATION-HARDENING`, `ART-V18-DEPLOYMENT-MANIFEST`, `ART-V19-INSTALL-UPGRADE`
- SP2
- Separate write surfaces from A0: deploy/compose/runtime config and focused deploy tests/docs.
- Remove fixed normal-mode DB password; explicit generated/operator secret/ref; operational empty/unconfigured default; explicit private/loopback exposure; real compose config/health smoke without public-deployment claim.

### READY A2 — V2A-020a — start V2 integration candidate from verified commits only
- Artifact: `ART-V20-INTEGRATED-CANDIDATE`
- SP1
- Intended transition: `planned -> drafting`.
- Branch: `cursor/v2-integration`.
- Integrate only lead-verified V2A-001 source `c3df96e`, V2A-002 source `48a02e3` and evidence binding `ee5a066` (or an exact descendant proven to contain no additional unreviewed source). Do **not** pull V2A-003a yet because lead requested changes.
- Run full available offline/backend/console/migration CI and record an integration receipt with source commits/conflicts/integration SHA. No main/PR merge.

### FOLLOW-ON A3 — V2A-003b + V2A-H3 — atomic eligible claim/renew/expire
- Artifact: `ART-V15-LEASE-FENCING`
- SP2
- Blocked until A0 is lead-reviewable.
- Transactional single-winner eligible-task claim; incompatible head cannot block later eligible task; fairness; renewal/expiry/CAS race tests.

### FOLLOW-ON A4 — V2A-003c — result acceptance fence
SP2; depends A3. Reject stale worker generation/lease/task revision/input/source/cancellation and duplicates; exactly one accepted result.

### FOLLOW-ON A5 — V2A-004 — durable worker service/client
SP3; depends A4. Registration/heartbeat/claim/result/drain against durable store with restart-safe tests.

### FOLLOW-ON A6 — V2A-003X — DBOS reuse spike
SP2; depends repaired foundation. Verify installed DBOS API/version and isolated queue/restart/stale-fence behavior before ADR decision.

### LATER A7 — V2A-018a/b/c/d
Site epoch, backup, restore/reconcile and stale-site fence; blocked on durable worker/control store. Source implementation is authorized, public deployment is not.

## Session B — evaluation/knowledge/tools/product/beta

Owns `cursor/v2-product-lane`. Do not edit shared Session-A API/store/routes/schemas/CLI/lockfile/migration surfaces; hand central migration deltas to Session A.

### READY B1 — V2B-001 / W-131C1 — freeze qualification pool/version manifest
- Artifact: `ART-V13-TASK-POOL`; SP2; `drafting -> reviewable`.
- Freeze calibration vs held-out IDs/hashes for coding/planning/reasoning/extraction × S/M/L/XL plus source/license, size-classifier, scorer/grader, prompt, tool and exact model config versions. Hidden answers not worker-visible. No counted qualification before lead freeze.

### READY B2 — V2B-002 / W-131C2 — reviewer calibration + benchmark freeze
- Artifact: `ART-V13-REVIEWER-QUALIFICATION`; SP3.
- Calibration only; diagnose weak reviewer screening, fix benchmark/scorer, version/freeze design; no reviewer qualification claim and no held-out contamination.

### READY B3 — V2B-003a + V2B-H1 — provenance repository/project isolation
- Artifact: `ART-V16-PROVENANCE` + V2 hardening; SP2.
- Versioned knowledge/provenance/permission labels/tombstones in Session-B module; no hard-coded `proj_local`; two-project non-leak tests. Hand schema migration delta to Session A.

### READY B4 — V2B-004a + V2B-H4 — ActionEnvelope/ApprovalGrant/ActionReceipt contracts
- Artifact: `ART-V17-APPROVAL-BINDING` + V2 hardening; SP2.
- Mandatory operational project_id, exact operation/destination/payload digest, expiry/revocation, explicit test fixture helper only; no production `proj_demo` default.

### FOLLOW-ON B5 — V2B-003b — permission-first retrieval
SP2; depends B3. Authorization before ranking/context plus retrieval receipts.

### FOLLOW-ON B6 — V2B-003c — supersession/deletion
SP2; depends B3. Version/tombstone/conflict tests.

### FOLLOW-ON B7 — V2B-004b + V2B-H5 — ToolGateway adapter/effect-key semantics
SP2; depends B4. Normalize existing gateway; durable effect identity binds project/operation/destination/payload; restart/duplicate/unknown-outcome tests; Session A owns central persistence integration.

### FOLLOW-ON B8 — V2B-019a — extension manifest
SP2; depends B4. Stable manifest/registry boundary with no arbitrary unreviewed code execution.

## Honest blocked acceptance artifacts

- `ART-V10-WORKER-HEARTBEAT`: blocked on live `cursor agent` authentication; configured timer is not worker evidence.
- `ART-V12-REMOTE-OVERLAP`: broker contract verified, but **0 admissible remote routes** remain. No dual-remote claim until two exact account/model routes have fresh zero-charge/auth/quota/health evidence.
- `ART-V13-QUALIFIED-MATRIX`: blocked on B1 freeze and frozen-protocol held-out batches.
- `ART-V14-ROLE-MANIFEST` / live adaptive proof: blocked on actual G13 qualifications and dual-remote overlap.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock time cannot be accelerated/backfilled.

## Lead parallel artifacts

Lead continues architecture/acceptance/research rather than routine source implementation. `ART-V23-MULTIMISSION-OPS` now includes durable queue state, weighted-deficit invariants, anti-gaming rules, dispatch-intent reservation compensation, scheduler-epoch fencing, explain receipts and a preregisterable fairness test design. V1.8 recovery, V2.0 security/reliability and V3 objective/learning contracts remain active lead lanes.

## Queue rule

Take dependency-ready work before waiting on human auth/provider/live gates. Keep >=3 ready packets per lane where practical. If a Session-B packet needs a shared Session-A-owned file, stop and hand off the delta. Every return names artifact ID, intended transition, base/completion SHA, exact tests/evidence and remaining blockers.
