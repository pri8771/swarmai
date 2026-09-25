# Source audit and open-source research

Research date: 25 September 2026. Static source and official-document inspection. This appendix is evidence and research context; it is not an implementation report. No product code was changed, Hermes installed, or live inference executed by this planning task.

The [product plan](SWARMAI_MVP_PLAN.md) and [execution packets](EXECUTION_PACKETS.md) are the decision baseline. Earlier alternatives/defaults in these notes are preserved for provenance; the final plan prevails. In particular, the newer decision is an optional Hermes planning-agent workstream within the MVP, after native contracts are available.

## Source reference roots

- [SwarmAI main snapshot](https://github.com/pri8771/swarmai/tree/08b910f981eff2ab66873a71055090f2c60f2a91) — unqualified relative Swarm paths in this appendix.
- [SwarmAI donor snapshot](https://github.com/pri8771/swarmai/tree/4d16fe85188861df6e123b4454c6bdc416e6c639) — paths explicitly marked candidate/donor.
- [Inference router observed snapshot](https://github.com/pri8771/inference_server/tree/bb6b6167c225efbf66b5a4edb6c977e8a79490e4).
- [Hermes inspected main snapshot](https://github.com/NousResearch/hermes-agent/tree/59004a62356f3a4697ab0fe8ad5086d2b405e2a6). Main inspection and release identity are distinguished below.

Local audit paths in the notes identify inspected checkouts. They are not implementation targets. Revalidate remote state before starting work.


---

## Part I — SwarmAI source audit

Read-only source inspection completed 2026-09-25. This document is planning evidence, not an implementation or acceptance report. No product files edited, no inference called, no service deployed, no test results invented. Existing tests were inspected but not rerun in this subtask.

#### Repositories, identities, and authority reset

- Product repository: https://github.com/pri8771/swarmai.
- Remote `main` verified using `git ls-remote`: `08b910f981eff2ab66873a71055090f2c60f2a91`.
- Baseline source checkout: `/Users/pchordia/Documents/Codex/2026-09-24/referenced-chatgpt-conversation-this-is-an/work/swarmai-main-audit`; detached at that commit.
- This checkout already has modified `docs/evidence/fix-004/last-checkin.json`, `docs/evidence/fix-004/runner-state.json`, `schemas/v1/COMPATIBILITY.md`, `schemas/v1/product_contract.v1.json`. These were not modified by this inspection. Preserve them; do not clean/reset/use this dirty audit checkout for implementation.
- No remote SwarmAI `dev` branch exists at inspection time. The pasted chat's `dev` branch and `804b28bd...` identity belong to **inference_server**, not SwarmAI. Do not transplant that branch instruction to SwarmAI as though it already exists.
- Separate V1.7 candidate: `/private/tmp/swarm-v17-composition-20260922`, branch `codex/swarm-v17-composition-20260922`, `4d16fe85188861df6e123b4454c6bdc416e6c639` (also verified on remote). Clean at inspection.
- Candidate/main merge base: `b9141fa3150f853586dede0334a47b344571bc16`. Main contains later V3 modules, candidate contains operational V1.7 fixes absent from main. Never merge the entire candidate blindly: compare and port bounded behavior/tests.
- Old coordination snapshot checkout `/Users/pchordia/Downloads/swarm_codex/coordination/swarmai`: branch `codex/portfolio-review-20260922`, commit `30b3cbbd3d1de8c63ecaa297387c3aeae3d0ba64`; not a current implementation baseline.
- Current remote coordination branch verified/fetched: `coordination/swarm-control` at `2fcb7bca4e734e147f203ad7168369ec00a14409`. No checkout mutation performed by fetch.
- No `AGENTS.md` or `CLAUDE.md` exists in main's tracked tree or main audit checkout ancestor paths inspected. Do not silently treat branch-local coordination rules as main's instructions. The candidate's AGENTS does direct its worker to coordination rules.
- Coordination AGENTS and SESSION_START still name an old V1.7-only scope/source and one implementation owner. Current user explicitly asks for a new detailed plan, so planning is authorized; a new execution handoff should explicitly state the selected source baseline, scope, owner, branch, and supersession. Do not edit old evidence or claim V1.7 accepted. Read the active owner/heartbeat before starting implementation so another worker is not overlapped.
- SwarmAI integration branch decision belongs in packet 0. Suggested new implementation branch from verified main, with independently reviewed candidate fixes. Creating an integration `dev` would be a new explicit plan decision, not discovery.

All line references below are relative to main baseline unless marked candidate.

#### What is reusable and what must change

| Area | Inspected source | Current fact | Planning direction |
|---|---|---|---|
| Mission and task contracts | `src/swarm/contracts/mission.py:35-129` | Mission goal, acceptance, scopes, resource caps; TaskSpec parent/dependency; TaskAttempt; thin AgentProfile/AgentSession; GraphProposal. No mandatory Crew/Swarm entity. | Reuse Mission/TaskSpec/Attempt; extend profiles for human-selected seed agents and personality. Separate logical agent identity from runtime generation/session and execution worker. Add delegation intent and succession records. No new Crew table or mandatory manager. |
| Fixed execution | `src/swarm/mission/runtime.py:51-59`, `:116-153`, `:130-231`; `mission/planner.py` | Static inspect/implement/verify/review sequence, one RepoWorker, sync work inside async run; no adaptive runtime dispatch. | Replace operational path with one agent run loop using durable task/attempt state. Keep parser/software sequence as an example adapter or archived demo. Route CLI/API/Python/UI to the same engine. |
| Agent tools | `src/swarm/mission/worker.py` | Specialized Python-repo worker with direct writes/tests, optional broker fallback; not autonomous reusable agent runtime. | Reuse bounded worktree utility as an optional tool, not core agent identity. General agent chooses work, messaging, memory retrieval, delegation from typed capabilities. No scripted collaboration sequence. |
| State and leases | `src/swarm/db/models.py:28-159`, `:355-585`; `db/repositories.py:33-279`; `db/lease_fencing.py:627-1526`; `workers/service.py:53-377`; `workers/durable_protocol.py` | SQLAlchemy domain rows, task/attempt/worker leases, cancellation generations, result fencing, receipts; live services largely disconnected from MissionRuntime. | Reuse as sole domain authority; wire into new operational engine rather than add another authority DB or scheduler. Extend transactional schema for agent identities/generations, mailboxes, handoffs, experiences/lessons. |
| API state | `src/swarm/api/store.py:50-71`, `:435-507`; `api/events.py:11-60` | ProductStore and events use process-local structures with JSON mission records. API review can accept caller-provided produced/check values and complete mission. | Turn store into service/repository facade. Acceptance must refer to protected checks for actual attempt/artifacts, not caller-created matching answers. Durable event stream/cursors and restart-safe idempotency. |
| API execution | `src/swarm/api/routes_v1.py:60-271` | Create/get/review/cancel/graph/events; no execute/start route in main. | One mission start/resume/pause/cancel path used by API, UI, SDK, CLI. Port candidate execute route semantics selectively. |
| Artifact preservation | `mission/runtime.py:261-289`, `:292-310` | Records pending_apply then deletes worktree unconditionally. | Fix before new runtime gate; retain/materialize accepted artifacts and independently test reopen after process shutdown. Candidate runtime `:419-442` is donor for preservation. |
| Communication | `contracts/workspace.py:146-159`; `workspace/events.py:24-71`; `db/models.py:465-508`; `db/repositories.py:202-279`; `api/events.py` | Event envelope has causation/correlation/dedupe. EventBus and API log are in-memory; no durable agent inbox/peer message/ack contract. | Reuse event envelope, SQL event rows, outbox. Add addressed messages plus shared mission notifications, cursors, read/ack status, reply-to and request expiration. A durable message is not a guarantee of model comprehension; acknowledgment state explicit. |
| Outbox | `src/swarm/db/outbox.py:15-35` | Named DBOS bridge but default enqueue function is a no-op; rows can be marked published with no real consumer. | Production startup must require a real dispatcher; fake/no-op permitted only explicit test mode. Test crash after commit/before dispatch, repeated dispatch, and no silent drop. |
| Graph admission | `controller/graph.py:42-100`; `controller/mission.py:43-85` | Scopes with partial overlap can exceed mission scopes; some graph op types validated but not mutated by commit. | Strict subset authorization and transactional revisions before enabling autonomous delegation. Support only fully implemented ops initially. Agent decides useful decomposition; deterministic policy enforces capacities/depth/permissions/deduplication. |
| Scheduler | `controller/scheduler.py:67-142`; `controller/resource_allocator.py:36-65`; `controller/fairness.py:17-20` | Useful capacity concepts, but dependency predicate all(True), aging same offset for all tasks, fairness not enforced operationally, allocator ranks one requester. | Single host small concurrency first, durable runnable queue and fairness. Reuse correct contracts and DB fencing; remove incomplete allocator from critical path. No distributed scheduling in MVP. |
| Memory schema | `contracts/knowledge.py:23-182`; `db/models.py:510-583`; `knowledge/repository.py:34-595`; migrations `a16know003a0001...` | Durable, versioned knowledge, permission labels, provenance, tombstones, supersession, contradictions. | Strong reuse candidate for long memory; add private-agent/shared-mission/project scopes clearly. Add experiential records and recall cues referencing immutable versions/digests. |
| Retrieval | `knowledge/retrieval.py:35-135`; `knowledge/budget.py:13-110` | Permission-first retrieval; returned bundle currently includes full selected bodies. Token estimate is whitespace count (`retrieval.py:31-32`). | Add separate lightweight index/cue search and explicit dereference. Source existence proves memory exists, not truth. Context builder pins mission instructions/critical active facts and budgets cue pool/fetched content. Replace whitespace count with model-aware count or conservative estimate plus measured usage. |
| Old memory | `memory/store.py:35-205`; `knowledge/memory_adapter.py` | JSONL legacy MemoryStore and separate adapter path. | Migrate/import into KnowledgeRepository; deprecate unrestricted legacy retrieval from operational routes. Avoid two writable memory authorities. |
| Context | `workspace/context.py:15-103`; `contracts/workspace.py:79-90` | Character/findings bounds and excerpts with provenance, no X/Y succession. | Reuse context provenance concept; introduce exact occupancy snapshot covering system/tool schemas/messages/output reserve. Add cue allowance, retrieval receipts, external memory refs, and reference compaction. |
| Succession | Search across `src/swarm`, `apps/console/src` for trainee/succession/handover/subagent/mailbox yielded no implementation. | No KT lifecycle or atomic takeover. | New core feature, not rename of checkpoint. X triggers exactly one trainee generation; Y stops parent new work and final KT. Trainee shadow is read/ask only until atomic owner-generation transfer. Preserve logical agent identity while recording different session/generation. Distinct from delegation child. |
| Learning | `learning/__init__.py:9-80`; `db/models.py:785`; `tests/objectives/test_v30_objectives_learning.py` | Proposal transitions (validation/holdout/canary) in an in-memory repo; no actual measured experience or social learning loop. Even accepted->rollback transition inconsistent with rollback method. | Reuse proposal/holdout/provenance concepts; add persisted experiences, provisional lessons, teaching messages, adoption/evaluation, contradictions/rollback. Evidence-specific expertise rather than categorical qualified gate. Do not claim model weights update. |
| Tools/effects | `contracts/actions.py`; `tools/v17_gateway.py:54-438`; `tools/effects.py:321-639` | Consequential tool boundary and durable effects exist; old and new gateways coexist; runtime bypasses main gateway. | Select one boundary and wire every tool through it. Port hardening from candidate with tests. Reuse effect reconciliation; unresolved side effects remain unknown after a timeout. |
| MCP | `tools/adapters/api_mcp.py:12-46`, `:48-105`; `pyproject.toml:8-24` | Explicit simulated MCP/API echo, invented ext ID from default transport; no MCP SDK dependency. | Replace with actual generic MCP client connection/session/catalog/call support behind same tool policy. Linear is an example server, never a built-in authority requirement. No fabricated success adapter in operational mode. |
| Extensions | `extensions/contracts.py`; `extensions/registry.py`; `extensions/loader.py` | Versioned manifests and scopes; registry process-local. | Reuse manifest/permission concepts as connector configuration; persistent grants, secret references, server lifecycle. Defer marketplace/plugin framework. |
| Inference | `broker/broker.py:64-361`; `broker/ledger.py:40-321`; `mission/brokered_inference.py:96-210`; providers package | Swarm has own provider adapters/catalog/admission/quotas/local chat, duplicating inference_server's intended owner role. | Swarm keeps mission budget, privacy and required model capabilities. Separate router owns upstream accounts/model normalization/fallback/route selection/provider usage. Implement one typed HTTP adapter to inference_server, no cross-repo source imports. Retire Swarm's direct upstream runtime path after parity. Keep local fake router for deterministic tests. Preserve upstream attempt IDs/usage/unknown outcomes; do not double-count spend. |
| Python SDK | `pyproject.toml:43-44`; `src/swarm/cli.py`; no sdk path in tracked tree | Importable Python package and CLI exist; no stable user-level SDK for define agents/mission, run, observe, messages. | Add thin Python client over same API or common in-process application service (one chosen contract); generation from shared schema where appropriate. Avoid separate execution engine in SDK. |
| Visual product | `apps/console/package.json`; `apps/console/src/App.tsx`; `api/client.ts:64-75`, `:91-126`, `:129-251` | React/Vite console, live create/history/capacity plus fixtures. Live mission conversion fills tasks=[], planningRoles=[], logicalAgents=0. Many interactions are explicit fixtures. | Reuse app shell/components/client discipline; implement agent/profile editor, goal/seed selection, real start/observe, peer messages, delegation ancestry, trainee/handoff state, context occupancy, memory inspector, lesson evidence. Both surfaces edit same definitions. No crew builder required. |

#### DBOS/PydanticAI: exact observed usage

`pyproject.toml:16` pins `pydantic-ai[dbos]>=2.46,<2.47`. Real imports and DBOS workflows occur in `src/swarm/spike/durable_agent.py:9-11`, `:28-42`, `:66-87`, `:114-165`; the docstring explicitly calls it a compatibility spike, using two fake route identities and local SQLite DBOS system DB. `src/swarm/spike/broker_hook.py` uses PydanticAI FunctionModel. `tests/spikes/test_durable_spike.py` covers the spike. The product runtime does not call these. `src/swarm/workers/transport.py:3` names HTTP/queue/DBOS as future adapters; only InProcessWorkerTransport is implemented here. `db/outbox.py` calls an injected callback and defaults to no-op.

Therefore "DBOS is installed and proven in a small compatibility spike" is supported; "the live mission path is durable through DBOS" is not. The plan should choose explicit reuse or deferral and keep PostgreSQL domain state as authority. If DBOS is adopted for execution replay, its workflow state must not become a competing owner of mission/lease/effect authorization. Durable side effects must still use receipts/fences. Do not pull in Hermes/CrewAI/LangGraph as a second orchestration authority merely to gain a loop.

#### Candidate donor work worth preserving

Candidate commit `4d16fe8`, compare against main `08b910f`, has about 6,699 added and 566 removed lines in 39 files across mission/API/tool tests and CI. This is too large for blind cherry-pick.

Candidate-specific source donors:
- `src/swarm/mission/action_boundary.py:15-35`: bounded local worktree gateway (note defaults still in-memory/static; port concept and replace with real stores/fences).
- `src/swarm/mission/runtime.py:17`, `:174`, `:419-442`: gateway wiring, actor context, worktree preservation logic.
- `src/swarm/api/routes_v1.py:175`, `api/store.py:594`: mission execution path.
- `src/swarm/mission/worker.py`: targeted edits, proof grounding, thread bridge; relevant for optional code tool.
- `src/swarm/tools/adapter_registry.py`, `manifests.py`, `fences.py`, `effect_recovery.py`, `adapters/local_sandbox.py`, `adapters/base.py`: boundary hardening.

Candidate tests worth bringing forward with matching behavior:
- `tests/mission/test_worker_effects_via_gateway.py`
- `tests/mission/test_mission_runtime_async_worker_bridge.py`
- `tests/mission/test_defect_proof_gate.py`
- `tests/mission/test_review_grounding.py`
- `tests/mission/test_r02c_targeted_edits.py`
- `tests/mission/test_v14_materialization_repair.py`
- `tests/api/test_g11_execute.py`
- `tests/api/test_art_v11_process_restart.py`
- `tests/api/test_art_v12_broker_contract.py`
- `tests/tools/test_single_consequential_path.py`
- `tests/tools/test_v17_gateway_authority.py`
- `tests/tools/test_v17_gateway_classification_fences.py`
- `tests/tools/test_v17_gateway_failclosed.py`
- `tests/tools/test_gateway_envelope_integrity.py`
- `tests/tools/test_integration_manifests.py`

#### Existing checks and required extensions

Current `.github/workflows/ci.yml:15-21` runs uv sync, ruff, mypy, package install check, and Alembic heads. Offline pytest allowlist `:24-51` omits tests/knowledge, tests/objectives, tests/extensions, tests/recovery despite their presence. DB integration runs only if SWARM_DATABASE_URL exists (`:52-59`); skipped DB evidence is not durable acceptance. Console job `:61-76` runs npm ci/lint/test/build. Live job prints no-live notice only (`:78-90`).

Recommended new gate coverage:
1. All offline tests collected deliberately, with live network denied by default; do not exclude newly added feature folders from CI.
2. Disposable PostgreSQL service required in CI for migrations, concurrent graph revisions, mailbox delivery/cursors, scope isolation, lease fencing, takeover, effects, restart recovery. SQLite is insufficient evidence for PostgreSQL concurrency.
3. SDK/UI parity: same saved MissionDefinition, seed identities, personality/config versions, and start operation. API test client/Playwright runs against real local service plus fake router/MCP server, never fixture-only UI acceptance.
4. Autonomous behavior evaluated with actual model in authorized final gate: unprescribed peer help, useful delegation, corrected false peer lesson, collective goal retained after succession. Deterministic scripted fake behavior proves mechanics only; cannot prove autonomous choice/learning.
5. X/Y boundary tests: exact threshold, overshoot, one trainee, concurrent trigger, model with smaller context, giant tool result, final-KT failure, crash before/after ownership transfer, stale parent tool call rejection, incoming messages during takeover, trainee remains below its own threshold. Use configurable token window to trigger tests; reserve KT capacity so a giant output cannot consume last space.
6. Memory tests: cue points to actual accessible version, cue existence doesn't prove correctness, tombstone/supersession, no source->cue permission widening, fixed context cue budget, targeted retrieval cost vs copying, active constraints pinned, known unknowns not treated as facts.
7. Learning tests: lesson is provisional until evidence; adoption selected for relevant task; held-out repeated case comparison with source-free baseline; bad lesson quarantine/rollback; no fake learning claim based only on passing proposal transitions. Human can inspect/edit/reset acquired preferences and experience without changing authority.
8. Generic MCP: initialize/list tools/call using standard SDK transports, schema validation, tool list changes, connection lost, deadline/cancel, result size bound, redaction, secrets never in prompt, no retry of uncertain mutation without reconciliation, prompt content has no authority, namespaced tools; at least two different fixture servers so no Linear-specific assumption.
9. Router integration: stable request ID/attempt correlation, per-call model capability/context metadata, cancellation semantics, route fallback provenance, token usage and unknown price surfaced, model switch causes context recount, no direct upstream fallback in Swarm. Cross-repo contract tests pinned to versioned fixture/schema.

#### Suggested initial file-level packet sequence

This is proposed new placement, not existing code:
- P0 baseline/authority/branch and donor decision: checked-in ADR and packet queue; record existing dirty artifacts without modifying them; fresh worktree at verified main.
- P1 contracts + persistence: extend `contracts/mission.py`, add `contracts/agent.py`, `contracts/communication.py`, `contracts/succession.py`, `contracts/learning.py`; add SQL models/repos/migration alongside existing DB files.
- P2 unified application services and inference boundary: `runtime/agent_loop.py`, `runtime/mission_service.py`, `providers/router_client.py`; retire direct local/provider calls from operational entry points. Make fakes explicit injected transports.
- P3 durable communication and autonomous decisions: `runtime/communication.py`, `runtime/delegation.py`, repository inbox/outbox; keep semantics chosen by agents with human profiles and collective mission invariants.
- P4 reference memory/context: extend `knowledge/repository.py`, `retrieval.py`, add `knowledge/cues.py`, `runtime/context.py`; import old memory via adapter; actual tokenizer/count metadata.
- P5 trainee succession: `runtime/succession.py`; transactional generation transfer/inbox cursor/active action reconciliation; preserve logical identity and episode lineage. Parent/trainee have different session IDs.
- P6 learning experience: `learning/experiences.py`, `lessons.py`, `evaluation.py`; persist into existing knowledge stores and tables, allow agents to teach/ask/apply while measuring outcome.
- P7 generic tools/MCP: `tools/mcp_client.py`, server repository/config and real adapter using single gateway. Retire echo operational default, preserve test fixture.
- P8 SDK + console: add thin SDK package API, update routes/schemas/client and UI features; replace live empty placeholders with actual data; expose takeover/memory/lesson evidence clearly.
- P9 integrated acceptance and docs: run frozen scenario matrix, install/restart, no-content-loss, separate fake/live evidence, fix README/COMMAND_MAP/package status and examples to new model; keep old claims as historical evidence.

Do not claim a phase completed from classes, schemas, dashboards, or mock agent stories alone. Every packet needs a working observable behavior and an integrated successor packet gate.

---

## Part II — Hermes, including optional seed-agent integration

Research date: 2026-09-25. Planning only. Official Nous Research GitHub repositories and `hermes-agent.nousresearch.com` documentation were used. No installation, agent execution, provider inference, or service startup was performed. Source excerpts downloaded for inspection are under `work/hermes-source/`.

#### Recommendation

**Hermes is useful as a reference implementation and a possible optional worker runtime. It is not required for SwarmAI's MVP and should not own SwarmAI's mission state, shared memory, learning acceptance, or successor lifecycle.** First implement the native mission/agent/context/succession contracts. Then permit a bounded adapter spike against those contracts, with fake inference and restricted tools. Adopt the adapter only if it reduces implementation burden without obscuring requests, tool effects, context occupancy, cancellation, and costs.

This is an architectural recommendation, not a finding that Hermes is incapable. Hermes provides substantial working machinery, but it is a complete personal-agent application with its own state, memory, background inference, delegation, and tool authority. Making it the mandatory core would introduce two owners of the behavior SwarmAI is specifically trying to define.

#### Current upstream identity

- Canonical repository: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent). The official repository links to `hermes-agent.nousresearch.com`; similar organization names and domains were excluded.
- Latest release from GitHub API: **v0.21.5**, tag **v2026.9.24**, published **2026-09-24T10:09:38Z**. A search result listing v0.21.3 was stale. [Release](https://github.com/NousResearch/hermes-agent/releases/tag/v2026.9.24).
- Inspected main snapshot: **59004a62356f3a4697ab0fe8ad5086d2b405e2a6**, commit timestamp **2026-09-25T11:14:57Z**. Verified with `git ls-remote` and GitHub commit API. This is later than the release; do not equate inspected main behavior with tagged behavior. [Pinned snapshot](https://github.com/NousResearch/hermes-agent/tree/59004a62356f3a4697ab0fe8ad5086d2b405e2a6).
- Core license: MIT, confirmed in pinned [LICENSE](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/LICENSE). Retain notices if reusing code. Plugins and adjacent projects require their own dependency/license checks.
- The pinned `pyproject.toml` says package version `0.0.0`; use a Git SHA or verified release tag, not that field, to identify the build. It permits Python >=3.11,<3.15 for update compatibility, but comments state current runtime support is 3.14 and many dependencies are gated on >=3.14. This favors a separate process/container for an eventual adapter over installing it into SwarmAI's environment. [Packaging](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/pyproject.toml#L6).

#### Mechanisms relevant to the proposed design

##### Memory and references

Hermes has bounded profile-local `MEMORY.md` and `USER.md` notes injected as a frozen snapshot at session start. On-disk edits persist immediately, but the injected snapshot normally waits until a new session. It also retains conversations in SQLite and offers FTS5 session search and navigation to original messages. Current memory docs explicitly describe raw message retrieval without LLM summarization, while the README still calls session search LLM-summarized. Prefer inspected current tools to marketing descriptions. [Memory documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory), [pinned session search](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/tools/session_search_tool.py).

**Fit:** Good patterns for a small active memory plus on-demand durable recall. **Gap:** This does not establish SwarmAI's reference-only middle-memory model, mission-scoped shared learning, validated memory promotion, or the proposed two-stage successor transfer. Implement those as Swarm contracts. A reference proves a record exists; it does not prove the remembered claim is true, current, authorized, or applicable.

##### Skills and learning

Skills use compact discovery followed by on-demand `SKILL.md` and support-file reads. This is a useful interoperability format for promoted procedural lessons. The ordinary learning mechanism is model-authored persistent text, not automatic model-weight training. [Skills documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills).

Pinned code shows a background review agent replaying a conversation snapshot and deciding whether to write memory or skill updates. It inherits model/provider settings, runs on a daemon thread, uses a tool whitelist, and can write to the stores. The skill manager provides atomic writes, validation, read-before-write guards, optional scanning, and mutation telemetry. Those mechanisms support persistence and maintenance; they do not constitute an independent held-out behavioral evaluation before a lesson becomes trusted. [Background review](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/agent/background_review.py#L1), [skill writes](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/tools/skill_manager_tool.py#L350).

The curator manages stale/archive transitions and optional LLM consolidation. It tracks usage and maintains recoverable changes. Its documented mutation ledger is telemetry, not a fail-closed gate: a failed ledger write does not block a skill mutation. **Borrow the lifecycle and rollback ideas, but retain SwarmAI's own evidence/approval contract for trusted lessons.** [Curator documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/curator).

##### Delegation and succession

Hermes delegation creates `AIAgent` children with fresh conversations, goal/context briefs, selected inherited capabilities, and separate terminal sessions. Children return summaries; live control and background result delivery are also present. Default delegation is flat, with explicit orchestrator roles permitting deeper work. Background processes remain owned by the child that created them and are stopped during child teardown. [Delegation documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation), [child lifecycle implementation](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/tools/delegate_tool_child_run.py).

**This matches task delegation, not the requested succession rule.** The inspected documentation/code does not expose a native X%-spawn-trainee / Y%-final-KT / shadow-and-take-over lifecycle with transfer of work ownership. Context-pressure handling uses summarization/compaction, with optional session rotation. SwarmAI must implement successor readiness, two KT stages, event catch-up, and atomic assignment/inbox ownership transfer independently.

Hermes thresholds are also more complicated than a single percentage: configuration describes 50%, but pinned code applies a 75% floor to context windows below 512K, plus model/provider policies and an absolute token cap. Allowing that compressor to fire first would invalidate SwarmAI's X/Y policy. The adapter must expose or disable conflicting compaction and report context accounting accurately. [Compression documentation](https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching), [pinned threshold handling](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/agent/context_compressor.py#L1177).

##### Embedding and authority

Hermes documents direct Python `AIAgent` use with tool selection, custom endpoint, memory/context toggles, and iteration limits. Instances must not be shared across concurrent tasks. Its API offers agent execution over OpenAI-style endpoints and capability discovery; this endpoint wraps tool-running agents and is not merely a model transport. [Python library](https://hermes-agent.nousresearch.com/docs/guides/python-library), [API server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server), [constructor](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/run_agent.py#L260).

Hermes has its own provider/auxiliary routing, persistent profile state, tools, delegated workers, background reviews, and scheduling surfaces. A custom `base_url` makes an inference-router connection plausible but is not proof that every auxiliary request and fallback follows it. The adapter must demonstrate that property, or block all unapproved egress. The inference_server project should remain the owner of upstream credentials, transport reuse, provider/model registry, fallback, usage normalization, and route selection. Hermes, if used, sits above that router as an optional worker runtime.

Official security policy explicitly describes Hermes as a single-tenant personal agent. Local terminal commands run on the host by default; terminal-only sandboxing does not contain other code paths. The policy recommends wrapping the whole process for untrusted input or shared/production usage. **For SwarmAI, one isolated process/profile per admitted runtime scope is a stronger integration starting point than shared in-process agents.** [Security policy](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/SECURITY.md).

#### Suggested bounded adapter spike

Dependency: native Swarm `AgentRuntime` contract and fake runtime already pass mission, context, delegation, cancellation, and handoff acceptance checks. The Hermes spike is optional and must not block MVP completion.

1. Pin a reviewed Hermes release/SHA in a dedicated image/environment. Verify that snapshot's actual behavior; this assessment inspected main, not the release tag.
2. Implement Swarm's runtime operations around Hermes' documented conversation/run interfaces. The names `start`, `step`, `interrupt`, `snapshot`, and `close` would be **Swarm adapter operations**, not a claim that Hermes exposes each as a native method. No native single-step/snapshot API was established in this assessment. Use documented `AIAgent.chat` / `run_conversation` or the HTTP Runs API, and prove the selected boundary permits Swarm control before adopting it. Map every Hermes session/child/call to mission, logical agent, generation, task, and attempt IDs.
3. Route all main and auxiliary model calls through a fake inference_server endpoint. Disable autonomous fallback, cron, background learning, built-in delegation, and independent persistent memory until each has an explicit mapping. Use allowlisted tools only.
4. Make Swarm's permission gate the execution boundary for every tool. If the wrapper cannot intercept or contain all effect paths, fail the spike instead of relying on prompts.
5. Send a compact immutable mission brief and relevant memory references. Export findings as proposals/artifacts into Swarm's durable store. Hermes skill writes remain candidate lessons; Swarm evaluates and promotes them.
6. Demonstrate two concurrent isolated agents, cancellation of a blocked tool, restart/replay, no unauthorized provider requests, captured auxiliary usage, and no direct writes outside the workspace.
7. Demonstrate X/Y successor training and atomic ownership handoff driven by Swarm. Prove compaction cannot silently bypass thresholds; prove old generation messages/tool completions cannot commit after takeover.
8. Compare against the native runtime on the same replay fixtures: correctness, context fidelity, handoff loss, latency/call count, developer complexity, maintenance burden. Keep Hermes only with measurable benefit and no loss of observability/control.

Stop criteria: provider bypass, unknown context occupancy, opaque tools, uncancellable effects, profile leakage, hidden memory mutation, or required invasive fork. Result is an ADR and measured comparison, not automatic promotion into production.

#### Adjacent future candidate

[NousResearch/hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution) is a separate project using DSPy/GEPA to evaluate and evolve text artifacts. Its README marks skill evolution implemented and tool descriptions, prompts, code evolution, and continuous operation planned. It does not supply the requested social-learning system today. Defer it until Swarm has a real lesson dataset, held-out tasks, baseline metrics, rollback, and authorized inference budget. The project declares MIT; the proposed external Darwinian Evolver is listed as AGPL v3 and requires a separate licensing decision before adoption. No performance or cost claim from its README was independently reproduced.

#### Useful immediate reuse without runtime dependency

- Adopt interoperable `SKILL.md` packages as an import/export representation for validated procedural lessons, with provenance and pinned content hashes.
- Reuse the design patterns of SQLite-backed exact recall, compact indexes, explicit source retrieval, mutation history, recoverable archival, and bounded background maintenance.
- Keep agent-created lessons, peer endorsements, and verified results distinct. Repeated sharing is not independent confirmation; preserve a lesson's source ancestry.
- Use Hermes as a comparison case in architecture tests, especially hidden auxiliary calls and context policy conflicts. Do not promise that adding Hermes makes SwarmAI autonomous, learning, or durable by itself.

#### Evidence limitations

Static inspection and official-document review only. No Hermes test suite or live runtime was executed. No claim is made that every upstream feature is audited or that the inspected main SHA remains current after research. Context thresholds, memory defaults, and Python runtime requirements vary across snapshots; adapter implementation must recheck its pinned version.

#### Addendum: optional Hermes agent selected at swarm creation

The user's newer direction makes this a useful **optional MVP workstream**, not an all-or-nothing core adoption. Swarm creation may mix a Hermes-backed agent with native Swarm agents. The operator chooses the initial individuals, or lets Swarm propose them. A Hermes agent can be assigned the initial planning contribution without becoming the swarm's manager or acquiring authority over peers.

Keep three independent settings:

- **Runtime:** native Swarm or a specific qualified Hermes adapter snapshot. This identifies the software executing the agent loop.
- **Role/profile:** planner, investigator, implementer, reviewer, or an operator-defined personality and skill profile. Planner conveys purpose, not administrative permission.
- **Model/route:** a model admitted through inference_server. Selecting Hermes does not select a Nous model, Nous Portal, a subscription, or independent upstream credentials.

The runtime capability registry should state exactly what was qualified for a particular adapter build/configuration/provider combination. Show an unavailable Hermes option with its unmet qualification reason until it passes; never equate installed/configured with qualified. Fake-only qualification enables a labeled demo mode, not live provider execution. Live selectability requires the applicable route and runtime evidence. Changing a pinned adapter build or capability configuration invalidates affected qualification until rechecked.

##### A narrow, useful first integration

Use Hermes for bounded planning turns. Swarm supplies the collective goal, operator-selected profile, permitted context references, current facts, and messages. Hermes returns structured proposals, questions, peer-message intents, and requested reads. Swarm validates and executes those requests through the kernel, then returns the authorized results for the next turn. The planner can ask any admitted peer for help, including a peer without a matching expertise label. It can propose a task split; the kernel admits the requested child and records it as a normal swarm agent.

The initial adapter grants no direct filesystem writes, shell, browser, external messaging, provider fallback, cron, autonomous Hermes child spawning, built-in memory mutation, skill mutation, or background review. Authorized memory reads, messages, graph proposals, and descendant requests use Swarm's ordinary capability boundary. Later versions can qualify specific tools individually. The UI must clearly state these restrictions on the selected agent; a restricted Hermes planner must not be presented as a fully equipped Hermes installation.

**Feasibility is conditional but credible.** The inspected constructor accepts explicit provider/base URL, toolset selection, `skip_memory`, `skip_background_review`, `skip_context_files`, iteration/time limits, and callbacks. The documented library supports conversation calls, and HTTP runs support start/status/events/cooperative stop. A thin, isolated wrapper around those calls can implement the narrow structured-exchange pattern without a hypothetical native `step()` API. However, an empty toolset must be tested against defaults and automatic tool injection; callbacks must not be assumed to be approval gates. Confirm all effective tools and all emitted provider requests in the actual pinned build. [Pinned constructor](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/run_agent.py#L262), [documented run control](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server#runs-api-streaming-friendly-alternative).

Additional verification findings: the inspected constructor defaults `max_iterations` to `sys.maxsize`, despite library documentation describing a 500 default; always set an explicit limit. HTTP caller instructions are layered on top of Hermes' core prompt and retain its tools/memory, so requesting "planning only" in a prompt is not capability enforcement. The stop endpoint returns before work actually exits; retain an authoritative stopping state and reject late commits until the worker exit is confirmed. [Pinned constructor](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/run_agent.py#L267), [HTTP prompt and stop behavior](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server).

Planning-only operation still follows X/Y succession. Swarm measures the complete submitted context for the active generation, including schemas and runtime prompt overhead, and schedules KT/shadowing/takeover. It must stop or decline another turn when occupancy cannot be established or the next call would cross the protected boundary. Do not reset the accounting by opening a fresh Hermes request/session. Transfer the logical assignment/inbox through the same generation fence as native agents. A short turn or tool-free role is not an exemption.

##### Qualification task and done condition

One bounded implementation task: build `HermesPlanningAdapter` behind the existing native runtime contract and feature flag, in a separate environment, with deterministic fake inference. Add the capability manifest, mixed-runtime seed selection, structured intent mapping, and visible limitations. Demonstrate: native and Hermes agents exchange requests through the kernel; invalid self-promotion/dispatch/permissions are rejected; all inference reaches the fake router; no hidden tool, memory, background, or child activity occurs; context thresholds trigger both KT stages; stop/takeover fences reject late results; saved runs resume without losing messages or ownership. Run the native suite with Hermes absent to prove optionality. Deliver a pinned evidence report and qualification record. If a required boundary needs an invasive Hermes fork or cannot be observed, keep the option unavailable and document the failure; the native MVP continues.

---

## Part III — Open-source stack assessment

Research date: 2026-09-25. Primary official sources only. These are architecture recommendations, not installed/qualified integration claims. No software was installed and no external inference was run. Hermes is assessed separately.

#### Decision

Reuse the existing PydanticAI, DBOS, FastAPI, SQLAlchemy/Alembic and PostgreSQL foundation. Add a real generic MCP client boundary and OpenTelemetry instrumentation. Keep SwarmAI responsible for mission policy, agent identity and generations, messages, work claims, memory provenance, context succession and acceptance. Keep `inference_server` responsible for upstream providers, routing/fallback and provider usage. Use one durable orchestration owner and one authoritative application database. Avoid adding CrewAI, LangGraph, Letta and Hermes as simultaneous runtimes or adding an independent vector database by default.

The inspected SwarmAI audit checkout pins `pydantic-ai[dbos]>=2.46,<2.47` in `pyproject.toml`, alongside FastAPI, SQLAlchemy, Alembic and psycopg. This is evidence of declared dependencies, not proof they are connected to the operational mission path. Current upstream examples may use newer APIs: the implementation worker must start from the repository lockfile, inspect that exact installed API, and record a compatibility decision before changing versions.

#### Reuse now

##### PydanticAI — agent-turn adapter; MIT

Official upstream describes a typed agent loop, structured outputs, tool definitions and OpenTelemetry instrumentation. Its current repository also advertises a separate harness with context management and subagent capabilities. [Repository and MIT license](https://github.com/pydantic/pydantic-ai).

Use the core library behind `AgentRuntime` for one bounded agent turn, structured action outputs, and tool schemas. SwarmAI owns the persistent agent/session identity, collective mission, selection of actions, and when another turn runs. Connect its model interface only to the authorized router contract; do not adopt Pydantic's separate provider gateway as another routing owner. Integration cost: low to medium, since it is already declared. A library feature named "subagents" must not independently spawn workers around the kernel's quota and succession controls.

Before core integration, do a bounded compatibility spike using a deterministic fake model: valid/invalid structured action, concurrent tool callbacks, streamed messages, router tool-call IDs, usage receipts, cancellation, and replay. Do not select a new framework merely because an upstream README demonstrates a similar feature.

##### DBOS — durable execution substrate; MIT

Official docs describe checkpointed workflows backed by SQLite or PostgreSQL, recommending PostgreSQL for production. DBOS runs as a library. [Programming guide](https://docs.dbos.dev/python/programming-guide), [license](https://github.com/dbos-inc/dbos-transact-py/blob/main/LICENSE).

The PydanticAI DBOS integration currently documents that model and MCP calls are checkpointed inside a DBOS workflow, while custom tool functions and event handlers need explicit durable wrapping when they perform I/O. Failed steps may restart from the beginning. [PydanticAI integration source](https://github.com/pydantic/pydantic-ai/blob/main/docs/durable_execution/dbos.md).

Use DBOS for scheduling and recovery mechanics while SwarmAI owns domain state and legal transitions. Keep DBOS tables isolated from application tables in the same PostgreSQL service where supported; never mutate DBOS internal state as the application API. Integration cost: medium. Do not create a competing bespoke workflow executor or add Temporal/Celery/LangGraph in parallel. Do not assume checkpointing delivers exactly-once external effects: SwarmAI still needs durable effect IDs, outbox records, fencing, and reconciliation of ambiguous results. Retries must be bounded and classified. [Step and retry semantics](https://docs.dbos.dev/python/tutorials/step-tutorial).

Required spike: crash after accepting a model result, crash after recording an effect but before acknowledgment, restart during X/Y succession, cancellation during an in-flight call, and a workflow version change. Pass only if no duplicate assignment ownership or unintended repeated effect occurs. Unknown external outcomes must remain unknown until reconciled.

##### PostgreSQL — authoritative records; PostgreSQL License

Use existing PostgreSQL for mission/agent/session records, durable messages and delivery state, work claims, effect receipts, memory source records and references, lessons/evaluations, and transactional outbox. Use SQLAlchemy/Alembic already present. [PostgreSQL license](https://www.postgresql.org/about/licence/).

For the first memory implementation, exact IDs, metadata filters and PostgreSQL full-text search are sufficient to make the short/middle/long memory contract real. Retrieval and indexes are replaceable derived views; original evidence, version, access scope and supersession links are authoritative. Large artifacts can live in the existing artifact store with hashes and durable metadata. Do not embed full transcripts into every context, and do not use a vector database as the sole record of mission truth.

##### Official MCP SDK — generic integration transport; MIT

The official Python SDK supplies client/server support for tools, resources and prompts, including stdio and Streamable HTTP. It now documents a v2 stable line; pin a version compatible with the selected PydanticAI dependency rather than upgrading transitively without a test. [SDK documentation](https://py.sdk.modelcontextprotocol.io/), [client source](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/client/index.md), [MIT license](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE).

Build a generic MCP server registry: server ID, transport, endpoint/approved executable, credential reference, negotiated capabilities, discovered schemas and their versions, selected tools/resources, connection health, and per-mission/agent permissions. Linear is one possible configured server; do not model tasks around Linear or require Linear for acceptance. The router's existing mailbox MCP server does not establish an external MCP client capability.

All tool calls go through SwarmAI's effect boundary. Discovery is not authorization. Server annotations are hints and may be false; local command launch and remote auth are separate operational trust decisions. Keep resource contents and tool responses as untrusted data, preserve references and size limits, and recheck scope at invocation. [Official annotation explanation](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/), [security guidance](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices).

Integration cost: medium. Acceptance: deterministic local servers over stdio and HTTP; dynamic discovery; tools/resources/prompts; malformed schema; cancellation; timeout; disconnect/reconnect; changed schema; secrets redacted; oversized result stored as artifact; read and write paths; replay with no duplicate non-idempotent effect. After explicit authorization, one real external MCP server can be qualified without provider-specific application code.

##### OpenTelemetry — trace interoperability; Apache-2.0

Use OpenTelemetry for trace and metric instrumentation. The Python project declares traces and metrics stable and its license Apache-2.0. [Official repository](https://github.com/open-telemetry/opentelemetry-python).

Give mission, work item, agent identity, session generation, model request, message, succession, retrieval and effect records correlated IDs. Export model/provider usage as router-reported facts with estimates separately labeled. Default to metadata and artifact references; content capture is an explicit setting. The durable mission event journal powers the product UI; telemetry is not the source of truth for resuming work. Integration cost: low to medium. Acceptance must prove trace linkage across successor sessions and router requests without leaking credentials.

#### Bounded spike or later

##### pgvector — optional semantic retrieval; PostgreSQL-style license

pgvector adds exact and approximate vector search within PostgreSQL. Approximate index filtering can reduce recall, and its docs discuss filtered search and tenant isolation. [Official repository](https://github.com/pgvector/pgvector), [license](https://github.com/pgvector/pgvector/blob/master/LICENSE).

Recommendation: retain an optional adapter, enable only if a retrieval benchmark shows a meaningful gain over metadata/full-text search. Integration cost: low to medium; no second database required. Enforce scope before material is returned, retain embedding model/version/dimensions, and never use similarity as proof that a memory is true. Embeddings must use an explicitly authorized route or local model; there is no free inference hidden in "memory." Test paraphrase recall, conflicting dated facts, correction/supersession, revoked access, and cue-to-source dereferencing.

##### Langfuse — optional observability backend, after the built-in run UI

Langfuse accepts OTLP traces and can be self-hosted. Current license is MIT for most code, with enterprise directories under a separate license. It is not uniformly MIT. [OTel integration](https://langfuse.com/integrations/native/opentelemetry), [self-hosting](https://langfuse.com/self-hosting), [license](https://github.com/langfuse/langfuse/blob/main/LICENSE).

Recommendation: an optional exporter integration or post-MVP deployment. Do not make it necessary to start a swarm or to observe basic agent messages and succession. Added operational cost exceeds adding instrumentation alone; evaluate the current deployment dependencies and license of the exact features used. It helps inspect traces/evaluations, but it cannot replace the mission event journal or prove learned behavior by itself. No automatic cloud signup or content export.

##### Mem0 — optional extraction/retrieval experiment; Apache-2.0

The OSS library exposes memory ingestion and retrieval with configurable LLMs, embedders and stores including pgvector. Its current docs distinguish OSS from managed graph-memory features. The official README explicitly says its headline benchmark results include managed proprietary optimizations. [Repository/license](https://github.com/mem0ai/mem0), [OSS configuration](https://docs.mem0.ai/open-source/configuration).

Recommendation: later bounded experiment behind `MemoryExtractor`/`MemoryRetriever`, never mission authority. Integration cost: medium; hidden default upstream inference and a second vector store must be disabled. Use the router and existing PostgreSQL. Compare against SwarmAI's baseline on retrieval quality, unsupported fact extraction, correction handling, context tokens, latency and total inference cost. An extracted memory remains a candidate claim with evidence; extraction or recall does not establish that the agent learned a useful strategy. Do not copy managed benchmark percentages into SwarmAI acceptance claims.

##### Letta — reference design / possible future worker adapter; Apache-2.0

The current Letta repository points active development to `letta-ai/letta-code`; its former API server is on an archive branch. Letta Code describes persistent identities, memory and skills, context tracked in Git, and subagents. Its repository is Apache-2.0. [Repository transition](https://github.com/letta-ai/letta), [current harness](https://github.com/letta-ai/letta-code).

Recommendation: study its memory/context patterns; do not embed a second agent owner in this MVP. A future adapter could dispatch a bounded Letta worker while SwarmAI keeps mission leases and permissions. Integration cost: high relative to using the current Python stack, including overlapping identity, scheduling, memory mutations and delegation. Its claims of learning need independent behavioral evaluation, and its context compaction is not the user's X/Y two-stage trainee succession contract.

##### Honcho — future peer-learning experiment; AGPL-3.0 core

Honcho models peers, sessions and changing representations, with background inference and querying across these records. The current official core repository says AGPL-3.0. [Official repository and license](https://github.com/plastic-labs/honcho).

Recommendation: later, if evidence shows that SwarmAI's simple subject-specific peer experience records are inadequate. Relevant to asking for help and trading lessons, but inferred beliefs about peers must not become permission decisions or unconditional facts. Integration cost: medium to high: another service, inference consumption, derived state and product-license compatibility to evaluate. Do not label it MIT/Apache from an old summary or add it merely because Hermes optionally supports it.

#### Considered orchestration alternatives

CrewAI's open-source framework is MIT and provides agents, tasks, crews and flows. Its repository distinguishes its commercial AMP control plane from the framework. [Official repository](https://github.com/crewAIInc/crewAI). It is a useful SDK/UI product benchmark, but importing its core abstractions would pull SwarmAI back toward crew/task ownership the user has deliberately removed. No runtime dependency recommended.

LangGraph is MIT, can operate without LangChain, and provides stateful graph execution, checkpoints and interrupts. [Official repository](https://github.com/langchain-ai/langgraph), [persistence docs](https://docs.langchain.com/oss/python/langgraph/persistence). It is a credible replacement candidate if the bounded PydanticAI/DBOS prototype cannot meet the requirements. It should not be an additional orchestration owner. A migration should require a specific failed requirement, a reproducible comparison, and a single selected runtime afterward.

#### Integration ownership and implementation order

1. Lock the stack and build one fake-model agent-turn adapter plus DBOS restart/cancellation spike.
2. Connect authoritative mission/agent/session/message/effect records to PostgreSQL.
3. Connect the separate inference router with correlation IDs, streamed tool calls, cancellation and factual usage. No Swarm-side LiteLLM proxy or provider-fallback loop.
4. Implement generic MCP client execution through the same effect boundary.
5. Implement memory IDs, cues, dereferencing, permissions and corrections using database records and exact/full-text retrieval.
6. Implement X/Y succession and first/delta KT, using those records and fenced ownership transfer.
7. Instrument all paths with OpenTelemetry and render the product's event journal in its UI.
8. Only then benchmark pgvector and a memory engine; introduce one only if measured benefit exceeds complexity.

At each stage distinguish installed, adapter-tested, integrated in a real mission, and live-qualified. None of these libraries supplies the entire requested social-learning engine or the specific trainee succession protocol. SwarmAI must implement and test those product behaviors.

---

## Part IV — Independent acceptance-scenario review

Proposed tests and acceptance evidence only; no code or tests executed in this review. Stack assumptions: native PydanticAI/DBOS execution, PostgreSQL domain authority, separate inference_server service. All agent work serves one collective mission. Humans may dictate initial agents. Crews are not a required entity. Source baseline and known gaps are in `work/source-map.md`.

Evidence classes:
- **D: deterministic integration** — real Swarm API/services/PostgreSQL/DBOS and a scripted fake model/router; real local fake MCP servers as specified. Proves mechanics, enforcement, restart behavior. Does not prove autonomy or learning.
- **M: actual-model behavior** — authorized model calls through inference_server, with task materials/final verifier held separately. Preserve exact model/route/config versions, prompts/context references, tool/message events, costs/unknown costs, evaluator results. Proves observed behavior in these cases, not universal reliability.
- **U: user surface** — real UI and SDK against same service, no UI fixture mode. Preserve browser interaction plus API/event evidence.
- **O: optional integration** — only when selected for a later packet or explicitly included; never a prerequisite that forces an optional framework into core.

| ID | Setup | Action / failure injection | Required assertion | Proof |
|---|---|---|---|---|
| A01 Human-selected seeds and one shared goal | Mission with human-selected Analyst A and Builder B, distinct personality profiles, bounded resource policy. Include a task that can be completed by either agent. | Start through API; ask A a clarification; try an undeclared seed/profile replacement and a child request with a contradictory top-level objective. | Initial identities and pinned profile versions match human selection. Human instruction is delivered and versioned. All descendants reference the same mission goal/revision. Contradictory proposal becomes a visible conflict/request, never silently replaces collective goal. No mandatory crew or manager created. | D + U; M for observed response to instruction |
| A02 Autonomous useful division and peer help | Small novel problem with two independently useful work portions and an uncertainty only a peer can help investigate; peer directory exposes capabilities but no preselected collaboration script. | Run multiple held-out task variants with actual model. Agent may work alone, ask peers, or request children. Do not instruct a precise delegation sequence. | At least one useful delegation and one agent-chosen peer consultation arise across the suite, with decision rationale summary and outcome. Total mission acceptance is externally checked. No score for number of agents; unnecessary delegation/cost is visible. Scripted model version separately proves dispatch mechanics only. | D then M |
| A03 One collective goal under local-task temptation | Parent assigns a child to optimize one component; test fixture includes a local optimization that harms a frozen mission constraint. | Offer attractive local result that violates global quality/compatibility requirement. A second agent flags the conflict. | Child and parent retain mission constraints in context; local task completion cannot accept the mission. Agents revise/reject/escalate based on evidence. Record disagreement and resulting decision without altering acceptance criteria to fit result. | D for immutable criteria; M for judgment |
| A04 Delegation admission and concurrent ownership | Two agents see same open work, enough capacity for only one child, finite depth/call budget. | Simultaneous spawn/claim requests; repeat same request after lost acknowledgment; child requests broader scope. | One durable owner per work item and one child per idempotency key. Limits enforced atomically. Broader scope rejected; agent receives actionable status. Rejected work can be reconsidered without duplicate hidden child. Logical agents, active generations and in-flight inference counted separately. | D with PostgreSQL concurrency |
| A05 Reliable communication without broadcast overload | Three agents with inboxes, mission announcements, requests, and replies. | Send direct request, reply, global instruction and 100 irrelevant messages; disconnect receiver after delivery before acknowledgment. | Ordered per-recipient sequence, no loss on reconnect, duplicate delivery handled once, request/reply correlation persists. Context contains relevant messages and pinned instructions within budget. "Delivered", "read by runtime", and "agent acknowledged" distinguished. No inference that an unanswered message was understood. | D + U |
| A06 X% crossing triggers first KT exactly once | Configurable small context window, X<Y, one active agent and capacity reserved for one trainee. Seed pinned instructions, findings, disputed memory and open promises. | Cross X exactly; repeat event; jump from below X to above Y using bounded oversized tool result. | Exactly one succession record and trainee generation. Initial KT contains goal, constraints, active ownership, inbox cursor, unresolved commitments, decisions with evidence, cue versions and uncertainties. Tool output is externalized/truncated before losing transfer reserve. Thresholds calculated against usable input budget consistently. Trainee is distinguishable from delegated task child. | D |
| A07 Trainee shadow and teach-back | Succession at X underway; trainee has initial KT and read-only/shadow capabilities. | Parent receives correction, peer request and tool result after first KT. Trainee asks questions and attempts a write/tool mutation. | Trainee receives ordered deltas and can ask questions; consequential action rejected until promotion. First KT + delta reconstructs changed facts. Teach-back states current goal, next action, constraints, pending effects/requests; mismatches are corrected and retained. Actual-model checks score factual recall and task continuation, not hidden reasoning similarity. | D + M |
| A08 Y% final KT and atomic promotion | Parent has a trainee ready and one pending request plus a tool action in flight. | Cross Y; final KT; pause/crash just before and just after generation transfer; let old parent submit a delayed action/result. | Parent stops taking new work at Y. Transaction advances active generation once with final KT digest/event watermark/inbox cursor. Old generation cannot mutate memory, claim work, send new commitments, or execute effects. Existing unknown effects reconcile by prior effect ID. Successor retains logical agent identity and new generation/session provenance. Exactly one active owner after recovery. | D with PostgreSQL/DBOS crash-restart |
| A09 Failed KT or missing trainee capacity | X crossed while normal worker capacity full; then Y reached with incomplete/failed teach-back. | Trainee start fails, KT inference times out, or a large tool response exceeds predicted tokens. | Reserved succession capacity or explicit queue behavior documented and exercised. Mission visibly pauses/blocks affected agent before exhausting context; no blind promotion or unlimited parent continuation. Other independent agents can continue. Human can inspect reason and retry/replace through same recorded process. | D + U |
| A10 Reference memory retrieval and budget | Long memory contains many irrelevant items, a relevant cue, corrected versions, and a contradictory source. Active context has finite cue allowance. | Agent notices a cue, fetches exact referenced record, requests more details, later starts another turn. | Context carries small informative cues with ID/version/digest; dereference loads only permitted relevant content. Cue existence means remembered record exists, not that claim is true. Active facts needed now may remain inline. Entire request (messages, schemas, retrieved content, reserved output) stays within enforced budget. Report retrieval round trips, tokens and task quality versus full-history baseline. | D; M for efficiency/quality tradeoff |
| A11 Correction, tombstone and invalidated cues | Several agents hold cues/derived lessons referring to memory v1. Reviewer or human corrects source to v2, or deletes/restricts source. | Fetch using old cue; replay cached request after deletion; have trainee receive old KT reference. | Version remains auditable where permitted, newest status clearly returned; superseded/invalid cues do not silently serve old claim as current truth. Dependent summaries/lessons marked for revalidation. Deleted or newly denied data does not leak through cue titles, snippets, search results, KT or artifacts. | D + U |
| A12 Learn from an apparently unqualified peer | Agent faces novel issue; generalist peer has a relevant observation but low/no evidence of expertise in that domain. Another peer offers confident wrong advice. | Agent freely selects whom to ask. Include task variants so always asking a named peer fails the suite. | Access and mission membership determine communication eligibility, not expertise rank. Agent tests advice and records the evidence/outcome. Correct unexpected idea may be adopted; confidence/authority alone cannot certify false advice. Rating updates are domain-specific evidence, not permanent global labels. | D for eligibility; M for social behavior |
| A13 Learning changes later action and supports rollback | Retain experience from A12 as provisional lesson with conditions, provenance and uncertainty. Prepare unseen similar and superficially similar-but-different tasks. | Compare fresh/no-lesson and learned variants with matched model/config and held-out cases; introduce false or stale lesson. | Learned agent uses lesson appropriately on later case without human restating it, while recognizing a non-applicable case. Record correctness, latency/tool/model cost and failure rate with raw per-case results. No claim of improvement based only on stored lesson or state transition. False lesson is challenged/quarantined/superseded and reversal retained. Weight updates are never claimed. | M plus D for lesson state and rollback |
| A14 Generic MCP across two unrelated servers | Two local fixture MCP servers with different tool schemas, one read-only resource/search and one mutating record tool; tools discovered dynamically. No Linear dependency. | Initialize/list/call, tool schema/list change, malformed arguments, transport loss, timeout after server mutation before response, malicious instruction text in result. | Standard transport/session behavior and schema validation. Namespaced tool identity; runtime-owned grants applied before call. Connector output remains data. Unknown mutation is recorded and reconciled if supported; no automatic re-execution or fabricated success. Secrets absent from model/context/logs. Both servers usable without app-specific source changes. | D + U; optional separately authorized real MCP server evidence |
| A15 Router boundary and changed context capacity | Fake inference_server returns model capability/window metadata, route fallbacks, streaming tool calls, usage and missing/unknown cost. Swarm has no provider keys. | Router unavailable; smaller-window fallback; disconnect after dispatch; cancellation while request in flight; unknown model metadata. | All inference goes through router. Swarm preserves correlation/attempt IDs and requests adequate capabilities. Before fallback invocation context is checked or incompatible fallback denied; no silent direct-provider call. Usage and unknown billing outcomes persist accurately. Application retry cannot cause hidden duplicated non-idempotent work. | D; authorized M connector acceptance separately |
| A16 SDK/UI identity and restart continuity | Same saved MissionDefinition with seed agents, profiles, X/Y settings, cue budget and MCP connections. | Create in UI/read and start in SDK; create in SDK/read and start in UI; send human message; restart services during run; reopen result. | One definition/version and run ID, same behavior/config, durable agent/message/delegation/succession/memory/lesson events. UI counts from actual service events, never fixtures. Final artifacts reopen with checksums; no lost accepted worktree result. All operations use common application service. | U + D |
| A17 Optional Hermes seed interoperability | Only if later selected: Hermes is a user-selected planning seed or external worker behind adapter; native seeds always supported. Grant bounded planner/read capabilities initially. | Hermes proposes tasks/memory lessons, requests prohibited action, fails mid-response; repeat same proposal. | Swarm owns mission, identity/generation, messages, memory, scopes, state and acceptance. External seed cannot dispatch outside core admission or run hidden consequential tools. Import is typed/provenance-tagged; uncertain external capabilities cause adapter to reject unsupported mode. Failure doesn't strand native agents. Hermes absent still passes all core tests. | O; D mechanics plus M actual adapter behavior |
| A18 Whole mission evidence and human steering | End-to-end mission needs discovery, useful delegation, peer consultation, one memory lookup, one corrected lesson and forced X/Y succession. Frozen acceptance conditions, finite budget. | Human redirects priority mid-run without changing authorized goal; restart once; stop another run during pending action. | Completed run's externally checked artifacts satisfy final authorized goal and recorded criteria. Budget/cancel/authority holds through restart and takeover. Every acceptance result tied to run, artifacts, verifier and config; no self-certification using caller-supplied matching checks. Failed/cancelled/unknown runs remain distinct evidence. Capture actual-model and deterministic results separately. | D + M + U |

#### Decisions that must be frozen before a smaller executor starts

The executor should receive decisions, not vague placeholders. Suggested defaults below are design proposals; the user's hard requirements are mandatory succession at X/Y, agents as individuals, human-selectable seeds, shared collective goal, agent-selected delegation/peer help, reference-based middle memory and experiential/social learning.

1. **Logical identity at succession.** Preserve `agent_id`, human-defined personality/profile and commitments; create new `generation_id`/`session_id`, link parent→trainee, fence the previous generation. Delegated child gets a new agent_id. This operationalizes "subagent becomes the agent" without losing provenance. Do not make the trainee create its own trainee while shadowing; if its context fills, rebuild/replace it under the same succession record.
2. **Threshold math.** Propose X=60%, Y=80% as configurable initial values, not asserted optimal values. Define usable input capacity = model window minus reserved maximum output and runtime safety margin. Occupancy includes instructions, tool schemas, messages, fetched memories, images/token estimates, pending tool returns. Preflight projected occupancy before call; measured provider count updates estimate after call. Unknown context limit blocks dispatch rather than inventing a capacity.
3. **Admission order at Y.** Pause parent new tasks/model work; allow only final KT/necessary resolution within reserve. Use one PostgreSQL transaction to commit final KT reference, last-observed event watermark, inbox cursor and active generation. No new mutating tool execution between handoff freeze and transfer. Existing effects keep effect identity and reconcile; do not reissue under successor ID.
4. **Trainee readiness.** Deterministic completeness checks require pinned mission/profile/scopes, owned task IDs, pending requests/effects, current instructions, conflicts, source refs and next action. Model teach-back graded for factual consistency against those records; this is a handoff quality check, not proof of every belief. Failure yields visible pause, not silent promotion. Specify retry bound and human override semantics.
5. **Agent autonomy loop.** Provide action affordances rather than fixed conversations: inspect/work, ask peer/human, inform, propose/delegate, retrieve, reflect/teach, yield/wait and finish contribution. Agent chooses next action. Kernel enforces authority, capacity, delivery, shared ownership and final acceptance. Personality affects selection/tone but never permissions. Do not require a manager or default crew.
6. **Human-selected seeds versus automatic seeds.** Define explicit seed list as authoritative; omitted list may use default/automatic selection. Freeze profile/model requirements per run. New instructions to one agent can change its assignment within mission scope; a conflict with collective goal triggers a visible clarification/mission amendment. Do not silently treat a private message as a mission-wide authority update.
7. **Sharing and source confidence.** Default common mission findings and commitments are discoverable to permitted mission agents; private working notes remain agent-scoped until deliberately shared. Durable memory has explicit project/mission/agent scopes, version/digest, producer/source and correction lineage. Source exists is not source verified. No raw private chain-of-thought requirement; record useful rationale summaries and observable evidence.
8. **Cue budget and retrieval.** Set cue budget as percentage or absolute cap of usable context, not of ever-growing disk storage; e.g. initial 5% configurable. Reference index remains durable outside context. Pin immediate constraints/facts inline. Decide lexical search first with optional later semantic retrieval; measure before adding another vector DB. Fetch operations and result token caps need defaults, as does policy for vanished/restricted refs.
9. **Persistence and execution ownership.** PostgreSQL domain tables authoritative; DBOS private workflow tables provide replay/dispatch. Use durable effect/inference/message receipts to avoid repeated side effects. One in-process or service coordinator for MVP; no second workflow engine or external issue tracker as authority. Kernel-only authority does not mean a manager model must approve every thought.
10. **Router contract.** Freeze versioned API fields for model/context/tool/structured-output capabilities, request/attempt IDs, usage, route/fallback history, cancellation and unknown outcome. OpenAI-compatible chat alone may not carry all metadata. No fallback owned in both repos; Swarm controls mission envelope, inference_server controls upstream routing. Missing real credentials must not block local deterministic implementation.
11. **MCP scope.** Choose standard local stdio plus HTTP transport support explicitly; connections/secrets owned by service, not passed to model. Dynamic tool discovery metadata comes from untrusted server and cannot define permission by itself. Mutating tool classification/approval policy is operator config. MCP does not itself provide idempotency or reconciliation; unsupported uncertain effects stay unknown.
12. **Learning acceptance.** MVP learning is retrieval/adoption of evidence-backed procedures/preferences, not training weights. Make human-visible per-case before/after results mandatory. Freeze a small held-out suite (suggest at least 5 cases × 3 seeds/runs per condition for observed comparison, no claim of statistical significance by default); avoid exact dialogue or fixed route/agent assertions. The suite must include a false lesson and unfamiliar peer helping.
13. **Hermes boundary.** Optional external seed/worker is later integration unless current native runtime cannot support a required behavior. Verify Hermes can operate in bounded planner/tool-free mode and expose required state/provenance before integration. If it cannot, use it for design/reference evaluation only. Do not embed its independent memory/tool/automation engine as hidden authority.
14. **Authorization and proof gates.** Deterministic local development can complete independently. Actual model and real external connector calls run only under the user-authorized environment/budget; label missing live evidence blocked, not failed or passed. Do not make every individual agent request or lesson need human approval—the user asked for autonomy. Restrict approvals to actual authority boundaries or user-selected policies.
15. **Branch and scope handoff.** `inference_server/dev` is independent. SwarmAI has no existing remote dev at inspection. Specify new Swarm branch from verified main and donor tests, then a single integration owner. This plan does not retroactively accept existing V1.7/V3 claims or override archived evidence.

#### Acceptance traps to prevent

- A scripted fake model choosing help/delegation/lesson adoption is wiring evidence, not autonomous behavior evidence.
- A JSON KT blob or "ready" flag alone does not show the successor can continue; require post-takeover task progress and preserved constraints.
- A reference index's existence does not show retrieval correctness or prove referenced memories true.
- A successful MCP echo cannot establish generic MCP support; use real protocol handshakes and two distinct schemas/transports in local integration.
- A dashboard showing data is insufficient when fields are fixture-filled or reset to zero by mapping code.
- Model repetition is not independent evidence; record correlated runs honestly and use task variants/held-out inputs.
- Swarm-wide global message replication can consume context faster than succession fixes it; relevant delivery/context budget is an explicit contract.
- Persistent sessions and logical identities are not process workers. Resource counts and lineage must distinguish them, particularly during parent/trainee overlap.
