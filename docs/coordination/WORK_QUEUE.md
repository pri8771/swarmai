# SwarmAI artifact-derived execution queue — V2 acceleration

Canonical state: `ARTIFACT_REGISTRY.json`. Detailed packet contracts: `WORKER_PACKET_BACKLOG.md`. Owner authorizes source implementation through V3.0; immediate target is a V2.0 implementation/artifact-complete candidate. Main merge/public release/additional spend remain separately gated.

## Current reviewed source truth

- Session A runtime WIP: `5f3388b1b9ebded8de532e86ee6fcd6c34c99ea6`; Actions `35551159907` green for offline/backend + console. DB integration skipped without `SWARM_DATABASE_URL`; live-gated job is notice-only. Commit explicitly says WIP/incomplete/not evidence-bound.
- V2 integration: `9ce727842446b98cfa55c28c7e70808f57f17d7b`; code baseline `ee5a06612aa2e4409fa8bbfd1969225c16887615`; Actions `35550653160` green.
- Session B product lane: `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea`; no new source activity/message observed in LEAD-022.
- Historical V1.4 base/PR #14: `2c08f968...`; main remains `b9141fa3150f853586dede0334a47b344571bc16`.
- Current active worker topology is Session A + Session B. Verification/review remains lead-owned; reserve verification branch is dormant unless explicitly reassigned for a concrete isolated bottleneck.

## Lead review in LEAD-022

### V2A-003b-R WIP — not submitted/accepted

`ART-V15-LEASE-FENCING` work at `5f3388b...` contains useful repairs:
- claim validates current mission status/project/graph/source/cancellation authority before lease mutation;
- renew checks durable worker project against lease project;
- claim scanning uses keyset pagination and no longer has the old fixed 32-row correctness ceiling;
- regressions cover cancelled/stale claim authority, worker project reassignment and >32 incompatible queue heads.

Two required gaps remain before this packet can be reviewable:
1. `renew_lease()` must re-check **current** mission/task/source/cancellation authority, not only the persisted worker/lease generation/project/window.
2. `expire_leases()` must never revive cancelled/superseded/stale-authority work to `ready`; add direct negative regression(s).

No artifact transition or worker-performance score was recorded because this was explicitly an interrupted WIP checkpoint, not a completed review request.

### Previously reviewed decisions still controlling

- **V2A-020a / ART-V20-INTEGRATED-CANDIDATE / SP1 accepted packet** — integration baseline `9ce727842...` correctly contains only reviewed V2A-001/V2A-002 lineage. Artifact remains drafting.
- **V2A-H6A / ART-V20-FOUNDATION-HARDENING / SP2 changes required** — owner-only secret-file permissions plus explicit fresh-config overwrite semantics remain.
- V2A-001 broker contract and V2A-002 real process-restart evidence remain verified.

## Session A — runtime/control plane/distributed/recovery + integration

Branches: `cursor/v2-runtime-lane` and `cursor/v2-integration`. Session A owns shared API/store/routes/schemas/CLI/lockfile/migrations.

Ready now:
1. **Finish V2A-003b-R / ART-V15-LEASE-FENCING / SP2** in the existing worktree. Add renewal-time mission/task/source/cancellation authority revalidation; prevent expiry from requeueing stale/cancelled/superseded tasks; add DB-backed negatives; return exact completion/evidence SHA and exact-tip CI. Do not restart the packet or integrate WIP ancestry yet.
2. **V2A-H6A-R / ART-V20-FOUNDATION-HARDENING / SP1** — secret-bearing compose env owner-only permissions plus explicit fresh-config overwrite semantics; preserve fail-closed/private behavior and rebind evidence.
3. **V2A-003X / ART-V15-DBOS-REUSE / SP2** — isolated DBOS reuse spike against the actual pinned version/API; queue/restart/duplicate/stale-fence evidence and ADR recommendation only, no production transport switch.
4. **Current-tip G12 local fallback/admission revalidation / ART-V12-LOCAL-FALLBACK + ART-V12-ADMISSION-RECONCILIATION / SP2** — after the critical V15 repair or in a non-conflicting worktree, prove actual current local-model execution/route loss + reservation/reconciliation; historical stubbed broker evidence is regression prep only.

After V2A-003b-R lead acceptance: V2A-003c result-acceptance fencing -> V2A-004 durable worker service/client -> real multi-host/recovery evidence. Integrate only lead-reviewed slices.

## Session B — evaluation/knowledge/tools/product/beta

Branch `cursor/v2-product-lane`. Keep off Session-A-owned shared API/store/routes/schemas/CLI/lockfile/migrations; hand central migration/integration deltas to Session A.

Ready now:
1. **V2B-001 / ART-V13-TASK-POOL / SP2** — freeze calibration/held-out IDs/hashes and source/license/size-classifier/scorer/prompt/tool/model-config manifest. No counted held-out qualification before lead freeze.
2. **V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3** — calibration-only reviewer benchmark/scorer repair and freeze; no qualification claim or held-out contamination.
3. **V2B-003a+H1 / ART-V16-PROVENANCE / SP2** — versioned project-scoped provenance/permission labels/tombstones and two-project non-leak tests; Session A owns central migration integration.
4. **V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2** — ActionEnvelope/ApprovalGrant/ActionReceipt contracts with mandatory project and exact operation/destination/payload binding; no production demo default.

Then: permission-first retrieval/supersession -> ToolGateway/effect-key semantics -> extension manifest/beta evidence. No Session-B activity has been observed yet; start a ready packet instead of waiting on live G12 or Cursor-CLI blockers.

## Earlier acceptance gates remain honest

- **V1.0:** all repair artifacts except `ART-V10-WORKER-HEARTBEAT` verified. Heartbeat blocked on actual Cursor CLI authentication and authenticated receipts.
- **V1.1:** required artifacts verified including real process restart; version set not promoted/accepted.
- **V1.2:** broker + provider eligibility verified; 0 admissible remote routes means remote overlap blocked. Local fallback/reconciliation are drafting pending current-tip actual-local proof.
- **V1.3:** protocol accepted; screening verified provisional; task pool not frozen, zero qualified cells, reviewer benchmark drafting.
- **V1.4:** role manifest/live adaptive proof blocked on G12/G13; logical load offline-only; LIVE-142 not started.

Do not call blocked live/time artifacts accepted because later source implementation proceeds.

## Human/live blockers

- `ART-V10-WORKER-HEARTBEAT`: `cursor agent status/whoami` not authenticated; only exact login/passkey/MFA/consent may require operator involvement.
- `ART-V12-REMOTE-OVERLAP`: zero admitted remote routes; exact account/model zero-charge/auth/quota/health evidence required before live proof.
- G13 qualification and G14 live proof remain prerequisite-bound.
- LIVE-142 and later reliability windows are real wall-clock evidence only; no acceleration or backfill.

## Lead lane

`ART-V30-OBJECTIVE-CONTRACT` was materially advanced in LEAD-022 with immutable objective versions, trigger receipts, deterministic schedule/missed-run semantics, MissionProposal admission, authority monotonicity, V2.3 fairness anti-amplification, learning-governance boundaries, restart/dedupe transaction semantics, threats and acceptance protocol. It remains drafting future architecture, not V3 acceptance.

Continue V30 learning/objective alignment with V2.3 scheduler/resource invariants and current V2.0 security/reliability review. Do not take routine SP1-SP3 implementation away from Cursor.

## Worker directive

Read `LEAD-20260921-022`, the canonical registry and backlog. Claim a dependency-ready packet with artifact ID, intended transition, base SHA/worktree and first test. Return exact source/evidence SHA and checks; do not self-accept. If auth/provider/live gates block one packet, switch to another ready packet rather than idling. The default active implementation team is Session A + Session B; do not activate another general Cursor lane without a concrete isolated bottleneck and explicit lead reassignment.
