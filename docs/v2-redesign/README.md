# SwarmAI V2 Redesign — canonical execution plan

Status: PLANNING ONLY. This branch does not authorize deployment, paid inference, destructive actions, or main-branch merge.

## Product sentence
SwarmAI is a cloud-first environment where persistent autonomous agents organize around a user goal, use heterogeneous inference models and tools, form/dissolve crews, learn from verified outcomes, and continue until the mission is verified complete or genuinely blocked.

## Non-negotiable properties
1. Goal-first UX; normal users do not design workflow graphs.
2. Agent != model. Identity/memory/personality/experience persist while model and effort may change per assignment.
3. Crew = agents collaborating on a shared subgoal. Swarm is not a hierarchy of crews.
4. Swarm = population of agents pursuing the collective mission and free to reorganize within available capabilities/resources.
5. Mixed-model by default.
6. Inference-agnostic core. SplitSignal is reference/first-class, never mandatory.
7. Real tools: terminal/sandbox, filesystem, web, Git, APIs, MCP.
8. Layered memory: working context, task state, medium/index, durable memory, artifacts, raw/archive, typed links.
9. Evidence-backed learning at agent/crew/domain/swarm scopes.
10. Experimenter behavioral archetype: persistent hypothesis/attempt loop with verified success.
11. Context is attention, not identity; refresh does not create a new agent.
12. Token/resource efficiency is measured and optimized.
13. Cloud-first durable execution.
14. MCP first-class.
15. Analytics join task + agent/profile + model/effort + tools + tokens/cost/latency + verified outcome.
16. Thin hard control plane: mission, resources, capabilities, evidence, pause/stop.
17. Existing working code is donor code; audit/reuse before rewriting.

## Execution hierarchy
Epic -> Task -> Atomic Subtask (AS).

An AS is the unit for a weak local model. It must have one outcome; normally touch <=3 implementation files plus tests/docs; require no unresolved product decision; list exact inputs/outputs/tests; have binary acceptance; be independently commit-able.

If an AS becomes ambiguous, STOP and create a blocker note. Do not expand scope.

## Worker reading order
1. this file
2. PACKET_STANDARD.md
3. ARCHITECTURE_AND_CONTRACTS.md
4. only the assigned epic/backlog section
5. IMPLEMENTATION_MAP.json after E00 creates it
6. exact source/tests named by the AS

## Files
- PACKET_STANDARD.md
- ARCHITECTURE_AND_CONTRACTS.md
- BACKLOG_A_FOUNDATION.md — E00-E04
- BACKLOG_B_INTELLIGENCE.md — E05-E09
- BACKLOG_C_PRODUCT.md — E10-E14
- ACCEPTANCE_MATRIX.md

## Epic order
E00 baseline audit/donor map
E01 core domain contracts
E02 cloud control plane/durable mission state
E03 inference abstraction: SplitSignal + BYO
E04 persistent person/agent runtime
E05 memory graph/context lifecycle
E06 evidence-backed learning
E07 tool runtime/sandbox/web/Git/MCP
E08 communication/crews/shared artifacts
E09 autonomous organization/spawning
E10 analytics/resource intelligence
E11 templates/customization
E12 cloud UX/API
E13 reliability/security/tenancy/operations
E14 E2E evals/migration/release readiness

E00 first. E01-E03 may proceed in parallel after E00. Later epics start when their listed dependencies pass.

## DONE
Subtask: specified tests pass + commit exists.
Task: all AS complete + task acceptance passes.
Epic: acceptance matrix row passes.
Project: E14 real E2E passes through SplitSignal and at least one independent BYO inference endpoint, durable cloud recovery, real tools, and verified output.

Mocks are development evidence, not final live acceptance.
