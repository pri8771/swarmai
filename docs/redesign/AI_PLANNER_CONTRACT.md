# AI Planner Contract

Purpose: convert a user goal into an execution graph optimized for AI workers, not a human project-management ceremony.

## Planner output
The planner emits:
1. Mission outcome contract.
2. Artifact DAG.
3. Atomic packet definitions.
4. Verification graph.
5. Resource/capability hypotheses.
6. Replan triggers.

It may also render a human summary, but that summary is not canonical.

## Planning algorithm
1. Parse the goal into externally observable completion conditions.
2. Identify required final artifacts/evidence.
3. Work backward from each final artifact to prerequisite artifacts.
4. Isolate uncertain design choices as decision/experiment artifacts.
5. Freeze shared interfaces before parallel implementation branches.
6. Split implementation until every leaf passes XS/S packet rules.
7. Mark genuinely independent nodes parallel-safe.
8. Attach required capabilities, not named workers.
9. Attach inference needs as capability profiles, not model brands unless user pinned one.
10. Attach exact verification to every leaf.
11. Add integration artifacts only where outputs must combine.
12. Validate DAG, packet size, output collisions and missing evidence.
13. Start with the smallest useful population; let execution recruit/reorganize as evidence appears.

## AI-efficiency heuristics
Prefer:
- structured schemas over prose handoffs;
- exact file/range inputs over whole-repo context;
- fixtures over repeated explanation;
- deterministic scripts for deterministic transformations;
- reusable artifacts over repeated inference;
- parallel branches after contract freeze;
- one producer per exclusive artifact;
- independent verification where outcome warrants it;
- medium-memory pointers instead of repeatedly loading raw history;
- cheap/small inference for narrow validated task families;
- stronger inference only when task evidence justifies it.

Avoid:
- meetings as default synchronization;
- fixed human roles when capabilities are enough;
- serial chains caused only by project-management convention;
- asking every agent to read the full mission history;
- copying the same context into every worker;
- spawning workers without an independent subproblem;
- using LLM calls for queueing, counters, permission checks, parsing, or other deterministic operations;
- treating more tokens/agents/effort as inherently better.

## Replanning
Replan only when an event invalidates the active graph:
- artifact rejected;
- required capability unavailable;
- dependency assumption disproven;
- new independent work discovered;
- repeated failure changes the hypothesis space;
- user changes mission/resources/capabilities;
- verification reveals missing work.

A replan creates a new graph version. Accepted artifacts remain reusable unless explicitly invalidated.

## Planning quality checks
Reject a plan if:
- a leaf says only "implement X" without exact output/test;
- a worker must choose architecture that should have been a decision artifact;
- multiple leaves write the same exclusive output without integration contract;
- success is agent self-report;
- provider/model names are hard-coded without a user/template requirement;
- a crew hierarchy is mandatory without task evidence;
- context refresh is modeled as creation of a new agent;
- the plan assumes browser/process memory is durable.

## Example decomposition
Bad:
"Build MCP support."

Better:
1. Define MCP-to-ToolCapability mapping contract.
2. Create fake MCP server fixture.
3. Discover one fake tool and register it.
4. Invoke registered fake tool.
5. Normalize result to ToolReceipt.
6. Verify native and MCP callers use the same registry path.

Each numbered item can be independently implemented and tested by a small worker.
