# SwarmAI MVP implementation packets

Version 1 · 25 September 2026 · Execute against [the product plan](SWARMAI_MVP_PLAN.md). This is a proposed build queue, not a completion report.

## How to use this queue

Use one integration owner. A smaller executor should complete one packet at a time, retain evidence, and checkpoint before proceeding. Independent workers may implement disjoint packets after their prerequisites pass; only the integration owner edits shared contracts/migrations, resolves conflicts, and records integration acceptance. Do not dispatch a second product worker into a checkout already owned by someone else.

Every packet returns:

```text
Packet ID and status: planned | implementing | implemented | verified | review_pending | accepted | blocked
Source base, implementation branch, commit SHA, dirty-state explanation
Files changed and behavior delivered
Commands/checks actually run, exact outcomes, skips and reasons
Evidence files: scenario inputs, event/receipt IDs, artifact hashes, redacted logs
Known limitations, unresolved risks, and next packet
Any changed design decision and why
```

Keep these in `docs/swarm-mvp/packets/Pxx.md` (new), with an index in `docs/swarm-mvp/STATE.md`. Store synthetic/redacted test evidence under `docs/swarm-mvp/evidence/Pxx/` or CI artifacts; do not commit secrets, raw customer prompts, model credentials, or huge generated recordings. Keep operational/runtime databases out of Git.

### Common rules

- Python package targets below use the `src/swarm/` prefix unless that full prefix is already shown: for example `api/store.py` means `src/swarm/api/store.py`, and **new** `runtime/agent_loop.py` means `src/swarm/runtime/agent_loop.py`. The same convention applies to contracts, db, mission, controller, tools, providers, broker, workers, knowledge, memory, learning, workspace, extensions, spike, sdk, and `cli.py`. Paths beginning `tests/`, `docs/`, `apps/`, `.github/`, or `migrations/` are repository-root paths. Never create parallel top-level Python packages from these shorthand targets. Files explicitly labeled **new** are proposed. Reuse an adequate existing module instead of creating a competing implementation.
- Generate shared schemas/types from one source. Avoid manual API/SDK/UI field duplication.
- Fake dependencies are injected explicitly. Operational startup must reject no-op dispatchers, simulated tool adapters, missing required persistence, or unqualified runtime configuration.
- A packet is not done because a class or screen exists. Its listed scenario must run through the application boundary and retain proof.
- New code uses the repository's current lint/type/test/build commands. Update CI collection deliberately; do not hide failures by dropping directories or adding blanket skips.
- PostgreSQL/restart gates require a disposable real PostgreSQL instance. A skipped database suite or SQLite-only pass does not satisfy them.
- Do not make live inference, paid calls, real external writes, deployment, publication, or main merges part of an unattended packet. Those need existing explicit authorization. Keep all local/fake work moving meanwhile.
- The quoted router transcript does not authorize this executor to take over inference_server, merge its branches, or push SwarmAI changes automatically. Repository publication follows the actual execution assignment.

## Dependency map and milestones

| Packet | Prerequisites | Result |
|---|---|---|
| P00 | None | Fresh source/owner baseline and recorded decisions |
| P01 | P00 | Existing false-completion/artifact/scope hazards contained |
| P02 | P00 | Shared contracts and invariant definitions |
| P03 | P01, P02 | PostgreSQL authority and restart-safe repositories |
| P04 | P02, P03 | Qualified native/DBOS adapter and real outbox dispatch |
| P05 | P02, P03 | Inference-router contract client and context metadata |
| P06 | P01, P03 | Single effect/tool boundary and containment |
| P07 | P03 | Durable peer communication |
| P08 | P02, P03, P05 | Reference memory and context accounting |
| P09 | P04–P08 | Native agent vertical slice and seed selection |
| P10 | P09 | Autonomous delegation and shared-work coordination |
| P11 | P07–P10 | Complete X/Y trainee succession |
| P12 | P07–P11 | Measured experience/lesson/adoption loop |
| P13 | P05, P06, P08 | Generic real MCP client |
| P14 | P09–P13 | Complete common API and Python SDK |
| P15 | P14 | Real visual product and cross-surface parity |
| P16 (optional) | P09, P11, P13, P14; UI enablement also needs P15 | Qualified Hermes planning seed or precise blocked result |
| P17 | P03 onward; finalize after P15 | Instrumentation, install/restart/migration/docs |
| P18 | P01–P15, P17 | Integrated local engineering acceptance |
| P19 (authorization-dependent) | P18; P16 only for Hermes cases | Actual-model behavioral evidence and operator handoff |

Suggested checkpoints: **M1** native durable mission (P00–P09), **M2** autonomous collaboration and continuity (P10–P13), **M3** SDK+visual local product (P14–P15/P17–P18), **M4** behavioral qualification (P19). Hermes is a parallel optional feature after the core contracts exist. M3 must pass with Hermes absent.

## P00 — Freeze source, ownership, and implementation baseline

**Purpose:** prevent the worker from building in a stale/dirty coordination checkout or applying inference_server branch instructions to SwarmAI.

**Read:** current repository instructions; root README/pyproject; active coordination status/owner; [source appendix](SOURCE_AUDIT_AND_RESEARCH.md); current main and V1.7 donor identities. Main at research time was `08b910f981eff2ab66873a71055090f2c60f2a91`; donor `4d16fe85188861df6e123b4454c6bdc416e6c639`.

**Actions:**

1. Confirm repository remote, current branches, local changes, active owner, and parent-directory instructions. Preserve all existing changes.
2. Create a fresh isolated worktree from verified main when execution is assigned. Proposed implementation branch: `work/swarm-agent-mvp`. This is a new Swarm branch; no assumed `dev` branch or main merge.
3. If main advanced, inspect changed files relevant to this plan and update the source map. Do not redo the whole audit without a concrete need.
4. Write **new** `docs/swarm-mvp/ADR-001-product-and-authority.md`, `DECISIONS.md`, `STATE.md`, `SOURCE_BASELINE.json`, and packet queue. Record that current user choices supersede crew-centric requirements for this build, while historical evidence remains unchanged.
5. Record exact resolved library versions/lockfile identity. Select the existing React/Vite/FastAPI/PydanticAI/PostgreSQL stack and one DBOS substrate; mark the required compatibility spike pending.

**Done means:** a clean implementation location, named owner, scope, source SHA, exact defaults, and packet queue are recorded; current checks and known failures are captured without claiming repairs. A conflicting live owner blocks edits to its scope, not further planning.

## P01 — Contain existing acceptance and artifact defects

**Targets:** `api/store.py`, `mission/runtime.py`, `mission/acceptance.py`, `controller/graph.py`, `tools/v17_gateway.py`, related tests. Inspect matching donor changes before implementing.

**Actions:** make operational completion depend on actual attempt/artifact/check IDs rather than caller-provided matching objects; retain backward compatibility only where it cannot manufacture acceptance. Preserve accepted/pending artifacts in managed storage before worktree cleanup. Check target path containment. Correct permission subset validation and reject graph operation kinds whose commit behavior is unimplemented. Ensure fixture acceptance endpoints cannot run as ordinary live routes.

Port bounded donor behavior with its regression tests, especially `test_review_grounding.py`, `test_defect_proof_gate.py`, `test_v14_materialization_repair.py`, `test_gateway_envelope_integrity.py`, and `test_single_consequential_path.py`. Do not merge the donor wholesale.

**Done means:** a forged completion request fails; a genuine verified attempt can complete; an artifact reopens with identical hash after worker shutdown; path escape and permission-widening attempts fail. Existing evidence files are not edited to show a new pass.

## P02 — Define stable agent, communication, context, and lesson contracts

**Targets:** existing `contracts/mission.py`, `knowledge.py`, `workspace.py`, `actions.py`, `provider.py`; **new** `contracts/agent.py`, `communication.py`, `succession.py`, `learning.py`; schema export tests.

**Actions:** introduce logical agent versus incarnation/generation; runtime/role/model separation; specified/automatic/mixed seeds; `delegation` versus `succession`; typed next-action proposals; durable message envelopes; context manifests; immutable cue refs; KT packet/readback/cutover fields; experiences/lessons/evaluations. Keep mission/task/attempt concepts where already adequate.

Specify legal state transitions and stable error codes. Define `AgentRuntime` as a Swarm interface supporting bounded execution, effective-context inspection/accounting, cancellation, persisted state export/import or reconstructability, and capability reporting. Method names are this project's contract, not claims about native Hermes methods.

**Done means:** representative definitions round-trip through schemas; malformed context policies, unauthorized fields, unknown action kinds, invalid transition requests, and duplicate IDs fail clearly. No new Crew entity. Exported client types are generated from the contracts.

## P03 — Connect authoritative PostgreSQL persistence

**Targets:** `db/models.py`, `db/repositories.py`, existing lease/fencing modules, `api/store.py`, `mission/store.py`, `api/events.py`; **new** focused repository modules and Alembic migration(s).

**Actions:** add/extend tables for lineages/incarnations, inbox deliveries, succession, context refs, lessons, runtime qualifications, and connection grants. Use domain transactions and unique constraints for one active generation, one open succession, idempotency, and task ownership. Convert ProductStore to a facade over services/repositories. Retire writable process-local/JSON authorities from operational routes; keep fixtures explicit.

Add durable mission events with monotonic sequence and transactional outbox. Implement optimistic revision conflicts. Define managed artifact publication and orphan reconciliation. Prepare a one-time legacy import that preserves source/provenance and reports unsupported records without guessing.

**Done means:** two concurrent workers cannot create duplicate ownership; duplicate API requests after service restart return the original logical result; event order and state survive full process restart; fresh DB and upgrade-from-baseline migrations pass. Destructive migration is not the default.

## P04 — Qualify native runtime and DBOS recovery

**Targets:** `spike/durable_agent.py`, `spike/broker_hook.py`, `db/outbox.py`, worker service/protocol; **new** `runtime/adapters/base.py`, `native.py`, `runtime/workflows.py`.

**Actions:** use pinned PydanticAI with a fake model and one bounded structured-action turn. Prove available APIs before changing dependencies. Add the DBOS durable workflow/step mapping, real enqueue callback, stable workflow IDs, and restart logic. Recheck cancellation/generation at every application commit. Wrap custom I/O durably; avoid unrecorded tool callbacks inside replayed model calls.

Production construction without an enqueue dispatcher must fail. Implement outbox acknowledgment only after a real durable enqueue response. Duplicate enqueue must address the same workflow intent. Document workflow versioning and how active runs are drained or migrated.

**Done means:** crash after model result persistence does not silently issue an extra model call; crash between domain commit and enqueue still dispatches; failed effect step yields known/unknown receipt and bounded recovery; cancellation of a blocked call prevents late domain commits. Keep observed upstream costs unknown where retry ambiguity exists.

**If the spike fails:** isolate the failing requirement, check supported pinned APIs, and record a small compatibility decision. Do not add a second runtime such as LangGraph alongside DBOS as an improvised fix.

## P05 — Add the inference_server client contract

**Targets:** `providers/`, `broker/`, `mission/brokered_inference.py`; **new** `providers/router_client.py`, `contracts/router_capabilities.py`, `tests/fixtures/router_http/`, configuration sample for context metadata.

**Actions:** use `/v1/models` and `/v1/chat/completions` with configured endpoint/credential reference; normalize outputs, tool calls, streaming, usage, router headers, error codes, cancellation, and unknown outcome. Swarm correlation IDs persist even when the router uses its own ID.

Disable framework/HTTP automatic retries and direct provider fallback in operational Swarm paths. Keep mission reservation/settlement; upstream retry/fallback belongs to the router. Qualify exact routes for capabilities and context. Until router metadata is sufficient, use evidence-backed pinned context overrides. Alias fallback requires an enforced immutable route set/revision and conservative per-route tokenizer counting. Otherwise use a pinned explicit route with fallback disabled and immutable router configuration. A local override cannot enforce remote routing; absent that guarantee, live qualification remains blocked while fixture development continues.

Create real local HTTP fixtures exercising partial streams, malformed JSON, tools, unavailable routes, rate limiting, missing usage, and smaller-context routes. Do not add upstream keys or provider adapters to Swarm.

**Done means:** every emitted model request is observed by the fake router; unknown metadata blocks; projected request size fits qualified route; fallback cannot violate privacy/billing/context; retry count and call costs are not multiplied or silently set to zero. Capture the cross-repo contract snapshot without modifying inference_server.

## P06 — Wire one tool/effect gateway

**Targets:** `tools/v17_gateway.py`, `tools/effects.py`, `tools/gateway.py`, adapters and candidate boundary/fence donors; **new** gateway application facade if required.

**Actions:** select the existing hardened gateway as the sole operational boundary. Bind action intent to identity/generation, mission, work attempt, grants, schema, target, argument hash and expiry. Persist action before dispatch; classify read/write/destructive effects with operator policy; reconcile uncertain remote outcomes. Gate local tools with real workspace/process containment. Preserve approval state across restart; only request approval when policy actually requires it.

Do not allow direct subprocess/file writes from the agent loop or an adapter. Test path containment against traversal/symlinks; tests should exercise an isolated filesystem/network boundary rather than merely inspect an environment variable.

**Done means:** a prohibited action cannot execute through old gateway, direct worker, or adapter paths; stale generation fails before new dispatch; timeout after fake remote mutation does not cause duplicate execution; authorized reads need no redundant human prompt. Trace proves every consequential call crossed the selected boundary.

## P07 — Build durable peer messages

**Targets:** existing event contracts/repos; **new** `runtime/communication.py`, message repository, API routes/tests.

**Actions:** authenticate sender server-side; route to logical identities; persist addressed message/delivery/reply/expiry states; implement durable per-recipient cursors, idempotent sends, acknowledgments, and relevant inbox batches. Keep shared announcements separate from direct questions. Add mission-scoped peer directory with subject experience and availability.

Implement operator interaction policy, limited broadcasts, debounce, request deadlines, and bounded wakeups. Everyone permitted can ask anyone permitted regardless of expertise rating. No semantic instruction in a message modifies grants/mission ownership. State-changing sends recheck current generation and cancellation at commit, including after replayed model results.

**Done means:** kill receiver after delivery and before acknowledgment; reconnect without loss/duplicate processing; answer links to question; one hundred irrelevant messages do not displace pinned constraints or produce an unlimited echo loop. No spoofed display name can send as another agent.

## P08 — Reference memory and context builder

**Targets:** `knowledge/repository.py`, `retrieval.py`, `budget.py`, `memory_adapter.py`, `workspace/context.py`; **new** `knowledge/cues.py`, `runtime/context.py`, `runtime/token_accounting.py`.

**Actions:** implement separate cue search and bounded source dereference with access checks before ranking/snippets. Reuse versioning/tombstones/contradictions. Track cue ancestry and invalidation on correction/revocation. Import old JSONL memory through a controlled migration; no second writable store.

Implement plan §8 budget formula and full request assembly manifest. Include runtime-added preamble/tool schemas and provider modality accounting; pin critical constraints; keep output/KT reserves. Count using qualified tokenizer or tested conservative estimate. Store giant results before excerpt selection. Count status is exact/estimated/unknown with reason. On access revocation invalidate affected context/KT caches, suspend their new use, rebuild from permitted sources, and quarantine late outputs; do not claim previously delivered content can be erased retroactively.

**Done means:** cue points to a real permitted version; correction and revoked access affect subsequent retrieval and dependent lessons; inactive full memory does not enter the prompt; current critical facts can remain inline; token limits apply to actual assembled input. Compare retrieval overhead to a full-history fixture without claiming an unmeasured quality gain.

## P09 — Deliver one native autonomous-agent vertical slice

**Targets:** `mission/runtime.py`, `api/store.py`, CLI; **new** `runtime/agent_loop.py`, `mission_service.py`, profile registry and admission service.

**Actions:** replace fixed operational inspect/implement/verify/review execution with the bounded action cycle. Add create/start/wait/pause/resume/cancel transitions; save specified or auto-selected seeds; instantiate profiles without overriding user fields. Use durable work claims, messages, memory retrieval, gateway tools, router inference, and visible reasons for waiting.

Use fake structured model decisions for deterministic mechanics. Every output is a proposal checked by the kernel. Preserve mission constraints in every context. Action selections can vary; no hardcoded collaboration dialogue. Keep repository repair as an example tool/scenario.

**Done means:** a mission started from the API persists two selected agents, performs useful fixture work, exchanges a question/reply, retrieves evidence, publishes a verified artifact, and resumes after backend/worker restart. Contradictory local subgoals cannot replace mission intent. This gate proves mechanics, not actual-model autonomy.

## P10 — Dynamic work graph and agent delegation

**Targets:** `controller/graph.py`, `scheduler.py`, `resource_allocator.py`, existing lease modules; **new** `runtime/delegation.py`.

**Actions:** implement only supported graph operations with transactional revisions, actual dependency checks, cycle prevention, and scope subsets. Admit typed spawn proposals; create a new logical ID; inherit bounded mission context/grants; track parent relationship without dependence on parent process life. Implement single-host fair queues, worker/call/spawn/depth budgets, and duplicate admission handling.

Define no-progress handling and reasons for refusal/wait. Resource ownership and deadlines persist across restarts. A child can report to the mission when its parent retires. No artificial requirement that agents always delegate.

**Done means:** simultaneous claims/spawns consume one available slot once; no oversubscription; dependency failure blocks dependent work; one noisy swarm cannot starve another; child result survives parent replacement. Real model judgment is evaluated later.

## P11 — Implement mandatory trainee succession

**Targets:** **new** `runtime/succession.py`, KT/readback services; extend incarnation/lease/message/context repos and DBOS workflows.

**Actions:** implement all plan §9 states, including concurrent threshold triggers, one open succession constraint, reserved trainee capacity, KT1, shadow deltas, explicit readback, final KT2, quiescence/reconciliation, and atomic promotion. Use logical ID continuity with new incarnation/generation. Separate delegation accounting from succession costs. Recheck all permissions after transfer.

Default readiness: all required factual fields present; no missing critical permitted evidence; current goal/constraint/work IDs agree with authoritative records; pending questions/effects enumerated; next-action proposal stays within mission; trainee below X after compact transfer. Allow at most two bounded KT correction attempts before visible blocked state; operator retry can start another recorded attempt, never force an unchecked hidden promotion.

At Y or predicted overshoot stop parent ordinary work. Select a finite KT cutover watermark; material goal/permission/work changes invalidate readiness, while ordinary later messages queue for the successor. Continuous chat cannot postpone promotion indefinitely. An emergency transfer records gaps honestly; source constraints still have to pass before promotion. Trainee never recursively spawns a trainee while shadowing. Final-KT budget exhaustion pauses.

**Done means:** exact X and Y, X→Y jumps, giant tool result, trainee crash, unavailable capacity, old-parent delayed commit, new message during cutover, and process death on both sides of commit all preserve one active generation and the work/inbox. Successor demonstrably completes subsequent work; a saved KT blob alone is insufficient. Unknown consequential effects are reconciled or block dependent takeover/actions.

## P12 — Implement experiential and social learning

**Targets:** `learning/__init__.py`, knowledge/provenance; **new** `learning/experiences.py`, `lessons.py`, `evaluation.py`, `adoption.py` and restricted skill export/import.

**Actions:** persist situation/action/outcome records and provisional lessons. Add scope/preconditions, source ancestry, contradictions, independent evaluation, limited canary, adoption version, actual use receipts, invalidation and rollback. Use teaching/question messages to propose transfer. Track expertise by topic with evidence/sample count/freshness.

Define protected fixed rubrics and held-out cases. Prevent proposing agents from modifying check outcomes or granting their own promotion. Allow automated scoped adoption after policy-defined evidence without requiring a human approval for every ordinary lesson. Protected permissions/budgets/identity are never learned away.

**Done means:** fixtures prove candidate→evaluated→adopted→used→rolled-back mechanics; false/superseded lessons are quarantined; low-expertise peer advice can enter an evaluation; copied endorsements are not counted as independent evidence. Actual behavior improvement remains an explicit P19 gate.

## P13 — Replace simulated MCP with generic connections

**Targets:** `tools/adapters/api_mcp.py`, extension manifest/config concepts; **new** `tools/mcp_client.py`, connection repository/services, fixture servers.

**Actions:** implement standard stdio and Streamable HTTP clients using a pinned compatible official SDK. Persist connection metadata and secret refs; initialize/negotiate, discover paginated tools/resources/prompts, namespace and hash schemas, invalidate grants on schema change, handle cancellation/disconnect. Reject unsupported server-initiated capabilities; don't silently run sampling outside the router.

Map tool execution through P06 and result bodies through P08. Treat prompts/resources/tool text as untrusted data. Keep canonical server/tool/schema identity and a model-compatible alias map in each context manifest; resolve returned calls only through that map. Add UI/API-facing capability and error model. Move echo transport to an explicitly named test fixture.

**Done means:** two unrelated local MCP servers, using different schemas and both transports, work without app-specific code; one supplies resources/prompts and one read/write tools. Test malformed args, changed tool list, hostile instruction text, disconnect, cancellation, huge result and timeout-after-write. No Linear dependency, leaked credentials, or assumed remote idempotency.

## P14 — Finish common API, CLI, and Python SDK

**Targets:** `api/routes_v1.py`, `schemas.py`, `errors.py`, `events.py`, `auth.py`, `cli.py`; **new** `sdk/client.py` and examples.

**Actions:** expose all operational lifecycle/profile/runtime/message/memory/lesson/connection/receipt services through the shared API. Implement resumable committed-event SSE, pagination, stable errors, revision conflicts, and auth/scope tests. SDK is an HTTP client with typed models and sync/async usage appropriate to current stack; it does not launch a separate engine implicitly. CLI calls the same operations.

Add examples: native fake mission; human-specified seeds; peer help/delegation; memory correction; forced succession using a small test window; optional Hermes only when qualified. Clearly separate illustrative pseudocode from tested examples.

**Done means:** SDK creates and starts a mission, reconnects events after restart, sends operator message and cancels correctly; saved definition round-trips without loss; invalid runtime/capability gets actionable error. Generated types match OpenAPI; no caller-supplied proof can complete a mission.

## P15 — Complete the visual product

**Targets:** `apps/console/src/App.tsx`, API client, existing components/routes; new views as needed. Reuse the current React/Vite tooling.

**Actions:** implement all required plan §14 screens using real API projections. First build create/run/observe/pause; then messages and work graph; then context/KT/memory/lessons/connections. Runtime/model/personality fields are independent. Distinguish delegation from succession, worker count from model concurrency, estimates from known usage, and blocked from failed.

Give human overrides concrete versioned actions. Show Hermes as unavailable with reason until qualification; allow native default. Clearly label fixture/demo mode. Keep product-facing text practical; internal IDs/details can be expandable diagnostics.

**Done means:** automated browser checks against the local real backend and fake external dependencies prove UI→SDK and SDK→UI continuity, reload/reconnect, actual task/agent counts, human messaging, memory correction, visible KT progression/cutover, and final artifact access. Console lint/test/build pass; no fixture data satisfies this gate.

## P16 — Optional Hermes planning-agent adapter

**Targets:** **new** `runtime/adapters/hermes.py`, isolated adapter packaging/config, runtime manifest and tests; UI runtime choices from P15.

**Actions:** choose a pinned Hermes version after reading its actual constructor/run APIs. Begin with bounded planning turns returning structured plans, questions, peer-message intents, permitted reads, and delegation proposals. Enforce limits explicitly. Verify empty/selected toolsets against effective capabilities; prompts alone do not restrict Hermes.

Disable or map its tools, memory/skills writes, compaction, children, auxiliary calls, cron/background jobs and fallback. Whole-process isolation plus egress restriction covers bypass paths. Swarm context accounting includes Hermes preamble; fresh requests cannot reset the logical context meter. Persist Swarm session state sufficient for restart and KT. Cooperative stop remains `stopping` until effective termination/fencing is confirmed.

**Done means:** mixed native/Hermes seeds exchange messages, propose work and use memory through the same kernel; all inference reaches the fixture router; forbidden tools/children/background writes never execute; two profiles remain isolated; X/Y and crash/takeover tests pass; Hermes absence preserves all native tests. Record qualified capabilities/build/config/route evidence and limitations. Live availability requires applicable live qualification; fake-only mode is labeled.

**Stop condition:** an unobservable call/effect/context boundary or invasive required fork makes the adapter unavailable with a precise report. Do not weaken core contracts to get a Hermes badge. No claim of performance advantage without a measured comparison. More capable Hermes tools can be qualified individually later.

## P17 — Observability, installation, and operational continuity

**Targets:** configuration/settings, logging/instrumentation, existing scripts, CI, docs; **new** local development compose/setup only where needed, operator guide and recovery runbook.

**Actions:** instrument each packet as it lands; finalize OTel span conventions and durable event projections. Add metrics defined in plan §16, with truthful unknown values. Provide a documented local install/start/stop/check/recover path for backend, worker, database, console, fake router and fixture MCP. Bind locally by default; require auth; secrets stay out of examples.

Back up/restore DB and artifact store consistently; verify restored hashes; document workflow upgrades, retention, crash recovery, unknown effects, and failed KT. Make health/readiness checks reflect dispatcher, DB, artifact store and runtime qualification. Router unavailability should be a visible capability/blocker rather than a fabricated success.

Update README/status/command maps so demos, integrated features, live qualification, and future work are distinct. Do not erase historical reports. Pin dependencies and run normal security/dependency checks relevant to added components without broad unrelated rewrites.

**Done means:** a fresh operator can run the offline example from documented steps; restart/restore preserves a mission and its artifact; missing configuration yields precise failure; traces correlate events across model/message/tool/KT boundaries without secrets. CI includes all relevant new and previously omitted suites.

## P18 — Integrated local engineering acceptance

**Targets:** **new** `tests/acceptance/`, PostgreSQL fixture/CI service, local MCP/router process fixtures, console E2E; protected scenario definitions.

Run the acceptance matrix below through actual entry points. Do not satisfy it with direct calls to state-transition helpers alone. Record exact dependency versions, source commit, fixture configuration, environment, runs/seeds, artifact hashes, events, errors/skips, and cost provenance.

Required gates:

1. Existing relevant regressions plus formatting/type checks and console lint/test/build.
2. Fresh migration and upgrade/restart with real PostgreSQL; no optional skip for durable claims.
3. At least two concurrent swarms with isolation, fairness, budget and cancellation checks.
4. Both SDK/UI workflows with no fixture mapping in live mode.
5. Faults before/after enqueue, ownership transfer, effect receipt, artifact publish, and event acknowledgment.
6. Forced X/Y succession with one late old-generation action and one unknown remote effect.
7. Memory correction/revocation and lesson invalidation through the same runtime.
8. Generic MCP fixtures with both transports; no dependency on Linear.
9. Native suite without Hermes. Separate optional adapter report if P16 is implemented.

**Done means:** all required deterministic acceptance assertions pass, failures are repaired with retained evidence, and an independent review verifies evidence/authority boundaries. If independent review is not available, report `verified; review_pending`, not accepted. Do not imply actual-model autonomy or live integration from this gate.

## P19 — Authorized behavioral qualification and final handoff

**Prerequisite:** explicit scope for real inference/connector use, allowed routes/data, call/token/spend limits, and no unauthorized external mutations. This plan does not supply those credentials or authorization.

**Actions:** run small held-out tasks through the same UI/SDK/runtime using actual models via inference_server. Suggested initial comparison: five task variants, three repeated runs per condition, with matched models and frozen rubrics; record model randomness/seeds when supported. Begin with a smaller smoke case to bound cost before the full matrix. This is observational evidence; do not claim statistical significance automatically.

Compare base agents against memory/lesson-enabled agents; include helpful advice from an unfamiliar peer, confident false advice, non-applicable lesson, collective-goal tradeoff, useful delegation, and forced successor continuation. Score artifact correctness first, then latency/cost and unnecessary communication/spawning. The evaluator must not require an exact dialogue or named peer choice. Evaluate Hermes separately if qualified; absence does not fail native product acceptance.

**Proposed behavioral pass rubric, freeze before running:** zero unauthorized effects/goal changes/false acceptances; at least 80% of held-out task runs pass their frozen outcome checks; useful agent-chosen peer help and useful delegation each appear on at least two distinct task variants; at least three forced-succession runs continue successfully with critical constraints preserved; lesson-enabled agents show the preregistered improvement on at least two unseen applicable cases against matched no-lesson baselines, with no critical regression and correct handling of the non-applicable/false-lesson cases. All runs stay inside the granted resource envelope. Define the improvement metric and acceptable cost change before seeing results. These are initial product thresholds, not a statistical significance claim.

**Done means:** publish a local evidence summary distinguishing mechanics, observed actual-model behavior, limitations, unrun gates, and operator acceptance. Show per-case outcomes and failed examples. Report `behavior_validated` only when the frozen rubric passes; a finished report with failed or inconclusive behavior is `evaluation_completed_not_validated`, and M4 remains unpassed. Do not loosen the rubric after a failed run and call the original evaluation a pass; record a new version and new evaluation. If authorization or credentials are missing, deliver the runnable local MVP, reproducible evaluation commands, required inputs, and exact pending gate. Do not invent successful provider or learning results.

## Acceptance matrix

Evidence: **D** deterministic integrated mechanics; **M** actual-model observations; **U** real UI/SDK workflow; **O** optional runtime. D uses real local PostgreSQL/DBOS/API and real protocol fixture processes, with fake inference. D never implies M.

| ID | Scenario / injection | Required result | Evidence / owner |
|---|---|---|---|
| A01 | Human-specified seeds; conflicting child objective | Exact selected profile versions persist; child retains collective constraints; no required crew/manager | D/U; P09/P15 |
| A02 | Novel split task, optional peer help, no conversation script | Across held-out cases useful agent-chosen delegation/help occurs; unnecessary spawning/cost visible | D wiring + M; P10/P19 |
| A03 | Local optimization harms global constraint | Frozen mission acceptance rejects violation; agents revise/escalate with evidence | D/M; P09/P19 |
| A04 | Concurrent claims/spawns; lost acknowledgment | One owner/admitted child per idempotency key; no scope/budget/depth widening | D PostgreSQL; P10 |
| A05 | Receiver crash after delivery; message flood | Durable cursor recovery, deduplicated processing, reply links, bounded context/wakes | D/U; P07/P15 |
| A06 | Exact X crossing, duplicate trigger, X→Y jump | One trainee/open succession, correct counts, retained constraints and KT reserve | D; P11 |
| A07 | Parent correction after KT1; trainee attempts a write | Ordered delta/readback catches change; trainee has no consequential authority | D/M; P11/P19 |
| A08 | Crash before/after cutover; late parent commit | One active generation, preserved logical ID/inbox, stale commits refused; successor does subsequent work | D; P11 |
| A09 | Trainee/capacity/budget failure; unknown external effect | Visible safe block; no unchecked promotion or duplicate effect; other independent work can continue | D/U; P11/P15 |
| A10 | Many irrelevant memories; cue and dereference | Bounded permitted cues/content, source version receipt, actual full-request limits | D; P08 |
| A11 | Correction/tombstone/access revocation during KT | No new leakage via cue/snippet/KT; stale dependent lesson revalidation; current version surfaced | D/U; P08/P11/P12 |
| A12 | Unexpected peer helpful; expert-sounding peer wrong | Asking allowed independent of expertise; advice tested, wrong assertion not certified by confidence | D eligibility + M; P12/P19 |
| A13 | Lesson adopted then unseen applicable/non-applicable cases | Observable later strategy change with evidence, measured quality/cost, incorrect lesson rollback | D state + M behavior; P12/P19 |
| A14 | Two MCP servers/transports; schema changes; timeout after mutation | Generic discovery/calls, host grants, no fake success, unknown/reconciled mutation, no blind retry | D/U; P13/P15 |
| A15 | Router outage, partial stream, smaller fallback window | No direct provider bypass; admission uses qualified limit; IDs/usage/unknown cost preserved | D; P05 |
| A16 | UI create→SDK start and reverse, restart/reload | Same definition/run/config, real agents/tasks/events, durable final artifact | D/U; P14/P15 |
| A17 | Mixed native/Hermes planning seeds; adapter missing/failing | Same authority/context contract, restricted capabilities enforced; native suite remains usable | D/O plus M when authorized; P16 |
| A18 | Whole mission, human steering, correction, delegation, KT and restart | Evidence-backed final artifact, correct budget/cancel behavior, no self-certified completion | D/U/M in separate reports; P18/P19 |

Expanded scenario rationale from the independent review is retained in the research appendix. Product plan defaults prevail over earlier brainstorming suggestions in research notes.

## Definition of the delivered MVP

The lower-capability executor should be able to hand over a fresh-checkout local product where the user defines individual agents in either Python or the UI, starts a collective mission, sees agents choose and coordinate work, inspects durable memory/lessons, observes trainee succession without ownership loss, connects generic MCP servers, and reopens verified artifacts after restart. Every advertised feature has a traceable acceptance result. Runtime/provider features awaiting qualification are clearly unavailable or labeled demo-only.

Passing deterministic scenarios establishes this executable architecture. Claiming useful autonomy and learning additionally requires the actual-model evidence in P19. Final handoff includes source branch/commit, runnable instructions, proof matrix, known limitations, pending authorizations, and an exact next step.
