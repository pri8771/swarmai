# SwarmAI compact project memory

Curated 2026-09-21 after `LEAD-20260921-020`. `ARTIFACT_REGISTRY.json` is canonical; this is a compact orientation only. Read registry/state and unread messages before deeper evidence.

## Authority and operating model

Owner authorizes source implementation through V3.0. Major milestones: V1.7, V2.3, V3.0. Immediate target: a V2.0 implementation/artifact-complete candidate. Main merge, public release/deployment, additional spend/paid fallback and destructive actions remain separately gated. Live/time-bound acceptance is real wall-clock evidence and is never backfilled.

Management is artifact-oriented. ChatGPT owns architecture/contracts/research/decomposition/independent review. Cursor does most SP1-SP3 implementation/test work. Session A owns runtime/control-plane/distributed/recovery plus integration on `cursor/v2-runtime-lane` / `cursor/v2-integration`; Session B owns eval/knowledge/tools/product/beta on `cursor/v2-product-lane`. Shared API/store/routes/schemas/CLI/lockfile/migrations belong to Session A.

## Current source truth

Main remains `b9141fa3150f853586dede0334a47b344571bc16`. V1.4 base is `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea`.

Session A runtime tip: `7a2491a2840ef8381e275b05e11f3f76c7a522e6`; Actions `35550769734` green. V2 integration tip: `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code baseline `ee5a06612aa2e4409fa8bbfd1969225c16887615`; Actions `35550653160` green. Session B remains at `2c08f...`; no Session-B source commit/message was observed in LEAD-020.

Lead-reviewed Session-A packets:
- V2A-001 / `ART-V12-BROKER-CONTRACT` verified: governed project-scoped broker is injected in generic ProductStore execution; broker-required denial/missing/unregistered routes do not fall through to direct local inference.
- V2A-002 / `ART-V11-RESTART-EVIDENCE` verified: actual uvicorn PID stop/start and same durable mission reopened through HTTP and separate CLI.
- V2A-003a-R repair verified; durable schema migration/token lifecycle/recursive sensitive metadata foundation is valid, but the overall lease-fencing artifact remains drafting.
- V2A-003b changes required: claim must validate current mission/source/cancellation authority before mutation, renewal must check current worker project, and fixed 32-row scanning can HOL-block an eligible task.
- V2A-020a SP1 accepted: integration branch correctly contains only lead-reviewed V2A-001/V2A-002 lineage and excludes V15 ancestry with unreviewed 003b behavior. `ART-V20-INTEGRATED-CANDIDATE` remains drafting.
- V2A-H6A SP2 changes required: fixed DB credentials are removed and compose fails closed/private, but generated secret-bearing `.env` needs explicit owner-only permissions and `--force` must not masquerade as safe credential rotation for an initialized database volume.

## Acceptance/gate truth

V1.0 repair: candidate/security/evidence/runtime artifacts verified; worker-heartbeat artifact blocked because Cursor CLI auth/real authenticated receipts remain absent.

V1.1: all required artifacts are verified, including real process restart; the version artifact set has not been promoted as accepted.

V1.2: broker and provider eligibility verified. Provider ledger still has **0 admissible remote routes**; remote overlap blocked. Local fallback/admission reconciliation remain reviewable and need rebind/review against the verified broker.

V1.3: frozen qualification protocol accepted; screening matrix verified as 72 provisional n=5 cells across three local configs and S/M/L/XL. Task pool/version manifest not frozen; zero qualified cells; reviewer qualification drafting.

V1.4: graph/load work is offline preparation. Qualified-role manifest and live adaptive proof remain blocked on G12/G13. LIVE-142 is preregistered but not started; mandatory wall-clock observation remains future truth.

V1.5 implementation is active but `ART-V15-LEASE-FENCING` remains drafting. V1.6/V1.7 Session-B packets are ready but no Session-B source activity has been observed.

V2.0 integration has a clean drafting baseline (V2A-001/002 only). Foundation hardening remains drafting; do not wholesale-merge runtime lineage while unreviewed V15 behavior remains in its ancestry.

## Ready queues

Session A: `V2A-003b-R` SP2 claim/renew/expire repair; `V2A-H6A-R` SP1 secret-file/overwrite-safety repair; `V2A-003X` SP2 isolated DBOS reuse spike. After 003b-R review: V2A-003c result fence, then durable worker service/client.

Session B: `V2B-001` SP2 task-pool/version freeze; `V2B-002` SP3 calibration-only reviewer repair/freeze; `V2B-003a+H1` SP2 project-scoped provenance; `V2B-004a+H4` SP2 ActionEnvelope/ApprovalGrant/Receipt contracts. Session B must hand central migration deltas to Session A.

## Lead future lane

`ART-V30-LEARNING-GOVERNANCE` was materially advanced in LEAD-020: immutable proposal state machine, protected-authority boundaries, held-out contamination and multiple-comparison rules, preregistered statistical/selection discipline, deterministic canary rollback/fencing, drift/revalidation and explicit governance acceptance scenarios. It remains drafting future architecture, not V3 acceptance.

`ART-V23-MULTIMISSION-OPS`, V1.8 recovery and V2.0 security/reliability artifacts remain active lead lanes.

## Human/live blockers

Cursor CLI authentication remains the immediate human-auth blocker for `ART-V10-WORKER-HEARTBEAT`: complete a live `cursor agent login` only when an actual waiter is active, then status/whoami must verify. G12 remote overlap requires fresh exact-route account/tier/zero-charge/quota/health evidence for two remote routes; public provider docs do not self-admit an account. Do not fabricate provider eligibility, cost, timing, worker activity or elapsed acceptance time.
