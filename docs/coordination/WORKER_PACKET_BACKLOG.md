# SwarmAI worker packet backlog

Updated: 2026-09-21T01:05:00Z. `ARTIFACT_REGISTRY.json` is canonical. Packets exist only to advance artifact state; story points are complexity/risk metadata, never hours. Worker completion never self-accepts an artifact.

## Newly reviewed worker results

- **V2A-001 / ART-V12-BROKER-CONTRACT / SP2 — completed, lead verified.** Source `c3df96ef074568e7a92dd2f6c6bfd070fe5374f3`; CI `35548643473` green. Independent source/test review confirmed ProductStore generic execution injects the governed project-scoped broker and `require_broker` deny/missing/unregistered-route paths cannot fall through to direct `local_chat`.
- **V2A-002 / ART-V11-RESTART-EVIDENCE / SP1 — completed, lead verified.** Implementation `48a02e3daae13f8fb569225e2d030097229f4780`, evidence tip `ee5a06612aa2e4409fa8bbfd1969225c16887615`; CI `35549111809` green. Evidence shows real uvicorn PID stop/start, first process exit, same durable mission ID/status/disk hash reopened by HTTP and separate CLI.
- Legacy intent packets `W-122A` and `W-111C` are superseded by V2A-001 and V2A-002 respectively; do not double-count them.

## Session A — runtime/control-plane/integration

Session A owns `cursor/v2-runtime-lane` and integration branch `cursor/v2-integration`. It owns shared API/store/routes/schemas/CLI/lockfile/migration integration. Do not let Session B edit those surfaces without an explicit handoff.

### READY A1 — V2A-003a + V2A-H2 — durable worker repository foundation
- Artifact: `ART-V15-LEASE-FENCING` + hardening contribution to `ART-V20-FOUNDATION-HARDENING`
- SP: 2 (H2 folded in, not separately counted)
- Intended transition: `ART-V15-LEASE-FENCING drafting -> reviewable` only for the durable repository/schema slice; whole lease/fence artifact remains incomplete until later packets.
- Write surfaces: `src/swarm/db/`, worker durable repository module, Alembic migration, focused tests. Session A owns central SQLAlchemy Base/migrations.
- Contract: extend the accepted `ART-V15-DURABLE-SCHEMA`; do not create a second persistence authority. Persist worker generation/status/capabilities/token hash or opaque credential reference, task attempts, lease identity/generation/expiry, result acceptance state and required outbox/effect linkage. Never persist raw worker token.
- Tests: migration up/down where supported, repository CRUD/unique constraints, token hash/ref only, token returned once, inspection/evidence redaction, revocation/rotation semantics, project ownership/isolation.
- Evidence: exact base/completion SHA, schema/migration identities, commands/results, DB mode and no-secret assertion.

### READY A2 — V2A-H6A — deployment secret + operational-default hardening
- Artifacts: `ART-V20-FOUNDATION-HARDENING`, `ART-V18-DEPLOYMENT-MANIFEST`, `ART-V19-INSTALL-UPGRADE`
- SP: 2
- Intended transition: keep artifacts `drafting`; produce reviewable source/evidence slice.
- Write surfaces: deploy/compose/runtime configuration + focused deploy tests/docs; avoid worker DB modules used by A1.
- Do: remove fixed normal-mode DB password; load secret from explicit generated/operator config/ref; operational empty/unconfigured remains default; API bind/exposure explicit and private/loopback by default; add real compose config/health smoke that does not claim public deployment.
- Acceptance: no demo/mock fallback, no committed credential, no paid infrastructure assumption, deterministic unconfigured failure/health state.

### READY A3 — V2A-020a — integrate verified runtime artifacts
- Artifact: `ART-V20-INTEGRATED-CANDIDATE`
- SP: 1
- Intended transition: `planned -> drafting`.
- Branch: `cursor/v2-integration`.
- Do: verify runtime lane ancestry first. Integrate **only** lead-verified V2A-001 source `c3df96e`, V2A-002 source `48a02e3`, and its evidence binding `ee5a066` (or an exact descendant containing no unreviewed source). Do not pull later unreviewed runtime work by accident.
- Run the integrated full offline/backend/console/migration checks currently available. Record integration receipt with source commits, conflict decisions, exact integration SHA and CI.
- Do not merge `main` or PR #14; this is only the V2 integration lane.

### FOLLOW-ON A4 — V2A-003b + V2A-H3 — atomic eligible lease claim/renew/expire
- Artifact: `ART-V15-LEASE-FENCING`
- SP: 2
- Depends: A1 reviewable source.
- Atomic single-winner eligible-task claim; incompatible queue head cannot block a later eligible task; preserve fairness; renewal/expiry/CAS race tests.

### FOLLOW-ON A5 — V2A-003c — result acceptance fence
- Artifact: `ART-V15-LEASE-FENCING`
- SP: 2
- Depends: A4.
- Stale worker generation, lease token/generation, cancellation/source revision or duplicate result cannot become accepted.

### FOLLOW-ON A6 — V2A-004 — durable worker protocol service/client
- Artifact: `ART-V15-WORKER-PROTOCOL`
- SP: 3
- Depends: A5.
- Registration/heartbeat/claim/result/drain on durable store with restart-safe tests.

### FOLLOW-ON A7 — V2A-003X — DBOS reuse spike
- Artifact: `ART-V15-DBOS-REUSE`
- SP: 2
- Depends: A1.
- Verify installed DBOS version/API and isolated queue/restart/stale-fence behavior; ADR decision only after evidence.

### LATER A8 — V2A-018a/b/c/d — site epoch / backup / restore / stale-site fence
Blocked on durable worker/control store. Source implementation is authorized, but evidence must remain honest and no cloud/public deployment is implied.

## Session B — evaluation/knowledge/tools/product/beta

Session B owns `cursor/v2-product-lane`. Keep it out of shared API/store/routes/schemas/CLI/lockfile/migration files. When durable schema changes are needed, implement product-domain contracts/repository interfaces and hand the central migration delta to Session A.

### READY B1 — V2B-001 / W-131C1 — freeze qualification pool/version manifest
- Artifact: `ART-V13-TASK-POOL`
- SP: 2
- Intended transition: `drafting -> reviewable`.
- Machine-readable calibration vs held-out IDs/hashes for coding/planning/reasoning/extraction × S/M/L/XL; bind source/license, size-classifier, scorer/grader, prompt, tool contract and exact model config versions. Hidden answers must not be worker-visible. Do not run counted qualification until lead freezes this artifact.

### READY B2 — V2B-002 / W-131C2 — reviewer calibration + benchmark freeze
- Artifact: `ART-V13-REVIEWER-QUALIFICATION`
- SP: 3
- Intended transition: benchmark/scorer design `drafting -> reviewable`; **not reviewer qualification**.
- Calibration-only diagnosis of weak reviewer screening; repair task construction/decision contract/evidence bundle/grader as necessary; version and freeze new benchmark/scorer; held-out IDs remain untouched until lead review.

### READY B3 — V2B-003a + V2B-H1 — provenance repository and project isolation
- Artifact: `ART-V16-PROVENANCE` + hardening contribution to `ART-V20-FOUNDATION-HARDENING`
- SP: 2
- Intended transition: provenance source slice `drafting -> reviewable`.
- Build versioned knowledge classes/provenance/permission labels/tombstones behind Session-B-owned module using accepted `ART-V16-DURABLE-SCHEMA`. Retrieval/routing memory is project-scoped; no hard-coded `proj_local`; two-project tests prove no content/count/preference/existence leak. Hand migration contract to Session A rather than editing central migration files.

### READY B4 — V2B-004a + V2B-H4 — action/approval/receipt contracts
- Artifact: `ART-V17-APPROVAL-BINDING` + hardening contribution to `ART-V20-FOUNDATION-HARDENING`
- SP: 2
- Intended transition: contract source slice `drafting -> reviewable`.
- Implement `ActionEnvelope`, `ApprovalGrant`, `ActionReceipt` value/contracts in product-owned module; operational `project_id` mandatory; fixture helper explicit/test-only; no `proj_demo` production default. Exact action/operation/destination/payload digest and approval expiry/revocation fields required.

### FOLLOW-ON B5 — V2B-003b — permission-first retrieval
SP2; depends B3. Filter authorization before ranking/context; emit retrieval receipts.

### FOLLOW-ON B6 — V2B-003c — supersession/deletion
SP2; depends B3. Version/tombstone/conflict tests.

### FOLLOW-ON B7 — V2B-004b + V2B-H5 — ToolGateway adapter + durable effect-key semantics
SP2; depends B4. Normalize existing ToolGateway behind contracts; effect key binds project/operation/destination/payload; cover restart/duplicate/unknown-outcome semantics. Session A later wires central durable repository.

### FOLLOW-ON B8 — V2B-019a — extension manifest
SP2; depends B4. Stable manifest/registry interface; no arbitrary unreviewed code execution.

## Earlier/live blocked artifacts remain honest

- `ART-V10-WORKER-HEARTBEAT`: blocked on live `cursor agent` authentication; scheduler configuration alone is not worker execution.
- `ART-V12-REMOTE-OVERLAP`: broker is now verified, but remote proof remains blocked on **0 admissible remote routes**. Do not run/claim overlap until two exact account/model routes have fresh zero-charge/auth/quota/health admission evidence.
- `ART-V13-QUALIFIED-MATRIX`: blocked until B1 is independently frozen and counted held-out batches follow the frozen protocol.
- `ART-V14-ROLE-MANIFEST` / live adaptive proof: blocked on actual G13 qualifications and dual-remote proof.
- `ART-LIVE142-CAMPAIGN`: wall-clock campaign has not started. Do not accelerate or backfill time.

## Lead parallel work

Lead owns architecture/acceptance/research, not routine SP1-SP3 source implementation. Active parallel artifacts include V1.5 worker/fencing contracts, V1.8 recovery, V2.0 security/reliability/integration contracts, `ART-V23-MULTIMISSION-OPS`, and V3 persistent-objective/learning governance. Future source packets may be created when safe, but speculative future code must not contaminate the active V2 integration lane.

## Queue rule

Both sessions should always take a dependency-ready packet before waiting on human auth/provider/live gates. Keep at least three ready packets per lane where practical. If a packet touches a shared Session-A-owned file, stop and hand off the required delta instead of creating a parallel implementation authority. Every return must name artifact ID, intended transition, base/completion SHA, exact tests/evidence and remaining blockers.
