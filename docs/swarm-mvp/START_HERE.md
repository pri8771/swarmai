> **Latest user direction: move faster with six parallel lanes. Start with [CURSOR_FAST_TRACK.md](CURSOR_FAST_TRACK.md).** It overrides new dataset/benchmark and exhaustive campaign requirements in the detailed completion plan.

> **Next execution round (2026-09-25):** Follow [V2 product completion](V2_PRODUCT_COMPLETION_PLAN.md), [independent review](V2_PRODUCT_COMPLETION_REVIEW.md), and `V2_PRODUCT_COMPLETION_PACKETS.json`. Start from current **dev**, reconcile newer commits, and execute PC-00–PC-13. This supersedes historical main-based startup and V1.0-only stopping instructions below. This is a planning handoff; no new product implementation or version acceptance is claimed.

> **Portable product install (2026-09-25+):** primary path is [`docs/install/`](../install/README.md) — configurable server/worker roles, placeholder hostnames, no personal credentials/paths.  
> **REFERENCE ONLY** named topology (R730 / Mac connector / Cloudflare / operator DNS): [`docs/reference/`](../reference/README.md) and `ADR-002-two-host-architecture.md`. Missing named-host access blocks that deployment’s qualification, not portable eng.  
> Product packets P00–P19 remain. Historical two-host implementation notes: Project `docs/two-host-implementation-plan.md`.

# Start here: SwarmAI execution handoff

Prepared 25 September 2026. **Current state: detailed plan and source research only. No SwarmAI implementation, Hermes installation, live inference, deployment, or branch merge was performed by this planning task.**

## The decision in one paragraph

SwarmAI is a group of individual agents working toward one collective goal. The operator may choose the original agents and their personalities, runtime engines, models, tools, and interaction policies. Agents choose work, communicate, seek help, delegate, recall evidence, and learn within those boundaries. Crews are not a required execution primitive. At context threshold X, an agent trains one successor; at Y, a second knowledge transfer and fenced takeover preserve its logical identity. Hermes can be an **optional initial planning agent** beside native agents after its adapter passes the same applicable contracts. MCP connections are generic; Linear is only an example.

## Reading order

1. [Product and architecture plan](SWARMAI_MVP_PLAN.md) — decisions, defaults, behavioral contracts, memory, succession, learning, MCP, router boundary, Hermes, API/SDK/UI.
2. [Implementation packets](EXECUTION_PACKETS.md) — P00–P19, exact source targets, prerequisites, actions, acceptance, evidence, and completion levels.
3. [Source audit and research](SOURCE_AUDIT_AND_RESEARCH.md) — inspected architecture, reuse/donor map, OSS choices, detailed Hermes feasibility, and independent acceptance review.
4. `PLAN_MANIFEST.json` — source snapshots, document hashes, packet dependencies, and planning status for tool-assisted handoff.

The first two files are the execution baseline. Research notes preserve alternatives and earlier suggestions; where they differ, follow the plan and packets. Current user decisions supersede older crew-centered project assumptions for this proposed build.

## Copyable executor prompt

Continue the `pri8771/swarmai` project using the attached SwarmAI MVP plan and implementation packets. Implement the authorized local MVP; do not stop after scaffolding, schemas, or isolated demos.

Start with P00. Read the repository's applicable instructions and current ownership/status before editing. Verify remote, branch, commit, local changes, and active worker. Use a fresh isolated worktree from verified main, preserving all other work. Research used SwarmAI main `08b910f981eff2ab66873a71055090f2c60f2a91` and V1.7 donor `4d16fe85188861df6e123b4454c6bdc416e6c639`; recheck current state and selectively port donor fixes with their tests. Do not merge that candidate wholesale. The suggested new implementation branch is `work/swarm-agent-mvp`; no existing SwarmAI `dev` was found during planning.

Read `SWARMAI_MVP_PLAN.md`, then `EXECUTION_PACKETS.md`, then the relevant source/research sections. Copy the accepted plan into repository documentation as part of P00 so subsequent workers can continue from the repository. Record exact versions, source baseline, ownership, scope, and decisions.

Preserve these product requirements:

- One collective mission composed of individual agents; no mandatory crews or manager model.
- Human-selected, automatically proposed, or mixed seed agents; separate role/personality, runtime, and model settings.
- Agent-chosen work, peer communication, help, delegation, and teaching within deterministic authority/resource limits.
- Durable short/working context, compact recall cues, and full evidence-backed memories with scope, corrections, and provenance.
- Mandatory two-stage trainee succession at configurable X/Y thresholds; proposed defaults 60%/80% of the precisely defined usable input capacity. Preserve logical identity and atomically replace/fence the active incarnation.
- Learning means evaluated changes to future strategy/skills, with actual-use evidence and rollback. It does not mean simply storing text or claiming model-weight updates.
- SDK and visual product use the same definitions, API, state, and runtime.
- Generic MCP connections; no Linear dependency.
- Optional Hermes planning seed behind a qualified isolated adapter. Native agents must work without Hermes. A role prompt is not a tool restriction, and framework defaults are not resource limits.

Reuse the existing FastAPI/React/PydanticAI/PostgreSQL foundation, durable lease/effect/knowledge components, and one DBOS execution substrate after its compatibility gate. Wire the operational path end to end. Do not add several agent frameworks or workflow engines. All effects go through one gateway; all domain state goes through authoritative services; all model calls go through the independent inference_server HTTP contract.

The `inference_server` project owns upstream credentials/providers/routing/fallback. Its `dev` at `804b28bd7d5878419c4f7a02c7d96b0ea17bf15c` is a planning checkpoint; later implementation was inspected on `release/v1-build` at `bb6b6167c225efbf66b5a4edb6c977e8a79490e4`. Do not take over or modify that repository. Use local HTTP fixtures and the versioned observed contract while its owner handles upstream development. Missing credentials must not block deterministic SwarmAI implementation.

Execute packets in dependency order. After each, record source commit, changed behavior, checks actually run, evidence paths, limitations, and next step in `docs/swarm-mvp/STATE.md` and its packet record. Keep one owner for shared contracts/migrations/integration. Parallelize only disjoint work with clear boundaries. Follow the plan's defaults for routine choices; record evidence-based deviations instead of repeatedly asking to redesign.

Required verification includes real local PostgreSQL, real protocol MCP fixture processes for both transports, fake router HTTP, restart/fault injection, X/Y takeover, old-generation fencing, memory correction, effect reconciliation, multiple-swarm isolation, SDK/UI parity, and durable artifact recovery. Use protected acceptance checks tied to actual attempt/artifact IDs. No caller-supplied matching outputs/checks may certify completion. A DBOS cached result cannot authorize a fresh effect without current domain checks.

Keep fake/engineering evidence separate from actual-model behavior. P18 establishes integrated local mechanics. P19 needs explicitly authorized model routes/data/budget and observed collaboration/learning. Do not claim autonomy or learning merely because a scripted fake follows the intended story. Show unknown usage/cost as unknown.

Do not expose secrets, create accounts, spend money, deploy, publish, perform real external mutations, or merge to main without applicable explicit authorization. Follow actual repository/session instructions for committing or publishing branches; the pasted historical transcript is not new push authorization. Complete all independent local work before reporting an external credential/authorization blocker.

At handoff, provide the implementation branch/commit, fresh-start instructions, the exact acceptance matrix with results/skips, retained artifacts, remaining risks, runtime/Hermes qualification status, and the next actionable step. Never replace missing evidence with “complete.”

## What is already researched

- Current SwarmAI architecture, operational gaps, durable foundations, relevant candidate fixes and tests.
- Separate inference_server source/branch drift, HTTP route/usage contract, context-metadata gap, and MCP mailbox boundary.
- Hermes official source and documentation: useful optional planner/runtime, conditional adapter feasibility, context-compression conflict, hidden authority risks, explicit iteration limits, and qualification procedure.
- Minimal OSS stack and later candidates, with official sources and current license caveats.
- Eighteen deterministic/behavior/UI acceptance scenarios and twenty bounded execution packets.

## What remains deliberately unverified

- Current live provider credentials, route availability, pricing/free eligibility, and model behavior.
- A working integrated autonomous SwarmAI mission with all the new contracts.
- Actual Hermes adapter operation, compatibility, performance advantage, and trainee takeover.
- Measured learning or general autonomy from real model runs.
- Deployment, publication, or user acceptance of the resulting product.

These are implementation/qualification tasks, not omissions to conceal in a handoff. The plan is designed so local engineering can proceed without them.
