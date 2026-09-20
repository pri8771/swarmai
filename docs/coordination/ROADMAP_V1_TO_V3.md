# SwarmAI: V1.0 repair -> V2.0 -> V3.0

**Date:** 2026-09-20. This is the lead's proposed product roadmap, not evidence of completed work or blanket authorization to merge every version. The operator promotes each 0.1 checkpoint. Detailed packets and independently runnable workstreams are derived from each approved checkpoint's contracts.

## Product outcome

SwarmAI is an elastic problem-solving runtime. A mission may have several capable planners, many independently qualified smaller-model workers, reviewers and deterministic tools, using approved providers concurrently. Agents can request specialists, split work and challenge findings; software enforces authority, budgets, dependencies and resource admission. The operator's copy targets no additional spending, free-cloud coordination where feasible, local resources and tested local recovery. Other deployments may explicitly authorize different budgets.

Do not define progress by role names, task counts, version labels or how many Markdown packets were checked. Define it by accepted outcomes with evidence. Reuse existing broker/contracts/tooling where sound. No mandatory CrewAI or rebuild of established queue/database/provider libraries.

## Universal checkpoint gate

Every checkpoint has an immutable source SHA, reviewed diff, reproducible commands and actual outputs, applicable CI/backend/frontend/security tests, a failure-path demonstration, cost/resource report and updated short handoff. Simulation, local inference, remote inference and deployment remain separate evidence categories. A missing live prerequisite means that part is blocked, not passed. Every feature needs an observable user-facing outcome.

Workflow: Cursor implements in bounded branches -> records evidence -> lead reviews and assigns repair if needed -> operator authorizes merge/promotion -> next checkpoint. Independent tasks inside an authorized checkpoint can run in parallel with shared contracts and clear file ownership. Do not batch-promote versions by writing release docs.

## V1.0 — Repair and establish an honest baseline

**Goal:** replace the current `1.0.0rc1` completion claim with a trustworthy, safe development baseline.

Fix the audit's failed/incomplete CI, default demo-token exposure, cross-project history/report/idempotency defects and misleading readiness/proof labels. Keep known-answer demos separate from model acceptance. Create compact coordination state, documented platform access and a functioning hourly lead/worker handoff. Preserve useful code and historical evidence.

**Exit gate:** lint and type checks actually run; every applicable offline/backend/frontend suite runs on the same candidate; unauthorized cross-project requests and demo credentials fail; structural checks cannot label unexecuted behavior as verified. Every remaining unmet original requirement is openly listed. This is a repaired local baseline, not permission to market it as the completed swarm.

**User sees:** one accurate status report, reliable login instructions and exact remaining capability gaps.

## V1.1 — One real, generic mission path

**Goal:** the CLI, API and console operate the same actual mission runtime.

Replace demo-specific file/answer assumptions with a task contract covering goal, approved inputs/tools, artifacts and acceptance. Wire submission, execution, progress, cancellation, approval and results through one authoritative store/executor. Separate fixture initialization from operational mode. Integrate any already-working generic agent components instead of creating a second runtime.

**Exit gate:** create a mission in the console, inspect it through API/CLI, execute it and obtain the same durable result everywhere. Demonstrate at least three previously unseen tasks across two task families, plus a wrong-output rejection and an unsupported-task outcome. No hidden `GOOD_FIX` or reference-answer fallback. A restart reopens the same mission identity and accepted state.

**User sees:** entering a new problem does useful work, rather than always repairing the demo parser.

## V1.2 — Concurrent inference pool and hard admission

**Goal:** all qualified approved sources can contribute concurrently to one mission.

Use exact account/model routes and a single broker for every model call, including planning, review, evaluation, embeddings and memory processing. Make auth, inference eligibility, pricing, quota and qualification independent. Add atomic reservations, shared quota groups, retry reconciliation, unknown-usage handling, reset windows, cooldowns and reserved capacity for planning/final verification. Eliminate test-only quota bypasses from executable production paths.

**Exit gate:** one mission has overlapping calls on at least two authorized independent remote provider accounts and uses a qualified local route when appropriate; proof records actual request times and identity. Exhaust one pool and continue elsewhere or wait, never purchase capacity. Race-test multiple workers sharing one allowance and prove no double allocation. A fake key, stale cost evidence or unverified free route cannot become ready. Offline multi-provider simulation is required but does not replace the live gate; unavailable free live routes remain explicitly blocked.

**User sees:** real available capacity and an explanation of why each task uses its route.

## V1.3 — Empirical model qualification by task and size

**Goal:** use smaller models where evidence supports them, not by reputation or parameter count.

Create versioned task families and S/M/L/XL complexity descriptors. Maintain calibration and held-out sets; use deterministic graders where possible and calibrated independent judgments when necessary. Record exact model version/settings, prompt/tool version, sample count, quality, latency, failures, retries, tokens and confidence. Add scoped promotion/demotion and regression/drift checks. Count supervisor, repair and verification overhead in every comparison.

**Exit gate:** qualified profiles exist for at least four useful task families across four sizes, using at least three actual model configurations. Declare sample sizes/uncertainty; inadequate evidence stays provisional. Router chooses from matching family/size evidence and demonstrates escalation/subdivision after failure. A smaller-model workflow is compared fairly with direct execution and includes total overhead. No claim of broad qualification from one tiny canary.

**User sees:** which model is good at which work, at what size, and where evidence is weak.

## V1.4 — Elastic swarm organization

**Goal:** the swarm grows, contracts and reorganizes around the problem.

Allow bounded graph-change proposals: spawn specialists, split work, create competing approaches, merge duplicates, reject assumptions, cancel obsolete branches and route reviews. Permit multiple strong planning/review models. Keep graph revisions/dependencies consistent, preserve independent investigation where useful, and stop runaway delegation. Distinguish logical agents, active sessions, in-flight calls and machines.

**Exit gate:** a representative mission starts small, expands when new independent work is discovered, contracts when work converges, and documents why. Demonstrate 10, 50 and 100 logical agents in the scheduler harness without treating those as fixed product limits. Separately measure real LLM concurrency under actual available quota. Compare completed-task quality/time/resource use against a single-agent and fixed-team baseline; report conditions where a swarm does not help. All admission failures block execution.

**User sees:** an evolving task graph with evidence-based allocation, not a fixed four-step chain or hash-only benchmark.

## V1.5 — Durable distributed workers

**Goal:** execution moves across authorized machines without losing progress or repeating effects.

Finish the chosen durable runtime integration (reuse DBOS/PostgreSQL or the justified existing backend rather than inventing another queue). Add worker capabilities, leases, heartbeats, timeouts, cancellation, fencing, atomic result acceptance and durable resource reservations. New nodes register and old nodes drain safely. Keep an explicit trust boundary around code/browser execution.

**Exit gate:** at least two independent worker processes on separate hosts execute eligible tasks; adding/removing a worker changes capacity. Kill a real worker mid-task, recover the same mission, finish remaining work and prove accepted side effects are not blindly repeated. Test stale lease rejection, duplicate deliveries and two simultaneous missions sharing provider quotas. A seeded JSON state transition alone does not pass.

**User sees:** a useful local machine can join the swarm; its disappearance does not silently lose work.

## V1.6 — Scoped reusable knowledge and compact context

**Goal:** use prior results without resending entire conversations or leaking projects.

Separate current task state, source artifacts, hypotheses, accepted facts and reusable procedures. Add permissions-before-retrieval, provenance, expiry, contradiction handling, correction/deletion, incremental summaries and context budgets. Use structured/text retrieval first; use vector retrieval where measured benefit justifies it. Reuse the existing store/interfaces, avoiding multiple conflicting memory authorities.

**Exit gate:** a second mission reuses verified results with measurable context savings without losing required evidence. Cross-project retrieval, summaries, caches, exports and traces do not leak forbidden content. Deleting or superseding a record affects future retrieval. Large irrelevant history does not force a full reload. Agent messages remain short and point to evidence instead of recording private reasoning/transcripts.

**User sees:** the swarm remembers useful work and shows why it believes a fact.

## V1.7 — Reliable tools, browser sessions and approvals

**Goal:** agents can perform useful actions and recover from authentication interruptions.

Expose approved APIs, filesystem/workspace tools, sandboxed execution and selected MCP/browser capabilities through one permission boundary. Bind consequential approvals to exact action/payload/destination and revalidate on change. Finish the platform-access registry, authentication checks, profile mapping, safe resume destinations and stale-link handling. Preserve existing browser/Google SSO restrictions. Use native APIs where possible; no unofficial subscription-to-API conversion.

**Exit gate:** demonstrate three real supported tool integrations. In a controlled expired-session test, opening an Apply/dashboard link prompts only for the essential human auth step, then returns to the correct destination without duplicate submission. Validate wrong-account/wrong-project denial, redirect-loop termination, denied side effects, restricted network/filesystem access and complete redaction. Documentation of credentials is not session restoration. The documentation part is implemented immediately at V1.0; this checkpoint completes runtime behavior.

**User sees:** a brief login handoff rather than being told to redo an entire account setup.

## V1.8 — Cloud-first operation with local recovery

**Goal:** the operator's installation runs without the development Mac being the controller.

Package a repeatable cloud deployment with protected access, health monitoring, state/artifact backups and optional local workers/models. Reassess current free-host eligibility/availability before selecting a host. Make resource/overage limits explicit; no silent billing. Separate provider fallback, worker failover and whole-site recovery; use fencing and consistent backups for takeover.

**Exit gate:** run a sustained 72-hour trial on an actually available approved host, with posted resource/cost evidence. Normal eligible missions continue while the home worker is off. Exercise provider and worker outages. Restore the control services/database/artifacts locally and finish the same recoverable work; document measured recovery time and possible data-loss window. If free capacity is unavailable, report that rather than call a paid deployment free. Cloud-to-local fallback requires an available local host and usable state.

**User sees:** Swarm runs in the cloud, uses local capacity when available, and has a tested recovery route.

## V1.9 — Independent beta and controlled self-development

**Goal:** prove portability and useful outcomes outside the original developer environment.

Freeze supported SDK/extension contracts, package one small set of general capability examples, verify install/upgrade/backup, finish license/security/dependency review and exercise the complete UI. Add bounded self-development: isolate branch/workspace, implement a selected issue, run independent tests/review, and prepare a PR. Never let an agent approve its own security policy, credentials or production deployment.

**Exit gate:** at least two clean external installations; no embedded personal identity/default credentials; end-to-end product/browser tests; held-out mission set evaluated against a declared baseline. At least one non-demo repository change is independently accepted as a PR candidate. Audit remaining failures honestly. Two successive hourly runner invocations acknowledge messages and make/record bounded progress without overlap. Publish only with separate operator authorization.

**User sees:** another technical user can install Swarm and accomplish a useful mission without your private setup.

## V2.0 — Accepted elastic problem-solving product

**Goal:** a dependable self-hostable product, not merely a version bump.

Integrate and independently review the preceding gates. Resolve release-blocking defects, freeze public interfaces and migration notes, publish accurate support/limits, and provide reproducible evidence. Run a seven-day operational acceptance window on the intended deployment (proposed gate, not an estimate of development time).

**Exit gate:** real heterogeneous concurrent missions; task-size-aware routing; dynamic graph changes; multi-host restart recovery; scoped memory; secure browser/tool handoffs; cost admission; repeatable installation and a clean independent review. Complete coding, research/synthesis and tool/automation missions through the same product path. Performance claims distinguish simulation from actual models and hosts. Operator explicitly approves stable release/tag/launch.

**User sees:** submit a problem and constraints, connect permitted resources, observe useful work scale up/down, review evidence and approve only consequential actions. No guarantee of unlimited free inference, permanent free hosting or optimal answers to every problem.

## What V2.0 should look like

A technical user installs SwarmAI, connects approved model routes and optional nodes, and submits a goal through the console/API. The swarm chooses a task structure and qualified models, runs independent work concurrently, requests specialists as new questions arise, checks results, and stops when success or an honest limit is reached. A provider outage or node loss does not destroy the mission. The result contains useful artifacts, evidence, resource accounting and unresolved questions.

Core product: mission runtime, resource broker, graph coordination, shared context/evidence, worker/tool interfaces, permissions and operator console. Optional integrations: model providers, local runtimes, coding/browser engines and business services. Personal businesses remain separate configurations or applications. Ordinary scripts are first-class; AI is not forced into every step.

## V3.0 direction — persistent, learning multi-mission operations

V3.0 extends the proven V2 runtime into ongoing objectives spanning multiple missions and projects. This is a direction to refine after real V2 usage, not a pre-approved giant feature list.

1. **Persistent objectives:** schedules/events propose bounded missions; the platform plans priorities and dependencies over time, with explicit authority and stop conditions.
2. **Portfolio resource allocation:** fair scheduling and configurable priorities across projects, provider quotas, local/cloud workers and deadlines; support the operator's zero-spend policy and others' explicit budgets.
3. **Governed operational learning:** improve prompts, procedures, model routing and decomposition from measured outcomes. Changes are versioned, tested on held-out work and rolled back after regression. No automatic trust in self-generated memory.
4. **Controlled self-development:** Swarm can fix selected bugs, improve adapters and prepare tested PRs through its own runtime; independent review and operator authority remain outside the agent's self-approval loop.
5. **Reusable capability ecosystem:** signed/versioned packs or adapters with declared permissions, schemas, tests and compatibility—not an unreviewed arbitrary-code marketplace.
6. **Fleet/team operations:** stronger identity, tenancy, policy, quotas, audit, portability and larger heterogeneous fleets where users actually need them.

Example: an authorized ongoing 'maintain this application' goal observes a failing test, opens an investigation, plans a fix, evaluates alternative implementations using different resources, creates evidence and submits a reviewed change. It learns which procedures worked without quietly deploying to production or spending money.

**V2.0 completes individual missions reliably. V3.0 manages continuing objectives through many reliable missions and improves its operating procedures under review.** Do not hide an unfinished V2 core inside a V3 promise.
