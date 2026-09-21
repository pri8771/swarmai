# SwarmAI worker packet backlog

Updated: 2026-09-21T02:12:00Z.

## Latest lead reviews

- **V2A-001 / ART-V12-BROKER-CONTRACT / SP2 — lead verified.** Source `c3df96ef074568e7a92dd2f6c6bfd070fe5374f3`; CI `35548643473` green.
- **V2A-002 / ART-V11-RESTART-EVIDENCE / SP1 — lead verified.** Source `48a02e3daae13f8fb569225e2d030097229f4780`; evidence `ee5a06612aa2e4409fa8bbfd1969225c16887615`; CI `35549111809` green.
- **V2A-003a / ART-V15-LEASE-FENCING / SP2 — first review changes required.** Source `630ab780ab45858c5dad4075be143cfa145e975f`; evidence `37f95fe63a1bf451f5d513855a7fcf1bb37d3d9b`. Required real previous-schema migration proof, token rotate/revoke lifecycle and recursive token-metadata protection.
- **V2A-003a-R / SP1 — repair packet lead verified.** Source `92f59faf2ffc1d7e0f999d7cc9f8212f53f764f2`; evidence tip `8e2c9754c9f64aa0e68e4fe5de47d646713a5413`. Source/evidence prove Alembic upgrade from populated `9eb193b10f4e`, unknown project ownership remains null, token rotation invalidates the old credential, revocation fences the new credential, and nested token metadata is rejected. This verifies the foundation repair packet, not the whole lease-fencing artifact.
- **V2A-003b / ART-V15-LEASE-FENCING / SP2 — changes required.** Source `7dcefe4c72ae9ada2ff512adeaf65eefa28632e2`; evidence bind `f55f8078b73597892b6dcddc2e41ac947d3c904e`. Source-review defects remain: claim does not validate current mission cancellation/status/source authority; renew does not require current worker project == lease project; fixed 32-row candidate scan can still block eligible task #33. Artifact remains drafting.
- **V2A-003b-R / ART-V15-LEASE-FENCING / SP2 — changes required after completed repair review.** Source `e764834a69315d1c2c85f00322c3392aa5037fd9`; evidence `c6e0a8f0634eddc473fe66aa1d3cb55352dc25a6`; focused suite 52 passed. Lead confirmed claim authority/dependency/HOL/renew-horizon improvements but found two remaining defects: renew does not explicitly fence terminal task/attempt state, and expiry authority is task-only so it can miss lease/attempt source/revision/cancellation drift. Follow-up is V2A-003b-R2; artifact remains drafting.
- **V2A-H6A / ART-V20-FOUNDATION-HARDENING / SP2 — changes required.** Implementation `77ef7e4c1675b74dbfcdeba27f8c955ae39f119c`; evidence bind `99733dccd91fc2b8356f96ff755f9b9aab20f2b4`; current tip `7a2491a2840ef8381e275b05e11f3f76c7a522e6`; CI `35550769734` green. Fixed credentials were removed and compose fails closed, but the generated secret-bearing `deploy/compose/.env` is not explicitly owner-only and `--force` is not guarded/documented against initialized-volume credential mismatch. Repair is V2A-H6A-R.
- **V2A-020a / ART-V20-INTEGRATED-CANDIDATE / SP1 — lead accepted.** Integration receipt `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code baseline `ee5a06612aa2e4409fa8bbfd1969225c16887615`, CI `35550653160` green. It correctly integrated only lead-reviewed V2A-001/V2A-002 lineage and left V15 out because its ancestry still contains unreviewed 003b behavior. The artifact remains **drafting**; this packet only establishes a clean reviewed integration baseline.
- Legacy intents `W-122A` and `W-111C` are superseded by V2A-001/V2A-002; do not double-count.

## Session A — runtime/control-plane/integration

Owns `cursor/v2-runtime-lane` and `cursor/v2-integration`; owns shared API/store/routes/schemas/CLI/lockfile/migrations. Current runtime tip: `7a2491a2840ef8381e275b05e11f3f76c7a522e6`, CI `35550769734` green. Current integration tip: `9ce727842446b98cfa55c28c7e70808f57f17d7b`, CI `35550653160` green. **Do not treat V2A-003b as accepted merely because descendants are green.** Integration must continue to import only independently reviewed slices.

### READY A0 — V2A-003b-R2 — terminal/expiry authority final repair
- Artifact: `ART-V15-LEASE-FENCING`
- SP1
- Base: current runtime branch descendant containing V2A-003b-R source `e764834a...`; do not restart earlier work.
- Intended artifact state: remain `drafting`; make the claim/renew/expire slice genuinely reviewable. V2A-003c result acceptance still follows.
- Required changes:
  1. Renewal must explicitly reject a terminal/incompatible TaskRow even if MissionRow remains runnable. Fence accepted/rejected/failed/cancelled/superseded or equivalent terminal task states.
  2. Renewal must reject a terminal/incompatible TaskAttemptRow, including terminal status, `terminal_at`, completed/accepted result state, or `accepted_result_id` when present.
  3. Expiry/requeue must compare TaskLeaseRow/TaskAttemptRow stored task revision, source revision and cancellation generation against current durable mission/task authority before returning a task to ready. The current task-only `_expire_task_status(task)` check is insufficient when source authority changed after claim but TaskRow payload lacks the old source marker.
  4. Add direct DB-backed regressions for terminal task renew, terminal/accepted attempt renew, post-claim source drift at expiry, cancellation/revision drift at expiry, and prove stale work is non-dispatchable.
  5. Preserve the existing 52-test behaviors: current claim authority, dependency readiness, >32 pagination, race, project-scoped renew, renewable horizon, cancelled-mission no-revive.
  6. Rebind evidence to the new implementation SHA and run exact-tip CI.
- Acceptance: no source/evidence ambiguity; do not self-accept. Lead review required before V2A-003c.
### READY A1 — V2A-H6A-R — secret-file and overwrite-safety repair
- Artifacts: `ART-V20-FOUNDATION-HARDENING`, `ART-V18-DEPLOYMENT-MANIFEST`, `ART-V19-INSTALL-UPGRADE`
- SP1
- Base: H6A source slice `77ef7e4c...` / current runtime descendant `7a2491a...`; keep this deploy/config repair separable from unreviewed V15 behavior for later cherry-pick/integration.
- Required changes:
  1. Generated `deploy/compose/.env` contains a database credential. Write it owner-only (`0600` on POSIX) and verify permissions in a deterministic test. Existing secret files repaired/overwritten by this helper must not remain group/world-readable.
  2. `--force` must not imply safe credential rotation for an already initialized Postgres volume. Guard or explicitly rename/require acknowledgement so a fresh generated password cannot silently desynchronize the DSN/container env from an existing database role. Never print the secret.
  3. Preserve current fail-closed DSN, loopback API bind, no host DB port, required compose vars and green compose-config smoke.
  4. Rebind sanitized evidence to the repaired source and exact-tip CI.
- Acceptance: focused deployment tests plus full exact-tip CI green; evidence says local/private hardening only and makes no public deployment/rotation claim.

### READY A2 — V2A-003X — DBOS reuse spike
- Artifact: `ART-V15-ARCH` / implementation-choice evidence for durable execution
- SP2
- Isolated spike only; no production queue replacement in this packet. Keep writes outside Session-A shared production schema unless the spike produces a reviewed delta.
- Inspect the installed DBOS version/API actually pinned in the environment, then build a minimal isolated proof for durable enqueue/claim or workflow restart semantics, crash/restart behavior, duplicate delivery expectations, and how Swarm lease/source/cancellation fences would map to it.
- Compare reuse against the existing SQLAlchemy/Postgres durable repository on complexity, recovery semantics, observability and migration risk. Do not claim DBOS solves Swarm-specific fencing without evidence.
- Acceptance: exact installed version/API refs, reproducible isolated tests, restart/stale-fence observations, and an ADR recommendation (`reuse`, `partial reuse`, or `do not adopt`) with explicit gaps. No source migration or V1.5 acceptance in this spike.

### REVIEWED A3 — V2A-020a — integration baseline
- Packet lead accepted at `9ce727842446b98cfa55c28c7e70808f57f17d7b` / code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.
- Artifact remains `ART-V20-INTEGRATED-CANDIDATE = drafting`.
- Next integration packet should only import newly lead-reviewed slices. Do not merge the runtime branch wholesale while 003b remains unreviewed.

### FOLLOW-ON A4 — V2A-003c — result acceptance fence
SP2; depends A0 review. Reject stale worker generation/lease/task revision/input/source/cancellation and duplicates; exactly one accepted result.

### FOLLOW-ON A5 — V2A-004 — durable worker service/client
SP3; depends A4. Registration/heartbeat/claim/result/drain against durable store with restart-safe tests.

### LATER A6 — V2A-018a/b/c/d
Site epoch, backup, restore/reconcile and stale-site fence; blocked on durable worker/control store. Source implementation is authorized, public deployment is not.

## Session B — evaluation/knowledge/tools/product/beta

Owns `cursor/v2-product-lane`. Current branch remains `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea`; **no Session B source change or worker message was observed in this heartbeat.** Do not fabricate activity. Session B must not edit shared Session-A API/store/routes/schemas/CLI/lockfile/migration surfaces; hand central migration deltas to Session A.

### READY B0 — V2B-000 — sync reviewed integration baseline
- Artifact: `ART-V20-INTEGRATED-CANDIDATE` support packet
- SP1
- Product branch has no product implementation yet, so merge only `origin/cursor/v2-integration` into `cursor/v2-product-lane` before B1.
- Preserve branch-local heartbeat/session instruction files; do not import unreviewed runtime-lane V15 work.
- Run baseline Ruff/mypy/pytest and console lint/test/build as available; push exact merge SHA and report Windows-specific results.
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
- Mandatory operational project ID, exact operation/destination/payload digest, expiry/revocation, explicit test fixture helper only; no production `proj_demo` default.

### FOLLOW-ON B5/B6/B7/B8
Permission-first retrieval -> supersession/deletion -> ToolGateway/effect-key semantics -> extension manifest.

## Honest blocked acceptance artifacts

- `ART-V10-WORKER-HEARTBEAT`: blocked on live `cursor agent` authentication; configured timer is not worker evidence.
- `ART-V12-REMOTE-OVERLAP`: broker verified, but **0 admissible remote routes** remain. No dual-remote claim until two exact account/model routes have fresh zero-charge/auth/quota/health evidence.
- `ART-V13-QUALIFIED-MATRIX`: blocked on B1 freeze and frozen-protocol held-out batches.
- `ART-V14-ROLE-MANIFEST` / live adaptive proof: blocked on actual G13 qualifications and dual-remote overlap.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock time cannot be accelerated/backfilled.

## Lead parallel artifacts

Lead continues architecture/acceptance/research rather than routine source implementation. `ART-V30-LEARNING-GOVERNANCE` was advanced this heartbeat with a formal proposal state machine, held-out contamination rules, preregistered selection/statistical discipline, protected-authority boundaries, deterministic rollback/fencing requirements, drift/revalidation rules and an explicit governance acceptance protocol. This is future architecture, not V3 acceptance or source implementation.

`ART-V23-MULTIMISSION-OPS`, V1.8 recovery, V2.0 security/reliability and V3 persistent-objective contracts remain active lead lanes.

## Queue rule

Take dependency-ready work before waiting on human auth/provider/live gates. Keep >=3 ready packets per lane where practical. If a Session-B packet needs a shared Session-A-owned file, stop and hand off the delta. Every return names artifact ID, intended transition, base/completion SHA, exact tests/evidence and remaining blockers.


## Reserve verification branch — dormant

`cursor/v2-verification-lane` exists only as a reserve branch. Do **not** start Session C merely because capacity exists.
Verification/review remains lead-owned while review capacity is healthy.
Previously drafted V2C packets are reserve ideas only and are not active worker assignments.
Current-tip G12 local revalidation is assigned to active Session A/lead after the critical V15 repair or in a non-conflicting A worktree.

## Heartbeat bootstrap packets

- **HB-A-BOOTSTRAP** — Session A pulls `SESSION_INSTRUCTIONS.md`, installs Mac heartbeat scheduler, publishes 3 consecutive valid 15-minute heartbeats.
- **HB-B-BOOTSTRAP** — Session B pulls `SESSION_INSTRUCTIONS.md`, installs Windows heartbeat scheduler, publishes 3 consecutive valid 15-minute heartbeats.
- Canonical protocol/state: `HEARTBEAT_PROTOCOL.md` + `HEARTBEAT_STATE.json`.
- After BOTH A and B have 3 valid 15-minute heartbeats, lead changes effective worker heartbeat cadence to hourly.
- This coordination heartbeat is not authenticated Cursor-agent FIX-004 evidence.
