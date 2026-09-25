# SwarmAI AI-Native Redesign Plan

Status: planning only. This branch does not authorize implementation or deployment.

## Product thesis
SwarmAI is a cloud-first environment where autonomous persistent agents organize themselves around a user goal, use heterogeneous inference and tools, learn from evidence, and continue until the mission is verified complete or genuinely blocked.

Normal user flow: state goal -> choose template/blank swarm -> connect inference -> grant tools and resources -> start -> swarm plans/staffs/executes/reorganizes/learns/verifies -> user receives evidence and artifacts.

## AI-native planning rule
SwarmAI does not plan primarily as prose for humans. Canonical planning output is an executable artifact graph:

Goal -> outcome contract -> artifact DAG -> atomic artifact packets -> verified artifacts -> integration -> mission outcome.

Human-readable roadmaps are projections of that graph.

## Core definitions
- Agent: persistent person-like identity, independent of model, process, context window, and assignment.
- Execution: bounded attempt by an agent using a specific model/effort/tool configuration.
- Crew: optional emergent group collaborating on a shared subgoal.
- Swarm: population of agents pursuing the collective mission; crews are optional organization inside it.
- Mission: goal plus completion evidence, resource envelope, capabilities, and stop state.
- Artifact: smallest durable work/evidence unit another agent can consume without private context.
- Lesson: evidence-linked candidate or validated change to future behavior.
- Tool: bounded capability, native or MCP-backed.
- Inference profile: portable capability request resolved to endpoint/model/effort.

## Principles
1. Autonomous by default inside the mission envelope.
2. Artifact-first communication; chat is coordination, artifacts are durable work.
3. Weak-model executable packets.
4. Heterogeneous models and effort are normal.
5. SplitSignal is the reference inference integration, never a dependency.
6. Bring-your-own inference is core.
7. Cloud-first; browser closure must not stop work.
8. Persistent identities; ephemeral executions.
9. Context is attention, not memory.
10. Memory is layered and graph-addressable.
11. Learning requires evidence.
12. Tools include sandbox terminal, web, files/git, APIs, and MCP.
13. Measure model/effort/task/tool/personality/crew outcomes.
14. Optimize verified success per resource, not agent count.
15. Prefer deterministic code for deterministic work.
16. Reuse existing repository modules before adding parallel frameworks.

## Canonical planning files
- docs/redesign/AI_NATIVE_ARTIFACT_PROTOCOL.md
- docs/redesign/EPIC_ROADMAP.md
- docs/redesign/ARTIFACT_BACKLOG.yaml

## Worker selection
1. Load ARTIFACT_BACKLOG.yaml.
2. Select a ready artifact whose dependencies are accepted.
3. Read only listed inputs and dependency contracts.
4. Produce only listed outputs.
5. Run listed verification.
6. Record evidence.
7. Stop; do not opportunistically continue.

This is intentionally optimized for small local models with limited context.
