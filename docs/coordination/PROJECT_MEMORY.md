# SwarmAI compact project memory

Curated 2026-09-21 after `LEAD-20260921-022`. `ARTIFACT_REGISTRY.json` is canonical; this is a compact derived orientation. Read registry/state and unread messages before deeper evidence.

## Authority and operating model

Owner authorizes source implementation through V3.0. Major milestones: V1.7, V2.3, V3.0. Immediate target: a V2.0 implementation/artifact-complete candidate. Main merge, public release/deployment, additional spend/paid fallback and destructive actions remain separately gated. Live/time-bound acceptance is real wall-clock evidence and is never backfilled.

Management is artifact-oriented. ChatGPT owns architecture, contracts, research, decomposition, hard debugging after worker non-convergence and independent review. Cursor does most SP1-SP3 implementation/test work. Session A owns runtime/control-plane/distributed/recovery plus integration on `cursor/v2-runtime-lane` / `cursor/v2-integration`; Session B owns evaluation/knowledge/tools/product/beta on `cursor/v2-product-lane`. Shared API/store/routes/schemas/CLI/lockfile/migrations belong to Session A. A reserve verification branch may exist, but the current team is A+B; lead handles verification unless a concrete isolated bottleneck is explicitly reassigned.

## Current source truth

Main remains `b9141fa3150f853586dede0334a47b344571bc16`. Historical V1.4 base/PR #14 remains draft at `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea` and is not the V2 integration target.

Session A runtime WIP: `5f3388b1b9ebded8de532e86ee6fcd6c34c99ea6`; Actions `35551159907` green for offline/backend + console checks, with DB integration skipped without `SWARM_DATABASE_URL` and live gates not run. V2 integration remains `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code baseline `ee5a06612aa2e4409fa8bbfd1969225c16887615`; Actions `35550653160` green. Session B remains `2c08f...`; no Session-B source commit/message was observed in LEAD-022.

Lead-reviewed Session-A results:
- V2A-001 / `ART-V12-BROKER-CONTRACT` verified: generic ProductStore execution injects the governed project broker; broker-required paths cannot fall through to direct local inference.
- V2A-002 / `ART-V11-RESTART-EVIDENCE` verified: actual uvicorn process stop/start and same durable mission reopen through HTTP and separate CLI.
- V2A-003a-R durable schema/token-foundation repair verified, but the overall lease-fencing artifact is not accepted.
- V2A-020a SP1 accepted as a bounded integration baseline: only reviewed V2A-001/002 lineage is present. `ART-V20-INTEGRATED-CANDIDATE` remains drafting.
- V2A-H6A needs a small repair: owner-only permissions for generated secret-bearing compose env and explicit fresh-config overwrite semantics rather than implying safe live DB credential rotation.

V2A-003b-R is currently **WIP, not evidence-bound**. Source at `5f3388b...` fixes claim-time mission/project/graph/source/cancellation authority, worker-project renewal check and keyset pagination past the old 32-row HOL ceiling. Lead review found two remaining packet-contract gaps: lease renewal does not re-check current mission/task/source/cancellation authority, and expiry can still set a stale/cancelled/superseded leased task back to `ready`. Direct regressions for those paths are missing. Finish the WIP; do not restart or integrate it yet.

## Acceptance/gate truth

V1.0 repair: candidate/security/evidence/runtime artifacts verified; worker-heartbeat blocked because Cursor CLI auth/real authenticated receipts remain absent.

V1.1: required artifacts verified, including real process restart; artifact-set promotion remains separate.

V1.2: broker and provider eligibility verified, but **0 admissible remote routes** means remote overlap is blocked. Historical local fallback/reconciliation evidence used stubs and is insufficient for current live-local proof; Session A + lead must revalidate current-tip real local execution/admission before promotion.

V1.3: qualification protocol accepted; screening matrix = 72 provisional n=5 cells across three local configs and S/M/L/XL. Task/version pool not frozen; zero qualified cells; reviewer qualification drafting.

V1.4: graph/load work is offline preparation. Qualified roles/live adaptive proof remain blocked on G12/G13. LIVE-142 is preregistered but not started; mandatory wall-clock observation remains future truth.

V1.5 source implementation is active. `ART-V15-LEASE-FENCING` still needs completed V2A-003b-R plus V2A-003c result acceptance fencing. V1.6/V1.7 Session-B packets are ready but no Session-B source activity has been observed.

V2.0 integration has a clean drafting baseline (V2A-001/002 only). Foundation hardening remains drafting. Do not wholesale-merge runtime lineage containing unreviewed V15 behavior.

## Ready queues

Session A: finish `V2A-003b-R` SP2; `V2A-H6A-R` SP1; isolated `V2A-003X` SP2 DBOS reuse spike. After 003b-R lead acceptance: V2A-003c result fence, then durable worker service/client. Session A also owns current-tip local broker/admission revalidation; do not create a third general implementation lane for it.

Session B: `V2B-001` SP2 task-pool/version freeze; `V2B-002` SP3 calibration-only reviewer repair/freeze; `V2B-003a+H1` SP2 project-scoped provenance; `V2B-004a+H4` SP2 ActionEnvelope/ApprovalGrant/Receipt contracts. Session B hands central migration/API integration notes to Session A.

## Lead future lane

`ART-V30-PERSISTENT-OBJECTIVE-CONTRACT` was materially expanded in LEAD-022: immutable objective versions, trigger receipts, deterministic schedule occurrence/missed-run policy, MissionProposal admission boundary, authority monotonicity, V2.3 fair-share anti-amplification, governed-learning candidate/version boundary, restart/dedupe semantics, threat cases and acceptance scenarios. It remains drafting architecture, not V3 implementation/acceptance.

`ART-V30-LEARNING-GOVERNANCE`, `ART-V23-MULTIMISSION-OPS`, V1.8 recovery and V2.0 security/reliability remain active lead lanes.

## Human/live blockers

Cursor CLI authentication remains the immediate human-auth blocker for `ART-V10-WORKER-HEARTBEAT`: complete a live `cursor agent login` only while an actual waiter is active, then status/whoami must verify. G12 remote overlap requires fresh exact-route account/tier/zero-charge/quota/health evidence for two remote routes; public provider docs do not self-admit an account. Do not fabricate provider eligibility, cost, timing, worker activity or elapsed acceptance time.
