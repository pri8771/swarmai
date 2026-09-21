# SwarmAI artifact-derived execution queue — V2 acceleration

Canonical state: `ARTIFACT_REGISTRY.json`. Detailed packet contracts: `WORKER_PACKET_BACKLOG.md`. Owner authorizes source implementation through V3.0; immediate target is a V2.0 implementation/artifact-complete candidate. Main merge/public release/additional spend remain separately gated.

## Current reviewed source truth

- Session A runtime: `7a2491a2840ef8381e275b05e11f3f76c7a522e6`; Actions `35550769734` green.
- V2 integration: `9ce727842446b98cfa55c28c7e70808f57f17d7b`; code baseline `ee5a06612aa2e4409fa8bbfd1969225c16887615`; Actions `35550653160` green.
- Session B product lane: `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea`; no new source activity/message observed in LEAD-020.
- V1.4 base: `2c08f968f301d3be80f8d0b17eb98b98fb2cb8ea`; main remains `b9141fa3150f853586dede0334a47b344571bc16`.

## Independently reviewed in LEAD-020

### Accepted packet

- **V2A-020a / ART-V20-INTEGRATED-CANDIDATE / SP1** — receipt `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code `ee5a06612aa2e4409fa8bbfd1969225c16887615`, CI `35550653160` green. Correctly integrated only lead-reviewed V2A-001/V2A-002 lineage and excluded unreviewed V15 ancestry. Artifact remains `drafting`; this proves only a clean reviewed integration starting point.

### Changes required

- **V2A-H6A / ART-V20-FOUNDATION-HARDENING / SP2** — implementation `77ef7e4c1675b74dbfcdeba27f8c955ae39f119c`, current tip `7a2491a...`, CI `35550769734` green. Fixed DB credential/default and private/fail-closed compose behavior are good. Repair still required because generated `deploy/compose/.env` contains a credential without explicit owner-only permissions, and `--force` must not be treated as safe rotation for an initialized Postgres volume. New packet: V2A-H6A-R SP1.

Prior verified/changes-required packet decisions remain as recorded in `WORKER_PERFORMANCE.json` and `WORKER_PACKET_BACKLOG.md`.

## Session A — runtime/control plane/integration

Branches: `cursor/v2-runtime-lane` and integration-owned `cursor/v2-integration`. Session A owns shared API/store/routes/schemas/CLI/lockfile/migrations.

Ready now:
1. **V2A-003b-R / ART-V15-LEASE-FENCING / SP2** — validate mission/source/cancellation authority before lease mutation; renewal must check current worker project; remove the 32-row HOL correctness limit; direct regressions and exact-tip CI.
2. **V2A-H6A-R / ART-V20-FOUNDATION-HARDENING / SP1** — secret-bearing compose env owner-only permissions plus safe/explicit fresh-config overwrite semantics; preserve fail-closed/private behavior and rebind evidence.
3. **V2A-003X / ART-V15-ARCH / SP2** — isolated DBOS reuse spike against actual pinned version/API; restart/duplicate/stale-fence evidence and ADR recommendation only, no production migration.

After V2A-003b-R lead review: V2A-003c result-acceptance fencing -> V2A-004 durable worker service/client. Integrate only lead-reviewed slices; do not wholesale-merge runtime ancestry containing unreviewed V15 behavior.

## Session B — evaluation/knowledge/tools/product/beta

Branch `cursor/v2-product-lane`. Keep off Session-A-owned shared API/store/routes/schemas/CLI/lockfile/migrations; hand migration deltas to Session A.

Ready now:
1. **V2B-001 / ART-V13-TASK-POOL / SP2** — freeze calibration/held-out IDs/hashes and source/license/size-classifier/scorer/prompt/tool/model-config manifest. No counted held-out qualification before lead freeze.
2. **V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3** — calibration-only reviewer benchmark/scorer repair and freeze; no qualification claim or held-out contamination.
3. **V2B-003a+H1 / ART-V16-PROVENANCE / SP2** — versioned project-scoped provenance/permission labels/tombstones and two-project non-leak tests; Session A owns central migration integration.
4. **V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2** — ActionEnvelope/ApprovalGrant/ActionReceipt contracts with mandatory operational project and exact operation/destination/payload binding; no production demo default.

Then: permission-first retrieval/supersession -> ToolGateway/effect-key semantics -> extension manifest/beta evidence.

## Earlier acceptance gates remain honest

- **V1.0:** all repair artifacts except `ART-V10-WORKER-HEARTBEAT` verified. Heartbeat blocked on actual Cursor CLI authentication and authenticated receipts.
- **V1.1:** all required artifacts verified, including real process restart; version set not promoted/accepted.
- **V1.2:** broker + provider eligibility verified; 0 admissible remote routes means `ART-V12-REMOTE-OVERLAP` remains blocked. Local fallback/reconciliation remain reviewable and need rebind/review.
- **V1.3:** protocol accepted; screening verified provisional; task pool not frozen, zero qualified cells, reviewer benchmark drafting.
- **V1.4:** role manifest/live adaptive proof blocked on G12/G13; logical load remains offline-only; LIVE-142 not started.

Do not call blocked live/time artifacts accepted because later implementation proceeds.

## Human/live blockers

- `ART-V10-WORKER-HEARTBEAT`: `cursor agent status/whoami` not authenticated; only exact login/passkey/MFA/consent may require operator involvement.
- `ART-V12-REMOTE-OVERLAP`: zero admitted remote routes; exact account/model zero-charge/auth/quota/health evidence required before live proof.
- LIVE-142 and later reliability windows: real wall-clock evidence only; no acceleration or backfill.

## Lead lane

`ART-V30-LEARNING-GOVERNANCE` was materially advanced in LEAD-020 with immutable proposal states, protected-authority boundaries, held-out contamination/selection controls, frozen statistical rules, deterministic rollback/fencing, drift revalidation and explicit acceptance scenarios. It remains drafting future architecture; no V3 acceptance claim.

Next lead work: map V30 learning authority to persistent-objective scope and V2.3 scheduler/fairness invariants, while continuing V2.0 security/reliability review as integration grows.

## Worker directive

Read `LEAD-20260921-020`, the canonical registry and backlog. Claim a dependency-ready packet with artifact ID, intended transition, base SHA/worktree and first test. Return exact source/evidence SHA and checks; do not self-accept. If auth/provider/live gates block one packet, switch to another ready packet rather than idling.
