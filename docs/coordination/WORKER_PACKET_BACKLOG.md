# SwarmAI worker packet backlog

Updated: 2026-09-21T01:24:30Z. `ARTIFACT_REGISTRY.json` is canonical. Packets only advance artifacts; story points describe complexity/risk, never hours. Workers do not self-accept artifacts.

## Latest lead reviews

- **V2A-001 / ART-V12-BROKER-CONTRACT / SP2 — lead verified.** Source `c3df96ef074568e7a92dd2f6c6bfd070fe5374f3`; CI `35548643473` green.
- **V2A-002 / ART-V11-RESTART-EVIDENCE / SP1 — lead verified.** Source `48a02e3daae13f8fb569225e2d030097229f4780`; evidence `ee5a06612aa2e4409fa8bbfd1969225c16887615`; CI `35549111809` green.
- **V2A-003a / ART-V15-LEASE-FENCING / SP2 — first review changes required.** Source `630ab780ab45858c5dad4075be143cfa145e975f`; evidence `37f95fe63a1bf451f5d513855a7fcf1bb37d3d9b`. Required real previous-schema migration proof, token rotate/revoke lifecycle and recursive token-metadata protection.
- **V2A-003a-R / SP1 — repair packet lead verified.** Source `92f59faf2ffc1d7e0f999d7cc9f8212f53f764f2`; evidence tip `8e2c9754c9f64aa0e68e4fe5de47d646713a5413`. Source/evidence prove Alembic upgrade from populated `9eb193b10f4e`, unknown project ownership remains null, token rotation invalidates the old credential, revocation fences the new credential, and nested token metadata is rejected. Current descendant tip `2ea443395590f047b3e2889787250084433f7f31` has CI `35550277430` green. This verifies the **foundation repair packet**, not the whole lease-fencing artifact.
- **V2A-003b / ART-V15-LEASE-FENCING / SP2 — changes required.** Source `7dcefe4c72ae9ada2ff512adeaf65eefa28632e2`; evidence bind `f55f8078b73597892b6dcddc2e41ac947d3c904e`. The later `2ea4433...` import-only fix made current-tip CI green, but source-review defects remain: claim does not validate current mission cancellation/status/source authority; renew does not require current worker project == lease project; fixed 32-row candidate scan can still block eligible task #33. Artifact remains drafting.
- Legacy intents `W-122A` and `W-111C` are superseded by V2A-001/V2A-002; do not double-count.

## Session A — runtime/control-plane/integration

Owns `cursor/v2-runtime-lane` and `cursor/v2-integration`; owns shared API/store/routes/schemas/CLI/lockfile/migrations. Current reviewed runtime descendant: `2ea443395590f047b3e2889787250084433f7f31`; CI `35550277430` green. **Do not treat V2A-003b as accepted just because CI is green.**

### READY A0 — V2A-003b-R — repair claim/renew/expire fencing
- Artifact: `ART-V15-LEASE-FENCING`
- SP2
- Intended artifact state: remain `drafting`; produce a reviewable claim/renew/expire slice. Full artifact still requires V2A-003c result-acceptance fencing.
- Base: current runtime-lane descendant containing verified V2A-003a-R.
- Required changes:
  1. Before creating an attempt/lease, validate current mission exists, is runnable/not cancelled, and task mission/project/graph/source/cancellation authority is still current. Failing any check must leave task/attempt/lease state unmutated.
  2. `renew_lease` must require the durable worker's **current project** to equal the lease project as well as matching worker ID, generation and token; project reassignment cannot renew an old-project lease.
  3. Remove the `_CLAIM_CANDIDATE_BATCH=32` head-of-line correctness limit. Safely paginate/filter until an eligible row is found or the current eligible set is exhausted; add a regression with >32 incompatible higher-priority rows followed by an eligible row.
  4. Preserve exactly-one-winner race, capability/privacy skip, renew/expire persistence and fail-closed behavior.
- Acceptance: direct negative tests for cancellation/source/project staleness, >32 HOL regression, focused DB tests, and full exact-tip CI green. No result acceptance fence or API route wiring is silently folded in.

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
- Integrate only lead-verified V2A-001 `c3df96e`, V2A-002 `48a02e3` + evidence `ee5a066`, and verified V2A-003a-R foundation source `92f59fa` **without** importing unreviewed V2A-003b behavior. If selective integration cannot separate the repair cleanly from 003b ancestry, leave the V15 foundation out until 003b-R is reviewed rather than importing unreviewed code.
- Run full available offline/backend/console/migration CI and record integration receipt with source commits/conflict decisions/exact integration SHA. No main merge.

### FOLLOW-ON A3 — V2A-003c — result acceptance fence
SP2; depends A0 review. Reject stale worker generation/lease/task revision/input/source/cancellation and duplicates; exactly one accepted result.

### FOLLOW-ON A4 — V2A-004 — durable worker service/client
SP3; depends A3. Registration/heartbeat/claim/result/drain against durable store with restart-safe tests.

### FOLLOW-ON A5 — V2A-003X — DBOS reuse spike
SP2; may proceed after stable repaired durable repository foundation. Verify installed DBOS API/version and isolated queue/restart/stale-fence behavior before ADR decision.

### LATER A6 — V2A-018a/b/c/d
Site epoch, backup, restore/reconcile and stale-site fence; blocked on durable worker/control store. Source implementation is authorized, public deployment is not.

## Session B — evaluation/knowledge/tools/product/beta

Owns `cursor/v2-product-lane`. Do not edit shared Session-A API/store/routes/schemas/CLI/lockfile/migration surfaces; hand central migration deltas to Session A. No Session B source change was observed in this lead heartbeat.

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

Lead continues architecture/acceptance/research rather than routine source implementation. `ART-V23-MULTIMISSION-OPS` now includes durable queue state, weighted-deficit invariants, anti-gaming, cross-resource DispatchIntent compensation, scheduler-epoch fencing, explain receipts and a preregisterable fairness design. V1.8 recovery, V2.0 security/reliability and V3 objective/learning contracts remain active lead lanes.

## Queue rule

Take dependency-ready work before waiting on human auth/provider/live gates. Keep >=3 ready packets per lane where practical. If a Session-B packet needs a shared Session-A-owned file, stop and hand off the delta. Every return names artifact ID, intended transition, base/completion SHA, exact tests/evidence and remaining blockers.
