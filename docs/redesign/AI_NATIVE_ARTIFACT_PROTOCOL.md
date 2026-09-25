# AI-Native Artifact Execution Protocol

## Primitive
The durable unit of work is an artifact, not a conversation or human-oriented ticket.

Mission -> Epic -> Capability artifact -> Atomic artifact packet -> Evidence artifact.

A packet is too large if its worker must invent architecture, choose among incompatible interfaces, perform open-ended research, or edit unrelated modules.

## Atomic packet schema
Every packet must define:
- id and epic
- one-sentence goal and why
- dependencies
- exact inputs
- exact outputs
- allowed and forbidden changes
- explicit steps
- exact tests/assertions
- observable acceptance
- evidence location
- rollback
- size: xs or s

## Weak-model sizing
XS:
- one behavior;
- normally one production file plus one focused test;
- at most one new public interface;
- no schema + API + UI combination;
- no open-ended design.

S:
- one behavior crossing at most two tightly coupled production files;
- interface already frozen by accepted dependencies;
- focused tests.

If larger, split it before implementation.

## Worker algorithm
1. Read packet.
2. Confirm dependencies are accepted.
3. Open only required inputs.
4. Implement the smallest change satisfying the contract.
5. Run focused verification.
6. Fix only packet-caused failures.
7. Run listed regression check.
8. Write evidence.
9. Stop.

Never refactor neighboring code or start the next packet.

## AI-native planning
Planning agents emit a graph. Each node declares artifact type, producer capability, consumers, prerequisites, completion predicate, evidence, and whether it is parallel-safe. Edges represent real data/interface dependencies.

Prefer parallel branches after contracts freeze.

Artifact types: contract, migration, adapter, service, tool, ui, eval, fixture, evidence, template, docs.

## Context bundle
A packet should run without loading the repository or chat history. Bundle only:
- packet definition;
- direct dependency contracts;
- exact target files;
- focused tests;
- architecture summary <= 1,500 tokens when needed.

## Communication
Durable coordination uses artifacts plus concise events:
started, blocked, artifact_ready, evidence_ready, rejected, accepted, help_requested, crew_joined, crew_left, replanning_requested.

A message never satisfies a dependency. An accepted artifact does.

## Memory
Working context is disposable; identity is persistent.

Layers:
1. raw/event store: tagged observations, transcripts, tool outputs, provenance;
2. long-term knowledge: facts, decisions, lessons, relationships linked to evidence;
3. medium/index memory: compact pointers describing what is known and where;
4. task state: commitments, blockers, active artifacts;
5. working context: dynamically assembled attention view;
6. archive: cold retrievable material.

Context pressure first triggers retrieval/compaction/refresh. It does not automatically create a new person.

## Learning
Experience -> outcome -> candidate explanation -> candidate lesson -> validation -> application -> measured result.

Each meaningful attempt records task family, agent, behavioral profile, provider/model/version when known, requested/applied effort, tokens when known, latency, tools, collaborators, outcome, verification, and cost when known.

## Experimenter
Persistent about the challenge; flexible about method.
hypothesis -> attempt -> evidence -> update search state -> materially different next attempt.
Identical retries require a reason such as reproducibility/noise. Independent hypotheses may be parallelized within mission resources.

## Autonomous organization
Agents may recruit available agents, spawn when allowed, form/dissolve crews, change assignments, request permitted inference profiles, run experiments, and publish findings. Runtime supplies mechanics and enforces the mission envelope rather than micromanaging organization.

## Minimal hard boundaries
Only five concepts are invariant:
- mission;
- resources;
- capabilities;
- evidence;
- stop.

Templates and personalities cannot override them.

## Inference
Agent identity never equals model identity. SwarmAI requests an inference profile; an adapter resolves it. SplitSignal is the reference adapter; supported BYO/OpenAI-compatible endpoints remain portable.

## Tools and MCP
All tools register through one capability registry with name, schemas, side-effect class, permission scope, execution location, timeout, and provenance behavior. MCP is a first-class adapter into the same registry. Native and MCP tools look equivalent after registration. Terminal uses an isolated sandbox by default. Web search/browse is a tool capability.

## Cloud-first
Durable state lives outside worker memory. Worker/browser failure cannot erase agent identity, mission state, artifacts, leases, memory, lessons, analytics, approvals, or evidence.

## Verification
Agent self-report is not completion. Use task-appropriate evidence: tests, API response, diff, schema validation, health check, benchmark, external retrieval, or independent verifier.

## Planning completion
A plan is complete when every epic has an exit predicate, every atomic artifact has exact outputs and verification, dependencies are acyclic, unknown design choices are isolated as decision artifacts, and no implementation packet depends on an unwritten convention.
