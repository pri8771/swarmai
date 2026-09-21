# SwarmAI artifact-derived execution queue — V2 acceleration

Canonical state: `ARTIFACT_REGISTRY.json`. Detailed packet contracts: `WORKER_PACKET_BACKLOG.md`. Owner authorizes source implementation through V3.0; immediate target is a V2.0 implementation/artifact-complete candidate. Main merge/public release/additional spend remain separately gated.

## Current reviewed source truth

- Session A runtime tip observed: `37f95fe63a1bf451f5dad4075be143cfa145e975f`; Actions `35549624046` green.
- Session B product lane: `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea`; no new source activity observed this heartbeat.
- Integration lane: `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea`; no V2 reviewed commits integrated yet.
- Main unchanged: `b9141fa3150f853586dede0334a47b344571bc16`.

## Independently reviewed this heartbeat

### Verified

- **V2A-001 / ART-V12-BROKER-CONTRACT / SP2** — `c3df96ef074568e7a92dd2f6c6bfd070fe5374f3`; CI `35548643473`. Generic ProductStore execution now uses the governed project-scoped broker; broker-required denial/missing/unregistered route does not fall through to direct `local_chat`.
- **V2A-002 / ART-V11-RESTART-EVIDENCE / SP1** — source `48a02e3daae13f8fb569225e2d030097229f4780`, evidence `ee5a06612aa2e4409fa8bbfd1969225c16887615`; CI `35549111809`. Real uvicorn process restart and durable same-mission reopen proved.

### Changes required

- **V2A-003a / ART-V15-LEASE-FENCING / SP2** — source `630ab780ab45858c5dad4075be143cfa145e975f`, evidence `37f95fe63a1bf451f5d513855a7fcf1bb37d3d9b`; CI `35549624046` green. Schema/repositories are useful, but artifact remains drafting because:
  1. representative legacy-row migration test does not actually upgrade a populated previous Alembic schema;
  2. V2A-H2 revoke/rotation lifecycle evidence is missing;
  3. token-sensitive free-form metadata validation is top-level only.

## Session A — runtime/control plane/integration

Branch `cursor/v2-runtime-lane`; integration owner `cursor/v2-integration`.

Ready now:
1. **V2A-003a-R / ART-V15-LEASE-FENCING / SP1** — repair true legacy migration proof + token rotate/revoke + recursive/typed token-sensitive metadata boundary.
2. **V2A-H6A / V2 hardening + V1.8/V1.9 deployment artifacts / SP2** — remove unsafe normal DB secret/default assumptions; private/operational default; compose health smoke.
3. **V2A-020a / ART-V20-INTEGRATED-CANDIDATE / SP1** — start integration lane with only lead-verified V2A-001/V2A-002 source/evidence; full available integrated CI; do not integrate unreviewed V2A-003a.

After V2A-003a-R lead review: V2A-003b+H3 atomic eligible claim/renew/expire -> V2A-003c result fence -> V2A-004 durable worker protocol -> DBOS reuse spike -> site epoch/backup/restore.

## Session B — evaluation/knowledge/tools/product/beta

Branch `cursor/v2-product-lane`. Keep off Session-A-owned API/store/routes/schemas/CLI/lockfile/migrations.

Ready now:
1. **V2B-001 / ART-V13-TASK-POOL / SP2** — freeze calibration vs held-out task/version manifest. No counted qualification before lead freeze.
2. **V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3** — calibration-only benchmark/scorer repair and freeze; no qualification claim.
3. **V2B-003a+H1 / ART-V16-PROVENANCE / SP2** — versioned project-scoped provenance/permission labels/tombstones and two-project non-leak tests; hand central migration delta to Session A.
4. **V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2** — ActionEnvelope/ApprovalGrant/ActionReceipt contracts; mandatory operational project binding and no demo default.

Then: permission-first retrieval/supersession -> ToolGateway/effect-key semantics -> extension manifest/beta evidence.

## Earlier acceptance gates remain honest

- **V1.0:** all repair artifacts except `ART-V10-WORKER-HEARTBEAT` verified. Heartbeat still blocked on actual Cursor CLI authentication and real receipts.
- **V1.1:** all required artifacts now verified, including process restart; version artifact set not promoted to accepted in this heartbeat.
- **V1.2:** broker + provider eligibility verified; 0 admissible remote routes means `ART-V12-REMOTE-OVERLAP` remains blocked. Local fallback/reconciliation remain reviewable.
- **V1.3:** protocol accepted; screening verified provisional; task pool not frozen, zero qualified cells, reviewer benchmark drafting.
- **V1.4:** role manifest/live adaptive proof blocked on G12/G13; logical load is offline-only; LIVE-142 not started.

Do not call blocked live/time artifacts accepted merely because later implementation continues.

## Human/live blockers

- `ART-V10-WORKER-HEARTBEAT`: `cursor agent status/whoami` not authenticated; only exact login/passkey/MFA/consent step may require operator involvement.
- `ART-V12-REMOTE-OVERLAP`: zero admitted remote routes; fresh exact account/model zero-charge/auth/quota/health evidence required before any live remote proof.
- LIVE-142 and later reliability windows: real wall-clock evidence only; no acceleration or backfill.

## Lead lane

Lead continues architecture/research/review while workers implement. `ART-V23-MULTIMISSION-OPS` was advanced with durable queue state, weighted-deficit fairness/anti-gaming, `DispatchIntent` reservation compensation, restart/scheduler-epoch fencing, decision receipts and a proposed preregistered fairness acceptance design. V1.8 recovery, V2.0 security/reliability and V3 objective/learning artifacts remain parallel lead work.

## Worker directive

Read `LEAD-20260921-019` plus the canonical registry/backlog. Claim one ready packet with artifact ID, intended transition, base SHA/worktree and first test. Return exact source/evidence SHA and checks. Do not self-accept. If human auth/provider eligibility blocks a packet, switch to another dependency-ready packet rather than idling.
