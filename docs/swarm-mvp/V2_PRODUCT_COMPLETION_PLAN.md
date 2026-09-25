> **Execution priority update:** Read [CURSOR_FAST_TRACK.md](CURSOR_FAST_TRACK.md) first. The user subsequently requested speed, multitasking and skipping new mock/test-data projects. That file overrides conflicting scope, sequencing and qualification work below. This detailed document remains the architecture and interface reference.

# SwarmAI V2.0 product completion — Cursor execution contract

Date: 2026-09-25. Source review baseline: `4444a565cbe71dbf5f013e9bd6510c68c257e4b3` on `dev`.

**Task:** deliver the integrated, portable, persistent goal-pursuit product through V2.0. Close the independently reproduced defects, connect the existing modules into one operational path, and prove that path from a fresh install. This is one substantial execution program with bounded packets, not one giant unreviewed change. The plan reduces ambiguity; it cannot guarantee a single model response will finish the implementation.

Read `V2_PRODUCT_COMPLETION_REVIEW.md`, `V2_PRODUCT_COMPLETION_PACKETS.json`, applicable AGENTS instructions, CONTRIBUTING, STATE, existing V2_GOAL_PURSUIT_PLAN, ADRs and current branch status before changing source. This plan supersedes an "engineering exhausted / wait for LiveGrant" stopping point for independent work. Preserve applicable safety, ownership and tracking requirements. Reconcile any newer commits before applying review fixes; do not overwrite another worker's work.

## 1. Exact deliverable and boundaries

A user can install SwarmAI on a supported generic Linux container host, open its UI or use its SDK, configure an agent and a permitted model route, attach an outbound worker with bounded workspace access, and give a collective goal. SwarmAI persists that goal, plans useful missions, dispatches real work, receives immutable artifacts, verifies progress, recovers after restart, learns scoped lessons from evidence, and pursues remaining criteria until it succeeds, pauses, is cancelled, exhausts its envelope, or needs a clearly identified human decision. The UI reopens the same state.

No personal host, path, domain, account, tracker, provider or model is intrinsic to core behavior. R730, Mac and Cloudflare are optional reference configurations. Do not silently choose between the historically mentioned `.com` and `.ai` domains; public ingress is configured and verified separately. Generic tests use reserved example domains and temporary roots.

Capability milestones remain:

| Milestone | Required outcome |
|---|---|
| V1.7 | Complete a bounded mission with verified artifacts, worker control and context succession |
| V1.8 | Persist goals, criteria, decisions, mission links and continuity across restarts |
| V1.9 | Autonomously schedule and execute bounded cycles toward remaining goal criteria |
| V2.0 | Integrate those capabilities into an installable SDK + UI product |

V3 goal coordination and V4 delegated ongoing functions are out of scope. Also defer peer consensus, multi-coordinator failover, replicated writable memory, Kubernetes, model fine-tuning, a marketplace, and a new inference router. Preserve optional OpenCode/Hermes adapter interfaces; completing their live qualification is not a reason to delay a working native product. They must remain unavailable/unqualified until they pass the same kernel contracts. Do not add dependencies merely to rename existing functions.

## 2. Architecture decisions to implement

### One authority and one operational path

Use existing kernel/controller authority for lifecycle, graph changes, policies, budgets, leases, cancellation generations and acceptance. Reuse `src/swarm/db/{models,repositories,outbox,lease_fencing}.py`, existing tool gateway, broker, mission/controller and artifact implementations after inspecting their contracts. Do not build a second portable scheduler or demonstration server.

Operational path:

`UI / SDK / CLI → authenticated API → durable goal + policy → coordinator cycle → admitted mission + task graph → durable outbox / queue → eligible worker lease → runtime → broker and tool gateway → immutable artifacts → protected verification → criterion progress → next cycle / terminal state`.

SQLite/file JSON or in-memory modes may remain explicit test/demo compatibility modes. PostgreSQL is authoritative for the shipped server operational path. Do not run simultaneous writable JSON and PostgreSQL authorities for the same entities. Local artifact blobs may use a durable volume with transactional database metadata. A migration/import tool must make legacy ownership explicit.

Single active coordinator is sufficient. Use a database advisory lock or equivalent durable singleton lease plus per-cycle fencing to prevent a second process from scheduling duplicates. This is duplicate prevention, not automatic high availability. Two scheduler processes in tests must not both execute a cycle.

### Simulated inference is an injected dependency, not a simulated product

RecordingExecutor and fixture/demo paths are permitted only through explicit test/demo composition. The offline integrated campaign must call the normal native runtime, normal model transport/broker, tool gateway, artifact API and protected verifier. Only the provider response source is deterministic. A fake HTTP provider is preferable for the main deployed campaign so request serialization, streaming/errors and transport accounting are exercised.

Operational composition without a permitted runtime/route reports a typed blocker. It must never fabricate success, evidence IDs, spend or qualification. Dry-run must not mutate operational goal achievement. Store an execution provenance field so UI/report consumers can distinguish synthetic and live evidence.

### Stable domain contracts

Extend the canonical existing models; the field names below are semantic requirements, not permission to add duplicate classes:

- **Goal:** stable project/goal ID, desired outcome, kind, revision, typed criteria with stable IDs, authority/resource envelope, state, strategy revision, next wake, stop reason.
- **Criterion evidence:** criterion ID + version, verifier identity/version, input artifact digest, task/attempt/mission IDs, scoped receipt reference, verdict and time. Human-only criteria remain unmet until a real authorized decision exists.
- **Cycle:** goal revision, idempotency key, schedule reason, lease/fence, proposed/admitted mission, phase, retry/backoff, timestamps, conclusion and evidence.
- **Mission/task/attempt:** stable lineage, dependency graph, work requirement, actual route/runtime, delegated envelope, cancellation generation, lease expiry, artifact/result refs and immutable execution provenance.
- **Logical agent:** durable identity/personality/policy/goal membership. A worker is the executing process; an agent session is a replaceable context instance. Model, runtime and personality are separate fields.
- **Enrollment:** advertised OS/architecture/runtime, declared abilities, explicit permission grants, qualification evidence and expiry, effective scheduling capabilities, trust/locality, workspace grants and credential generation. Display names are not authority.
- **Resource reservation:** parent goal → mission → task/attempt/session; held versus settled calls/tokens/time/spend. Child creation reserves from its parent rather than copying the full budget.
- **Message:** authenticated sender/session, recipient(s), goal/project/mission, kind, correlation ID, event order, artifact refs, expiry and delivery cursor. Message text cannot grant access or mutate acceptance.
- **Memory/lesson:** scope, owner, source/event/artifact refs, confidence/status, version, invalidation/expiry, access checks, adoption/reversion evidence.

### Behavior and defaults

Use configurable defaults for a conservative native baseline: one active mission per goal, two active task sessions per mission, delegation depth two, at most eight sessions created per mission, two repair attempts per failed task, bounded model/tool calls and wall time. Existing stricter approved limits prevail. Default spend ceiling is zero; zero dollars does not imply unlimited calls. Default native task envelope: 12 model calls, 40 tool calls, 10 minutes; default goal envelope: 10 missions, 100 model calls, 400 tool calls and 60 active-execution minutes. These are implementation defaults, not authorization to make live calls. Persist reservations and expose limits in UI/SDK.

Schedule with UTC persisted deadlines and monotonic time for in-process durations. Inject clocks in tests. Wake on new evidence, worker availability, authorized resume and due time. Idle coordinator polling is bounded (default five seconds with notification wakeups where already available); failures back off through 5/15/60/300/900 seconds with capped jitter. After three cycles with no verified progress and no genuinely new approach, wait with a specific explanation. Ongoing goals never auto-achieve merely because one cycle succeeded.

A finite goal is achieved only when its current required criteria have valid accepted evidence and no invalidating revision. Paused/cancelled/expired goals cannot admit new effects. `force` may make a schedule due; it cannot bypass authority, budgets, review, revocation or terminal states.

## 3. Execution packets and dependency order

The JSON manifest is the dispatch graph. One integration owner controls migrations, composition, shared contracts and dev merges. Parallel workers are optional, only after their interfaces and file ownership are agreed; never let several workers independently redesign ProductStore or the authority schema. Keep PRs reviewable and rerun relevant tests after integration.

### PC-00 — Freeze, inventory and assign ownership

Inputs: current dev, this review, existing plans and open PRs. Record source SHA, dirty worktrees, active owners, current schema heads and supported modes. Reproduce the six review probes using generated data. Map every required behavior to its actual runtime caller; identify dormant helpers and duplicated authority. Preserve original evidence, then turn observations into negative regression tests.

Produce a concise architecture decision mapping current functions to the one operational path, an explicit schema reuse/migration map, packet ownership/dependencies, and a tracker reconciliation queue. Do not arbitrarily close older PRs; classify them as integrated, independent, superseded or historical with evidence. Deliver a baseline receipt and reviewed interface changes before parallel implementation.

### PC-01 — Contain false success and repair authorization boundaries

Files: `api/store.py`, `api/routes_v1.py`, `pursuit/loop.py`, `workers/{continuous_connector,identity,capability_authority}.py`, `workspace/grants.py`, affected tests.

Remove implicit successful RecordingExecutor composition. Until dispatch is implemented, return `blocked_missing_implementation` with no achievement or fake mission. Require positive protected verification for criterion progress; reject failed/self-asserted success. Fix capabilities to require every required capability; required scopes also require explicit authorization. Preserve false/unproven qualification and reject/quarantine unsupported operational enrollment. Separate capability availability from permission and evidence.

Resolve inputs through workspace/artifact grants at dispatch and immediately before execution; realpath containment alone is insufficient if an attacker can swap symlinks between check and open. Use the existing safe file-access boundary or descriptor-based traversal where applicable; forbid arbitrary host paths by default. Revoke grants mid-flight in a regression test. No new entitlement comes from a personality, message or model response.

Done: each reproduced behavior has a regression test that fails on baseline and passes after fix; ordinary legitimate extraction still works in a generated authorized workspace. Keep precise errors without leaking paths/secrets across projects.

### PC-02 — Durable operational repositories and migrations

Files: `db/*`, `migrations/*`, `goals/models.py`, `pursuit/*`, `api/durable_authority.py`, `mission/store.py`, artifact metadata and event stores used by the product.

Persist goal revisions, criterion verdicts, cycles, schedules, dedupe keys, mission links, reservations, worker membership/generations, leases, result submissions, messages/cursors, context handoffs and lesson adoption needed for this vertical slice. Reuse existing tables where correct. Centralize writes behind repository transactions. Use optimistic version checks and unique constraints for idempotency; same key with different payload conflicts. Store token verifiers/hashes, not reusable plaintext bearer secrets in public snapshots.

Admission transaction commits cycle + reservation + mission/task records + outbox intent. Result transaction validates current fences, binds immutable artifact metadata and schedules verification. Verification transaction advances criteria and emits events. No external side effect occurs inside a long database transaction. Preserve pending/unknown effects for reconciliation after crash; do not assume exactly-once external delivery.

Provide a dry-run-first legacy JSON importer with schema/digest validation, backup/export, per-record receipts and idempotent restart. Reject incompatible or corrupt records without silently resetting history. Persist artifacts separately and verify their digests when restoring. Fresh migration and upgrade from the reviewed baseline must both work.

Done: fresh PostgreSQL instance and fresh API process can reopen real work; concurrent identical submissions create one record; failed transactions cannot orphan an admitted budget or lose an outbox event. Operational startup with unavailable DB is unready and cannot fall back to simulated writable state.

### PC-03 — Real mission dispatch and native execution

Files: `pursuit/loop.py`, `mission/{runtime,planner,worker,protected_verify}.py`, `controller/*`, `workers/{registry,connector,continuous_connector}.py`, `runtime/adapters/native.py`, broker and tool gateway composition.

Implement an asynchronous mission-executor adapter over the authoritative mission service; it returns pending/submitted identity and reconciles eventual results. Do not block an API request or coordinator loop on a whole mission. Convert proposed work into schema-validated task graphs; kernel validates scope, dependencies, budgets and graph limits. Worker advertises only configured qualified runtimes.

Native agent loop supports observe/context → model response → validated tool/help/delegation proposal → kernel admission → actual tool/model result → continuation/finish. Models propose actions; kernel executes permitted actions and records their effects. Implement real bounded local read/write/test capabilities required for the campaign. No extract-specific output can masquerade as arbitrary coding/planning work. All inference flows through the approved Swarm broker; reuse external inference-server interface if configured without redesigning that separate project.

Configure deterministic fake HTTP inference at the boundary for tests. Exercise malformed model output, tool-call schema errors, provider timeout, context limit, refusal and partial response; cap retries and record actual requests. Do not silently change provider/model/runtime after a denial. Normal no-route/no-runtime states must be visible and recoverable after authorized configuration.

Done: a user-created mission reaches the shipped connector, consumes generated provider responses, actually changes a generated workspace, uploads content-addressed output and passes an independent check. No harness constructs the expected output behind the runtime's back.

### PC-04 — Persistent bounded pursuit service

Files: `pursuit/{loop,schedule,frontier,policy,stagnation,models}.py`, API lifecycle, coordinator service/CLI entrypoint, deploy role wiring.

Replace constant clock and transient progress dictionaries with PC-02 repositories. Implement a long-running coordinator service integrated with the server/combined role; worker-only processes do not schedule goals. Acquire singleton authority and cycle fences, recover unfinished phases at startup, and reconcile results through events/outbox. A lost coordinator lease prevents new admission.

Observe current criteria/evidence, form a frontier, select a useful contribution, admit one bounded mission, wait/reconcile, verify and persist progress before the next cycle. Distinguish task retries from new approaches; title changes cannot evade dedupe. A valid repair path gets a new attempt while retaining causal linkage. `ask`, `request_human`, `wait` and `stop` are real durable states. Resource depletion includes held reservations. Never let failure keep an active-mission slot forever.

Done: two sequential missions run without manually pressing tick; restart between them preserves progress and dedupe; ongoing goals retain ongoing state; idle/blocked goals do not spin. Concurrent scheduler startup dispatches one mission. Wall-clock tests use virtual time rather than sleeps.

### PC-05 — Worker lifecycle, cancellation and isolation

Files: worker service/client/envelopes, API auth/routes/schemas, workspace grants, lease fencing, connector subprocess supervision.

Expose authenticated enroll/inspect/drain/revoke/rotate/reconnect controls through API and CLI. Enrollment secrets are one-time scoped credentials; membership is distinct from installation admin authority. Revoke by stable ID and generation; persist across restart. Re-enrollment cannot silently erase revocation or reset grants. Unqualified capabilities are visible but unschedulable.

Keep heartbeat/lease renewal/cancellation processing alive during slow execution. Current synchronous executor call must not prevent timely cancellation. Use a bounded supervised process/task appropriate to the runtime. On expiry or revoke, stop new tool/model admissions; terminate cancellable child processes within a documented bound (default ten seconds), mark uncertain external effects unknown, and reject stale results. Cancellation is not proved merely by refusing the final submit.

Workspace sandbox must deny parent traversal, symlink escape, cross-project artifact access and unnecessary host mounts. Do not give untrusted tasks a Docker socket or broad provider credentials. If isolated test-command execution needs container management, keep that interface in the trusted supervisor with a fixed allowlist and grant checks.

Done: worker death, network disconnect, duplicate result, mid-tool cancellation, post-restart revocation and forged scope all produce correct durable outcomes with no unauthorized new effects.

### PC-06 — Protected acceptance and evidence accounting

Files: mission verification/acceptance, artifact repository, pursuit verification, acceptance harness, evidence schemas.

Define criterion verifier registry: deterministic artifact schema/content checks, protected repository tests and explicitly authorized human decisions. A model critique can propose review findings but cannot manufacture a verifier receipt. Verifier runs separately from worker-controlled output and cannot accept a forged stdout marker. Freeze protected verifier/check definitions and bind receipts to their digests and candidate artifact digest. Reject stale, missing, tampered, foreign-project or wrong-revision evidence.

Update goal criteria only after acceptance of the exact current candidate. Failed execution never contributes successful criteria. Partial evidence can advance only the independently passed criteria. Mission completion and goal achievement remain distinct. Existing achieved records derived from simulation must be flagged synthetic/unverified during migration, not silently converted to real achievements; preserve their history.

Record requested/actual model, route, runtime, call count, token usage, cost source, reservations and uncertainty. Unknown usage/cost stays unknown. Settle child reservations exactly once under duplicate delivery. Cancellation/crash must reconcile holds without fabricating refunds.

Done: counterfeit success, forged evidence refs, changed artifacts, failed outcome with claimed criteria and duplicate accounting are all rejected through the actual API/service path.

### PC-07 — Agents, communication, memory and X/Y succession in the runtime

Files: canonical contracts, `mission/collab.py`, `memory/*`, `knowledge/*`, runtime session/checkpoint, existing handoff/fencing implementations, message APIs.

Preserve human-defined seed agents, personality, role guidance, allowed interactions, runtime and model choices. Agents may ask peers for help, offer evidence, teach lessons and propose delegation within policy. Temporary crews are goal-scoped memberships/coordination views, not an independent authority competing with the collective goal. A request for help can target any permitted peer; competence and response confidence remain explicit, and help is not accepted fact without evidence.

Persist messages, delivery cursors and causal references. Bound inbox/context size and deduplicate retries. Communication does not bypass project/data-locality boundaries or move secrets into shared memory. Delegation must be mediated through kernel task admission with child budget/depth/session limits.

Implement working context, reference/cue index and durable source memory using current repository abstractions. Cues contain compact summaries/references plus confidence; resolve the source when needed and check current access/revision. Retain indispensable current task instructions, constraints and immediate facts in context; a reference-only context is not sufficient. Enforce token budgets before calls, including system/tool schemas, output reserve and provider-specific context limits.

X/Y defaults: trainee starts at 65% of usable input budget; takeover begins at 80%; configurable with `0 < X < Y < 1`. Reserve at least 15% of usable input budget for KT/transition; recompute at model switch. Use provider token counts/tokenizer when available, conservative estimates otherwise and expose uncertainty. KT1 includes objective, decisions/evidence, grants, commitments, current task and memory refs. Trainee shadows read-only and cannot issue effects. KT2 contains deltas and the final event/inbox watermark. Atomically fence predecessor session and transfer ownership only after successor validates packet integrity and acknowledges continuity. Preserve logical agent ID; change session/generation. Context succession is distinct from delegated parallel subwork.

If occupancy crosses Y abruptly, pause new effects and attempt bounded handoff using durable state and reserved headroom. If handoff cannot be verified, block visibly; never reset context silently or allow both sessions to write. Crash at each handoff phase must be recoverable.

Done: a multi-agent mission exchanges real messages; trainee receives two transfers; successor resumes a pending commitment after restart; predecessor result/tool request is rejected. Unauthorized source-memory retrieval and oversized tool output are denied/truncated with provenance.

### PC-08 — Evidence-backed lessons and model evaluation

Files: `pursuit/learning.py`, `learning/*`, eval harness/route evidence, memory retrieval, configuration surfaces.

Learning in V2 means durable, scoped, testable lessons and improved choices. It does not mean modifying model weights. Failed and successful work can propose a lesson with source refs, conditions, confidence and intended effect. Separate proposed/evaluated/adopted/rejected/reverted states. Run bounded evaluation against a frozen task set before adoption; persist the policy/version and let operators inspect/revert. Teaching sends lesson references; recipients independently decide applicability under kernel policy. No lesson can expand authority.

Build a versioned dummy-task corpus in three tiers: simple extraction/schema conversion, medium repository fixes/planning with dependencies, hard multi-step repair/recovery under ambiguity. Minimum three distinct tasks per tier. Include hidden/protected checks, withheld evaluation cases, input fixtures and failure taxonomy. Measure verified quality, latency, calls/tokens, observed cost, invalid outputs and recovery behavior. Separate synthetic transport tests from actual model capability results. A fake provider cannot qualify a model. Record exact model/provider/runtime/config and sample counts; do not claim universal rankings from a small sample.

Done: a supported lesson is adopted only in its scope, an unsound lesson fails evaluation, rollback restores prior behavior, and a machine-readable benchmark can run offline or with a future valid LiveGrant without changing the product path.

### PC-09 — SDK, CLI and UI parity

Files: `api/*`, `sdk/*`, `cli.py`, `apps/console/src/{api,components,App.tsx}`.

Expose goals/criteria, policy envelopes, seed agents, runtime availability, worker enrollment/revocation, active missions, artifacts/evidence, messages, context succession, lessons, resource usage and precise blockers through the same API. Implement start/pause/resume/cancel with idempotency and optimistic concurrency. Remove any UI route that silently toggles a production action into a demo.

User journey: connect authenticated installation → configure project/workspace/route → create goal and agent → preview constraints/criteria → start → observe actual progress → inspect artifacts and verification → pause/restart/reopen → resume → inspect final result. Show why a goal is waiting and the specific permitted action that unblocks it. Runtime choices show supported capabilities and unavailable reasons; no false Hermes/OpenCode readiness.

Console subscribes or polls with durable event cursors, reconnects without duplicating events, handles expired auth and renders stale/offline state explicitly. Keep credentials out of URLs/local logs and use the existing authenticated session approach. Package UI assets or a dedicated console service in the supported deployment with documented API routing.

Done: browser E2E uses the real API and deterministic provider, no mocked product endpoints; SDK and UI reopen the same IDs/status/evidence. Static build/unit tests alone do not complete this packet.

### PC-10 — Fresh install, packaging and operational recovery

Files: Dockerfile, deploy/compose server/worker/combined profiles, env templates, entrypoint, install docs, support matrix.

Ship a complete compose baseline with private PostgreSQL, authenticated API, coordinator, UI, and outbound worker. Same code/image may serve role-specific entrypoints. Initialize named-volume ownership safely for non-root operation, including fresh worker workspace volumes; do not recursively chown arbitrary host paths. Keep credentials in runtime secrets/config and avoid broad repository mounts. Require explicit secrets or generated bootstrap credentials instead of shipping production defaults.

Separate liveness from readiness: DB/schema, migrations, artifact store, authority acquisition and configuration readiness must be visible. Lack of worker/provider can be a useful waiting state, not necessarily a dead server. Provide a documented initialization flow, upgrade procedure, backup/restore, worker rotation and rollback constraints. Migration and artifact versions must be compatible; fail clearly on incompatible restore.

Qualify the exact Linux architecture actually tested, record image digest/host runtime, and leave other cells experimental. Docker on Mac may exercise a Linux container cell on its actual architecture; it does not prove physical cross-host or the Mac native adapter. Test randomized install paths, hostname and host ports. DNS/Cloudflare and personal hardware are optional overlays, never generic acceptance prerequisites.

Done: new empty volumes and no existing checkout state yield a usable UI and worker, a goal completes offline through the real stack, stack recreation retains state, and backup restores to another isolated installation with validated artifact hashes.

### PC-11 — Real integrated acceptance and fault campaign

Replace the misleading "protocol twin" claim with explicit connectivity-smoke labels. Add an independent acceptance driver that talks only to shipped APIs/SDK/browser and manipulates container lifecycle as an operator. It may generate input fixtures and provider responses but must not create success artifacts, edit product database rows or directly call control-plane accept helpers to make the campaign pass.

Required scenarios are in section 4. Use unique compose project names, random ports, isolated volumes and `try/finally` cleanup. Never shut down another user's Swarm stack. Read back persisted results after fresh processes; a returned command or healthy container is not completion. Capture bounded redacted logs and retain failures. Run required scenarios in CI with ephemeral PostgreSQL/containers; an omitted Docker job cannot count as a passing product gate.

Done: exact merged candidate passes all offline product scenarios and independent review reproduces the dangerous cases; reports bind source/image/config/verifier/input digests and execution provenance. Promotion flags remain separate from engineering completion.

### PC-12 — Live qualification preparation and optional authorized execution

Implement the real LiveGrant dispatcher and qualification runner, including preflight for route/model/provider, resource/time/data scope, expiry, source/config binding and supported runtime. A valid grant plus missing implementation is an implementation defect. An invalid/missing grant is an authorization blocker. Fake-provider tests cover both and prove dispatch would take the normal path.

Produce one concrete grant request listing proposed benchmark/mission, exact route/model, maximum calls/tokens/spend/duration, data leaving host, artifact/evidence location and stop conditions. Reuse a previously granted permission only if its scope/expiry/binding actually matches; do not assume old grants cover changed source or route. No paid fallback, account creation, external inference, public DNS or deployment is authorized by this planning packet.

If an applicable grant exists, execute exactly its permitted cases and retain real receipts. Otherwise finish runner/tests/docs and mark only this live substep blocked. Continue PC-13 and all independent work.

### PC-13 — Integrate, independently review and hand off

One owner integrates dependency order into dev under existing authorization and repository protections; never main. Each PR records packet IDs, source/verification SHA, tests, cost, risks and artifact paths. Check actual remote tips and status after merge; clean stale stacked PR references only with evidence and ownership. Independent reviewer must inspect the integrated candidate and rerun critical negative cases. Do not call an author rereading their own output an independent review.

Update STATE, EXECUTION_MAP, packet queue, manifests, install docs, support matrix, changelog and Linear reconciliation using truthful statuses. Separate implementation, offline product verification, platform qualification, live qualification, independent review and operator acceptance. Set V1.7–V2.0 accepted only when their documented gates are actually satisfied; never infer acceptance from elapsed effort/test count.

Return concise summary: exact dev SHA/PRs, what a user can now do, evidence bundle, tests and skips, unresolved defects, pending live/deployment/operator gates and the single best next action. Push committed code/tests/docs/evidence before stopping, preserving others' uncommitted work.

## 4. Required acceptance scenarios

Each scenario needs expected state, observed state, exact candidate SHA/image, environment, request/correlation IDs, artifact hashes and pass/fail/blocked reason. These are actual product-path tests, except explicitly labelled unit/fault injection cases.

| ID | Scenario | Required observable result |
|---|---|---|
| A01 | Fresh generic install with empty volumes | Authenticated UI/API/worker ready; no personal config or fixture success |
| A02 | Simple generated extraction mission | Worker performs task; immutable artifact passes protected schema/content check |
| A03 | Multi-step repository repair | Native runtime plans/edits generated repo, fails a protected test once, repairs within limit and passes |
| A04 | Two-mission finite goal | First mission gives partial progress; second is autonomously scheduled; goal achieves only after both receipts |
| A05 | Persistent ongoing goal | Due/event wake works; one successful cycle does not terminate ongoing goal |
| A06 | API/coordinator/worker restarts at phase boundaries | Goal/cycle/lease/history/commitments survive; no duplicate admitted effect |
| A07 | Worker revoke/cancel during long execution | New admissions stop promptly; process termination bounded; stale submit rejected after restart |
| A08 | Authorization and confinement negatives | Missing capability/scope, unqualified host, path/symlink escape and cross-project retrieval denied |
| A09 | Forged/failed/stale results | Failed claims and forged stdout/receipts cannot advance criteria or achievement |
| A10 | Two workers race / duplicate submit / coordinator race | One authoritative lease/cycle/result; accounting settles once |
| A11 | Budget and grant boundaries | No unreserved child calls; revoked/expired grants stop; no paid fallback; unknown spend stays unknown |
| A12 | Peer help, delegation and memory retrieval | Real scoped exchange and source provenance; no authority expansion; bounded child work |
| A13 | KT1/KT2 and fenced succession | Logical identity retained; continuity verified; predecessor cannot act; crash recovery works |
| A14 | Lesson evaluate/adopt/revert | Unsupported lesson rejected; scoped valid lesson adopted with evidence; revert durable |
| A15 | UI/SDK parity and reconnect | Same goal/mission/artifact identities; pause/resume/cancel and event history truthful after reload |
| A16 | Export/backup and restore into fresh stack | Goal, active-state reconciliation, grants and artifacts retained; secrets handled separately |
| A17 | Bad provider/tool output and unknown side effect | Bounded retries, precise blocker/failure, no fabricated success or unsafe repeat |
| A18 | Model benchmark matrix | Nine frozen tasks across three tiers, measured results by route/runtime; synthetic vs live separated |
| A19 | Live/native model mission | Only with applicable LiveGrant; real route/tool/artifact/verifier evidence, otherwise explicitly blocked |

Crash points include: before/after admission commit, after outbox publish before acknowledgement, after worker claim, after external dispatch before response, after artifact upload before result commit, after verification before progress update, and during both handoff phases. For non-idempotent external effects with unknown outcome, reconciliation or human decision is required; do not assert impossible exactly-once execution.

## 5. Tracking, execution discipline and stopping conditions

Track PC-00 through PC-13 as one product program. Packet statuses: planned → owned → implementing → review_ready → integrated → verified; blocked requires specific reason, affected substep and independent work remaining. Every handoff includes owner, branch, base/head SHA, changed interfaces/files, tests/evidence, unresolved risks and next action. Use the current shared packet queue as canonical once packets are imported; do not keep competing status ledgers.

Resolve the existing Linear project/team before writing. Map packet IDs to real issue IDs; update dependencies, acceptance, branch/PR and evidence references, then read back. Never invent keys or duplicate the project. If Cursor's auth is unavailable or destination is unresolved, commit exact intended changes to LINEAR_RECONCILIATION with reason and continue implementation. Linear is a tracking integration, not the authority for execution or product readiness.

A docs-only packet, protocol scaffold, mock HTTP success, in-process acceptance helper, test count or unsubmitted prompt does not establish product completion. Conversely missing R730/Cloudflare/Linear/live authorization does not justify stopping unaffected engineering. Inspect source and current tests before declaring a task already complete; include the caller chain and retained proof.

Only pause dependent work for a genuine missing decision/access/authorization that cannot be resolved within this plan. Finish all independent packets, publish a precise checkpoint, and consolidate remaining requests. Do not expand this task to V3/V4 to avoid closing V2 gaps. End with a useful, testable product and honest remaining acceptance gates.
