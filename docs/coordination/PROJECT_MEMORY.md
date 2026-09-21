# SwarmAI compact project memory

Curated 2026-09-21 after `LEAD-20260921-019`. `ARTIFACT_REGISTRY.json` is canonical; this is only a compact orientation. Read registry/state and unread messages before deeper evidence.

## Authority and operating model

Owner authorizes source implementation through V3.0. Major milestones: V1.7, V2.3, V3.0. Immediate target: a V2.0 implementation/artifact-complete candidate. Main merge, public release/deployment, additional spend/paid fallback and destructive actions remain separately gated. Live/time-bound acceptance is real wall-clock evidence and is never backfilled.

Management is artifact-oriented. ChatGPT owns architecture/contracts/research/decomposition/independent review. Cursor does most SP1-SP3 implementation/test work. Session A owns runtime/control-plane/distributed/recovery plus integration on `cursor/v2-runtime-lane` / `cursor/v2-integration`. Session B owns eval/knowledge/tools/product/beta on `cursor/v2-product-lane`. Shared API/store/routes/schemas/CLI/lockfile/migrations belong to Session A.

## Current refs and reviewed progress

Main remains `b9141fa3150f853586dede0334a47b344571bc16`; V1.4 base and both V2 integration/product branches currently start at `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea`. Session A runtime tip observed this heartbeat: `37f95fe63a1bf451f5dad4075be143cfa145e975f`; CI `35549624046` is green. No Session B source commit was observed in this heartbeat.

Lead independently verified:
- `ART-V12-BROKER-CONTRACT`: source `c3df96ef074568e7a92dd2f6c6bfd070fe5374f3`, CI `35548643473`. ProductStore generic execution now injects the governed project-scoped broker; broker-required missing/denied/unregistered paths fail closed instead of falling through to direct local inference.
- `ART-V11-RESTART-EVIDENCE`: source `48a02e3daae13f8fb569225e2d030097229f4780`, evidence `ee5a06612aa2e4409fa8bbfd1969225c16887615`, CI `35549111809`. Actual uvicorn PID stop/start, first process exit, same durable mission ID/status/disk hash reopened through HTTP and separate CLI.

Session A also produced V2A-003a durable worker schema/repositories at `630ab780ab45858c5dad4075be143cfa145e975f`, evidence tip `37f95fe63a1bf451f5d513855a7fcf1bb37d3d9b`. Lead review requested changes; `ART-V15-LEASE-FENCING` stays drafting. Useful schema/repo work exists, but the current “legacy migration” test creates current metadata then inserts nullable legacy-shaped rows instead of upgrading a populated previous Alembic schema. V2A-H2 also lacks revoke/rotation lifecycle proof, and token-sensitive free-form metadata needs a recursive/typed boundary.

## Gate truth

V1.0 repair: candidate/security/evidence/runtime artifacts verified; worker-heartbeat artifact blocked because `cursor agent` auth/real receipts remain absent.

V1.1: all required artifacts are now verified, including real process restart, but version artifacts have not been promoted to accepted as a set.

V1.2: broker and provider-eligibility artifacts verified. Provider ledger still has **0 admissible remote routes**; remote overlap blocked. Local fallback/admission-reconciliation artifacts remain reviewable and need rebind/review against the verified broker.

V1.3: frozen qualification protocol accepted; screening matrix verified as 72 provisional n=5 cells across three local configs and S/M/L/XL. Task-pool/version manifest not frozen; zero qualified cells; reviewer benchmark still drafting.

V1.4: graph/load work remains offline preparation. Qualified-role manifest and live adaptive proof blocked on G12/G13. LIVE-142 is preregistered but not started; mandatory wall-clock observation remains future truth.

V1.5 implementation is active. Durable lease/fencing foundation needs V2A-003a-R repair before atomic claim/renew/expire and result fencing. V1.6/V1.7 implementation packets are ready for Session B but no product-lane source activity was observed yet.

## Current ready queues

Session A: `V2A-003a-R` SP1 (true legacy migration + token rotate/revoke + nested metadata boundary), `V2A-H6A` SP2 (deployment secret/runtime default hardening), `V2A-020a` SP1 (start V2 integration with verified V2A-001/V2A-002 only). Then V2A-003b/c and durable worker protocol.

Session B: `V2B-001` SP2 task-pool/version freeze, `V2B-002` SP3 calibration-only reviewer benchmark repair/freeze, `V2B-003a+H1` SP2 project-scoped provenance, `V2B-004a+H4` SP2 ActionEnvelope/ApprovalGrant/ActionReceipt contracts.

## Lead future lane

`ART-V23-MULTIMISSION-OPS` was materially advanced: durable project/mission queue state, weighted-deficit fairness, anti-gaming invariants, bounded urgency/aging, cross-resource `DispatchIntent` compensation, scheduler-epoch fencing, explain receipts and proposed preregistered fairness metrics. It remains drafting; no V2.3 acceptance claim.

## Human/live blockers

Cursor CLI authentication remains the only immediate human-auth blocker for `ART-V10-WORKER-HEARTBEAT`: complete a live `cursor agent login` only when an actual CLI waiter is active, then status/whoami must verify. G12 remote overlap requires fresh exact-route account/tier/zero-charge/quota/health evidence for two remote routes; public provider docs do not self-admit an account. Do not fabricate provider eligibility, cost, timing or worker activity.
