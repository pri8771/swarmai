# Execute SwarmAI through V1.4 — owner-approved tranche

Authorization recorded: 2026-09-20. Source: the operator approved the V1-to-V3 direction and said, "For now, lets just get to V1.4" and "the goal is, V1.4 with no issues or errors live."

This is an execution mandate, not evidence that implementation or live verification has occurred. Last source observed by the lead: main `b9141fa3150f853586dede0334a47b344571bc16`. Re-fetch current source and coordination refs before work.

## 1. Authority, scope and stopping point

The approved IMPLEMENTATION range is V1.0 repair -> V1.1 -> V1.2 -> V1.3 -> V1.4 inclusive. Cursor should continue through these checkpoints without repeatedly asking the operator whether to start the next 0.1. This supersedes earlier repair-only or per-increment implementation stop instructions in old handoffs/messages. It does NOT retroactively accept any checkpoint or remove engineering review.

ChatGPT directs priorities and independently reviews evidence. Cursor implements, tests and operates the authorized local browser/development environment. Work may continue on dependency-ready branches while a review is pending, but a checkpoint is not accepted until its required evidence and independent lead review exist. Preserve a review-pending state rather than inventing a lead reply.

Creating task/integration branches, making local commits, normal pushes to this private repository and draft PRs are authorized. Source integration between these working branches is allowed after checks. Merging into main, release tags/publishing, public exposure, production deployment, purchases, payment methods, billing activation, paid fallback, destructive changes and unrelated account actions are NOT newly authorized. The final V1.4 candidate is submitted for operator merge/release approval. V1.5-V3 remain approved roadmap direction only, not current implementation scope.

Live means actual configured application state, real inference and real tools in a protected local or already-authorized private environment. It does not mean opening a public endpoint or provisioning a cloud server. Cloud-first deployment/local site recovery remains V1.8; retain architectural compatibility without claiming it is completed at V1.4.

## 2. Definition of done — no known unresolved V1.4 defects

The target is zero known unresolved defects in the agreed V1.4 supported workflows, zero unexpected application errors in the final acceptance runs, and all mandatory acceptance/security gates passed. No finite test can establish that software has no possible future bugs. Do not promise that, suppress errors, remove failing cases or silently narrow support after a failure.

A rate limit, denied action, invalid input, unavailable provider or unsupported task must produce its specified truthful outcome. A handled negative scenario is not a bug; fabricated success or an unhandled exception is. Provider/model limitations remain visible. Do not count unavailable prerequisites as passes.

No operational demo data: no seeded identities/projects/activity, fake connected accounts, canned responses, known-answer patches, fabricated capacity, mocked product endpoints or automatic fixture fallback. Empty installation = empty state; no eligible route = blocked/waiting; failed model output = failure or bounded real repair. Keep useful isolated regression tests/fault injection, but never present their output as live inference evidence. Move test-only dependencies out of shipped runtime paths. Preserve historical demo evidence with accurate labels, never rewrite it as a successful live run.

## 3. Start and repository discipline

Read AGENTS.md, this contract, PROJECT_MEMORY.md, STATE.json, WORK_QUEUE.md, unread AGENT_MESSAGES.md entries and the relevant audit. Keep the initial context compact. The stable transport branch is `coordination/swarm-control`; its application snapshot is not the current development baseline.

Inspect actual main/PR/CI/worktrees. Preserve uncommitted work. Use a dedicated integration branch such as `cursor/v1.4-live-integration` and bounded packet worktrees, reusing existing matching work rather than duplicating it. One owner integrates shared contracts, migrations, lockfiles and overlapping API/runtime edits. Never force-push the coordination branch or reset a dirty checkout.

Record an ACK of LEAD-20260920-003 with actual source SHA, owned files, first test and current runner status. Reproduce current failures rather than blindly applying the old audit to changed code. Keep the pinned audit immutable; maintain a finding-resolution matrix with new fix/test evidence.

## 4. Execution gates

### G10: V1.0 repair — FIX-001 through FIX-005

Repair CI/test discovery, production auth bootstrap, project isolation, scoped idempotency, evidence verification, provider-readiness assertions and normal-mode demo dependencies. Remove GOOD_FIX/known-answer substitution and any force-progress admission bypass. Authenticate and authorize BEFORE cache/history/artifact access. Fail safely when auth or real storage is not configured.

Required proof: failing-then-passing security regressions; independent lint/type/backend/frontend jobs covering applicable suites; actual production-mode startup and empty state; no static demo credentials; missing/stale/failed evidence cannot pass release verification. All original capability gaps remain explicit until subsequent gates close them. Source review and test counts alone do not close behavioral findings.

Login/session documentation and the hourly worker runner proceed in parallel. Their precise external prerequisites must not hold up safe code work; final required items cannot be marked complete while blocked.

### G11: V1.1 — one generic real mission system

Wire console, API, CLI, task graph, executor and persistence into ONE mission path. Use task-provided goals, allowed inputs/tools, output contracts and acceptance criteria. Reuse sound existing runtime/broker/store libraries; do not create a second executor to satisfy a demonstration.

Required proof: at least three unfamiliar tasks across two families, selected before the run with no supplied solution available to workers. Create through console, observe through API/CLI, execute and inspect the same durable mission ID/artifacts. Restart the actual service and reopen that mission. Demonstrate cancellation, wrong-result rejection and unsupported-task outcomes. Review/checks must control acceptance, not append decorative notes after a predetermined success. No automatic copying of accepted edits into an unrelated primary worktree.

### G12: V1.2 — concurrent inference pool

Route EVERY model call through one governed call boundary: planners, workers, reviewers, evaluation, embedding/memory calls and retries. Preserve exact account alias/provider/model/configuration identity. Separate catalog/config/auth/inference eligibility/current health/price/quota/task qualification. Metadata endpoints that also work unauthenticated do not prove credential authentication.

Implement atomic reservations for shared account/project/org buckets, request/token/concurrency limits, reset windows, unknown usage, cooldowns and final reconciliation. Disable nested retries or meter each actual attempt. Reserve capacity for planning/review and avoid retry storms. Fail closed on uncertain charge eligibility; respect actual platform terms and user-owned accounts.

Required proof: one real mission with overlapping requests through at least TWO independently authorized remote providers, plus an actually available local model path. A serial fallback trace is insufficient. Show timestamps, request IDs where available and outcome/usage records without credentials. Kill/disable one route during a controlled private test and actually execute the permitted alternative, or wait honestly. Admission races must not double-allocate capacity. Unknown local availability must not become always-true readiness. Preserve privacy boundaries when selecting an alternative.

### G13: V1.3 — empirically qualified task/size routing

Use at least three actual model configurations, four useful task families and S/M/L/XL complexity descriptors. Size includes rules, entities, dependencies, tool steps and output obligations, not only token length. Standard task INPUTS and isolated test fixtures are valid; model RESPONSES and scores must come from actual calls. Prefer public/licensed or operator-approved non-sensitive material for live evaluation.

Create a coverage matrix. Every model/family/size cell must have measured evidence or a specific evidenced incompatibility; do not label an unrun cell qualified. Use calibration and held-out tasks with locked input/reference versions; workers must not read grader answers. Begin with at least five held-out independent observations per supported cell as screening, then obtain enough samples for the preregistered acceptance/uncertainty criterion. Five successes alone are not broad qualification. Keep underpowered cells provisional. Support can be limited to the cells that actually qualify, but do not silently waive the required four-family/four-size product coverage. Every required family/size needs at least one qualified route; all models need not be good at all sizes.

Before live runs, register task scoring, quality threshold, confidence method/sample rule, token/call budget and stop conditions. A reasonable default is a 0.80 minimum quality rate using a one-sided 90% lower confidence bound, plus deterministic checks and zero forbidden tool actions; record stricter requirements for riskier tasks. Do not change thresholds after looking at failures without a new reviewed evaluation version. Report sample counts and all unsuccessful attempts.

Required proof: the broker selects routes from matching observed family/size profiles, distinguishes strong planners from qualified smaller workers, and performs bounded repair/subdivision/escalation when necessary. Include total planning, coordination, retries, recombination and review costs/tokens/time versus direct execution. Demonstrate a provisional/unqualified route being rejected for a task that needs qualification. Provide cold-start evaluation mode with explicit limits rather than bypassing policy to create the first profile.

### G14: V1.4 — elastic swarm, not a fixed team

Implement versioned, validated graph changes for spawn/split/merge/reassign/cancel/review and competing approaches. Agents propose work; software enforces dependencies, permissions, available capacity and loop/delegation limits. Permit more than one capable planner/reviewer and multiple task-qualified workers using different routes concurrently. Graph changes must not orphan results, bypass resource admission or rerun already accepted effects.

Required live proof: at least one mission where two planning/review model configurations contribute, new evidence causes additional specialists/tasks to be created, and subsequent convergence causes agents/tasks to retire or combine. Record reasons and graph revisions, not a pre-scripted agent count animation. Independent useful work actually overlaps. Report logical agents, active sessions, in-flight model requests and worker processes separately.

Exercise scheduling at 10, 50 and 100 logical assignments in isolated load tests; these are not fixed product ceilings or proof of 100 reasoning agents. Measure real model concurrency separately at levels permitted by current resources. Do not falsify larger capacity or exhaust accounts to achieve a number. Under the same task sets, compare elastic execution with a single-agent and a fixed-team baseline; report quality, latency, total inference/coordination overhead and cases where a swarm does not help.

## 5. Accounts, sessions, credentials and live budgets

Reuse the existing provider accounts/keys; do not repeat signup because a fresh process lacks configuration. Use supported browser-first setup for missing access. Preserve the local normal Priyansh/Default Chrome rule and Google SSO restrictions. Never extract cookies or bypass CAPTCHA. Prepare the exact verification/consent/password/passkey step for the operator, resume the intended destination afterward, and continue independent work when one provider is blocked.

Store platform account ALIASES, login method/profile reference, safe entry/destination patterns, secret reference and actual last-check time in PLATFORM_ACCESS.md. Real identity mappings, passwords, keys, cookies, session state and sensitive URLs stay in an appropriate private local store. A previous signed-in status is historical, not a current session guarantee. Reopening Apply is not submitting an application.

The operator authorizes bounded real inference/acceptance tests for this tranche, within existing zero-additional-spend accounts and resources. Never add cards, use paid routes or enable top-ups. Before each live batch persist its exact allowlisted routes, current free eligibility evidence, call/token/wall-time envelope and stop conditions. Bound every call/retry with pre-admission. First discover inherited resource policies; use the stricter existing bound. Where none exists, start conservatively with at most 100 remote attempts and 200,000 counted input+output tokens per rolling 24h across this qualification/acceptance runner, and 20 attempts/32,000 tokens per individual mission; preserve capacity for review. These are starting VALIDATION envelopes, not hard-coded product scalability limits. The lead may redistribute only within verified available free quotas and the recorded tranche policy; larger envelopes require an explicit documented decision, not an unbounded run.

Exhausted allowance means pause/resume after a verified reset or use a qualified local route, not change acceptance thresholds or activate billing. Local calls also have concurrency, token and time limits. Unknown usage stays unknown and retains a conservative reservation until reconciled. Model rejection, outage and authentication failures must never be synthesized away. Do not send private repository/customer data to a provider without existing scope authorization; use self-contained non-sensitive live tasks otherwise.

## 6. Final V1.4 live acceptance

Lock the supported behaviors, representative task set and expected negative outcomes before testing. Use a clean worktree/install and a real persistent store, operational console/API/CLI and qualified routes; no demo runtime settings. Final evidence must bind to the candidate code/tree SHA, dependency/config versions, task/dataset hash, exact command, timestamps, mode, route identity, actual result, token/usage accounting and artifact locations.

Minimum final campaign:

- All relevant lint, typing, backend, frontend/browser, migration/install and security tests pass. Missing required tests are blocked, not skipped-green. Keep routine CI offline-safe while live gates run in the authorized environment.
- At least 12 previously registered positive missions covering coding, evidence extraction/research and task planning/tool use complete through the operational path after final fixes. Choose within the declared supported task envelope; include all runs and failures, not only a favorable subset. Final campaign success must not rely on references, silent fallbacks or human-prepared answers.
- At least six negative/failure scenarios pass: wrong project, denied tool, stale/invalid credential, exhausted quota, cancellation/deadline and invalid model result. A controlled process restart reopens actual persisted work. Real multi-provider overlap, real local fallback and graph expansion/contraction evidence are mandatory.
- Observe 24 wall-clock hours of the protected live application on an available authorized host after core fixes, exercising recurring bounded real missions and both normal/negative workflows. Record host availability, observation gaps, request errors and reconciliation. No time acceleration, fabricated heartbeat or future-dated evidence. Light monitoring need not call a model every minute. This is a V1.4 validation window, not a development-time promise or the V1.8 cloud rollout.
- Zero known unresolved in-scope defects or unexpected application errors. Every observed error is triaged; real bugs are fixed and affected checks rerun. Relevant fixes invalidate stale evidence. Expected policy denials/provider limitations are recorded rather than hidden. No unapproved charges, leaked secrets or duplicate consequential actions.
- Independent lead review examines the final diff, findings matrix and live artifacts. All G10-G14 rows must be passed with current evidence before calling V1.4 live-accepted. If remote capacity, host availability or operator verification prevents a gate, report implemented/live-blocked and the precise next action; do not claim completion.

Retain every attempt with provenance. Evidence may be stored privately with sanitized references in Git; hashes alone are not proof of execution. Pure documentation edits can reference an unchanged code-tree hash, but code/config changes require relevant revalidation. Never change a test label or expected output just to clear a failed run.

## 7. Collaboration and progress

Read compact memory/state plus unread messages. Append immutable LEAD/CURSOR message IDs using fresh blob SHAs or a dedicated fast-forward coordination worktree. Record Done / Evidence / Next / Blockers / source and ACKs. Do not manufacture the other agent's acceptance.

Keep the existing hourly lead automation. Install and verify only one supported no-extra-spend Cursor runner with a lease/no-overlap lock, resumable bounded invocations and truthful host status. A heartbeat file is not a live agent. Never report a future invocation as observed. While awaiting a review or real quota reset, continue ready independent work within V1.4; do not start V1.5.

Maintain a gate matrix for G10-G14, the pinned audit resolution matrix, packet/source SHAs, live evidence index and compact next action. Use suitable existing files rather than building another management system. Agent session interruption is not a reason to lose progress or restart architecture planning.

## 8. Delivery

Deliver a private V1.4 candidate branch/draft PR, exact source SHA, runnable start commands and the actually reachable private/local console address, real account/route readiness without secrets, test and live-evidence reports, full known-issue matrix and remaining operator actions. Do not invent a URL when the service is not running. Explicitly distinguish implemented / independently reviewed / live-accepted / merged / publicly released.

Stop feature development at V1.4. Continue repairing its defects and collecting required evidence, but leave V1.5+ unstarted. Final main merge/publication remains the operator's decision. This plan changes authorization and acceptance criteria only; no application repair or live success is claimed by its creation.
