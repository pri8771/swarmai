# SwarmAI Redesign Epic Roadmap

Epics are integration gates. Atomic implementation packets live in ARTIFACT_BACKLOG.yaml.

## E00 Repository truth and reuse map
Establish which existing modules are reused, adapted, deprecated, or missing.
Exit: module map + gap register accepted. No redesign implementation before this gate.

## E01 Canonical domain contracts
Freeze minimal contracts for Mission, Agent, Execution, Crew, Swarm, Artifact, Attempt, Lesson, InferenceProfile, ToolCapability, ResourceEnvelope.
Exit: contracts serialize/validate and have focused tests.

## E02 Durable cloud state
Persist mission/agent/execution/artifact/crew/event state and recover after restart.
Exit: restart test proves identity and mission continuity without in-memory authority.

## E03 Heterogeneous inference
Make provider/model/effort an execution resource, not agent identity.
Exit: same agent completes attempts through two configured profiles; requested/applied configuration is recorded.

## E04 Tools, terminal/web, MCP
One capability registry for native and MCP tools.
Exit: native + MCP tool invoke through same contract; terminal is sandboxed; web capability registered.

## E05 Artifact-native mission planner
Turn goal into executable artifact DAG sized for weak workers.
Exit: valid acyclic packets with exact outputs/dependencies/verification; validator rejects ambiguous/oversized packets.

## E06 Autonomous population and emergent crews
Agents recruit/spawn/reassign/form crews without central workflow micromanagement.
Exit: small initial population autonomously adds a worker for independent work, forms a crew, completes work, changes/dissolves crew, preserves identities/events.

## E07 Memory graph and context assembly
Separate raw evidence, long-term knowledge, medium pointers, task state, working context, archive.
Exit: pointer -> long-term node -> raw evidence retrieval works; context refresh preserves identity.

## E08 Learning engine and Experimenter
Capture attempts, candidate lessons, validation, reusable experience.
Exit: failures produce evidence-linked candidates; validated lesson affects later behavior; Experimenter resumes after restart without erasing failed attempts.

## E09 Analytics and resource intelligence
Measure model/effort/tool/personality/team effectiveness and efficiency.
Exit: verified outcome joins to actual inference/tool/token/latency/cost records; cohort comparisons are available without presenting correlation as causation.

## E10 Templates and customization
Provide blank, software engineering, research, experiment lab, and IT operations templates.
Exit: templates are copyable/editable/versioned and reference capabilities, not mandatory providers.

## E11 Cloud product journey
Goal -> configure -> start -> leave browser -> return -> inspect -> intervene -> receive verified artifacts.
Exit: end-to-end cloud journey survives browser/process interruption.

## E12 SplitSignal reference + BYO proof
Optimize SplitSignal integration without lock-in.
Exit: same applicable mission runs through SplitSignal adapter and a separate supported BYO/OpenAI-compatible endpoint without agent-code changes.

## E13 Efficiency and adaptive organization
Learn when extra agents/models/effort help or waste resources.
Exit: benchmarks expose success/resource curves and system can choose not to spawn when marginal benefit is poor.

## E14 Security, tenancy, release evidence
Tenant isolation, secrets, capability scoping, auditability, recovery and release proof.
Exit: security/isolation/e2e/recovery checks pass with reviewable evidence.

## Dependency spine
E00 -> E01 -> E02
E01 -> E03
E01 -> E04
E01 -> E05
E02 + E05 -> E06
E01 + E02 -> E07
E03 + E07 -> E08
E03 + E04 + E06 + E08 -> E09
E05 + E06 -> E10
E02 + E03 + E04 + E05 + E06 + E10 -> E11
E03 + E11 -> E12
E09 + E11 -> E13
E02 + E04 + E11 + E12 -> E14

Parallel execution is encouraged wherever these dependencies permit.
