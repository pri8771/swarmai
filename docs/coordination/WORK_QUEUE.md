# SwarmAI lead work queue — approved through V1.4

> **Artifact-oriented execution view:** `ARTIFACT_REGISTRY.json` is canonical. This queue exists only to show the next work that advances blocked/drafting/reviewable artifacts. Every packet must reference an artifact ID. Story points size worker effort; artifacts define project completion.


Updated 2026-09-20 by CURSOR-20260920-022 (ACK LEAD-013/014; W-121A/W-131A packaged). Owner authorization remains V1.0 repair -> V1.4 inclusive. Evidence/independent review gate acceptance; main merge/release/public exposure/additional spend remain unauthorized. Stop feature work at V1.4.

Remote main: `b9141fa3150f853586dede0334a47b344571bc16`. Draft PR #14 tip: `19b91ba89bfac5d670af0d766f21f4b9f2ca1a62` (feature `d9da26c7a8b47d1ffeabf866250cdbf30d14ffce`). Actions `35543599747` + `35543622029` green. LEAD-012 verified FIX-002/003/005 source repairs; G10 blocked only on FIX-004 authenticated hourly worker receipts. Cursor CLI still Not logged in. G11 LEAD-012 evidence rerun posted (browser create + hidden acceptance + operational controls/restart) — **not** lead-accepted. G12 dual-remote plan only; G13 criterion preregistered; G14/LIVE-142 unclaimed.

## Worker packet / story-point execution

Use `WORKER_STORY_POINT_PROTOCOL.md`, `WORKER_PACKET_BACKLOG.md` and `WORKER_PERFORMANCE.json`.

Worker bias: SP1–SP3 execution goes to Cursor. Split SP4–SP5 whenever practical. Lead handles architecture, hard debugging, acceptance, external research and review. Keep >=3 ready worker packets when practical.

Packaged while FIX-004 auth waits (CURSOR-022):
- W-111A/B: evidenced under CURSOR-021 (not lead-accepted).
- W-121A (SP2): eligibility ledger posted — **0 admissible remotes**; W-121B blocked.
- W-131A (SP1): gap map posted; W-131B not started.

FIX-004 W-041A remains external-blocked on live CLI login. Optional local $0: third-model L/XL n=5 screening gaps only. When auth succeeds, immediately perform W-041B/W-041C.

## Execution discipline

Use `cursor/v1.4-live-integration-11e2` plus bounded worktrees. One owner integrates shared API/store/schema/lockfile changes. Preserve unrelated work. Status progression remains queued -> assigned -> in_progress -> implemented -> tests_verified -> live_verified where required -> lead_reviewed. Passing CI is necessary, not sufficient. Unknown/blocked is better than fake success. Current operational runtime may not silently use fixtures, supplied answers, fake readiness or admission bypasses.

## G10 / V1.0 repair

### FIX-001 — comprehensive CI and honest baseline

Status: `tests_verified_current_tip`.

Lead verified current CI scope. Preserve it after every source change. Do not weaken checks. `tests/integration` remains an explicit non-pass until run in an environment with a valid DSN; prior local PostgreSQL results are worker-reported only.

### FIX-002 — authentication, project boundaries, scoped ownership

Status: `source_repaired_lead_verified` at current code tree.

Lead re-reviewed the operational app/routes/store. Install bootstrap uses install-local project identity rather than hard-coded demo memberships; fixed demo principals are fixture-only. Worker/approval views/actions are project-scoped, worker heartbeat and approval resolution bind to durable ownership, and inspected operational idempotency paths authorize before scoped cache/action access.

Keep negative two-project regressions. Do not regress these changes while implementing G11+.

### FIX-003 — evidence-backed release/readiness

Status: `source_repaired_lead_verified` at current code tree.

Release evidence now requires exact candidate SHA, command inventory, successful exit/result, compatible mode, freshness timestamp and evidence-kind-specific configuration/model/tool identity. Negative tests cover missing/wrong SHA, stale timestamps, failed exit, wrong mode and missing/empty identity. Do not relax these gates for later acceptance artifacts.

### FIX-004 — platform sessions and actual hourly worker

Status: `scheduler_verified_authenticated_worker_blocked`. **This is the remaining G10 contractual blocker.**

`cursor agent status` and `cursor agent whoami` still report **Not logged in**. Probe-only scheduler check-ins are useful scheduler evidence but do not count as authenticated unattended worker execution. Keep `SWARM_HOURLY_SKIP_CURSOR_PROBE` until authentication is truly verified.

After a fresh successful `cursor agent login` with the live CLI waiter, verify both status commands. Then capture:

1. one bounded authenticated manual worker invocation; and
2. two genuine hourly scheduler-triggered authenticated worker invocations with no overlap/lease violation.

Do not accelerate the hourly evidence, prewrite receipts or use billed cloud automation. Once those receipts exist, request G10 lead acceptance. No other G10 source feature work is currently assigned unless regression evidence appears.

### FIX-005 — remove operational demo/mock dependence

Status: `source_repaired_lead_verified` at current code tree.

Lead re-reviewed ProductStore/API/capacity/console. Operational mode defaults real/empty/unknown; mock broker and seeded catalog are fixture-only; the demo side-effect route is fixture-gated; live console defaults to empty/API data and never merges/recover-falls-back to mock; fixture Expand/Contract controls are explicit mock-only; parser dogfood is opt-in. Preserve these boundaries.

## G11 / V1.1 — RUN-111 unified generic mission

Status: `evidence_advanced_current_tip_revalidation_required_not_accepted`.

Useful evidence exists: three unfamiliar real-local Ollama missions across extract+triage completed at $0, with API/CLI reading the same durable IDs; parser dogfood is not the normal path; automatic primary-worktree promotion has been removed.

Do **not** call G11 accepted yet. Current residual acceptance work:

1. Run an **actual local operator-console browser journey**, not merely a request matching the console API shape. Create at least one unfamiliar mission through the UI and observe it in the UI; verify the exact same mission ID/status through API and CLI.
2. Re-run the required three unfamiliar tasks across two families on the exact current/future candidate with task-defined acceptance criteria. Where feasible, use deterministic/hidden graders so plausible-but-wrong nonempty output cannot pass; worker prompts must not contain grader answers.
3. Re-run unsupported-task, deliberately wrong-output rejection and cancellation on the current operational candidate. Old artifacts are not sufficient final proof if they lack current SHA/config binding.
4. Re-run actual service restart/reopen in **operational** mode. The inspected older restart artifact says `execution_mode: mock`; it is stale for final G11 acceptance after the real-data repairs.
5. Bind every G11 acceptance artifact to code/tree SHA, config/model/tool versions, commands, timestamps, mode and actual result under FIX-003 standards.
6. Re-run exact-tip CI after source changes. Evidence-only updates must state the unchanged code SHA explicitly.

This work may continue while FIX-004 waits because it is ready independent work inside the authorized V1.4 tranche. Acceptance remains ordered: G10 must pass before G11 promotion.

## G12 / V1.2 — INF-121 concurrent governed inference

Status: `in_progress_local_only_not_accepted`.

Lead verified the latest local admission/reconcile artifact as preparation: three brokered local calls across two Ollama routes settle correctly; the next call is honestly denied when the request bucket reaches zero. Artifact explicitly says remote dual proof is not claimed.

Next:

- Refresh exact-route authentication/current zero-charge eligibility/health evidence for candidate remote providers without generating paid traffic.
- Prepare one bounded mission/test plan that produces **overlapping actual calls through at least two independently authorized remote providers**, plus an actually available local route/fallback, with admission/reservation/reconciliation evidence.
- Do not run a remote route whose charge eligibility or authorization is stale/unknown. If an account session requires human authentication, prepare only that exact step.

G12 remains unaccepted until real dual-remote overlap exists; serial fallback, two local models or simulation do not satisfy it.

## G13 / V1.3 — EVAL-131 empirical qualification

Status: `provisional_screening_not_qualified`.

Latest worker screening covers roughly **60 provisional cells** across S/M/L/XL, six families and three local model configurations at small sample counts. Preserve it as screening only; do not promote provisional rates into qualified profiles.

Before any additional evaluation volume:

1. preregister task-family/size scoring and the qualification/uncertainty rule;
2. preregister call/token/wall-time stop conditions under current zero-charge policy;
3. include planning, coordination, retries, recombination and review overhead in comparisons;
4. version datasets, prompts/tools/models and keep held-out graders unavailable to workers;
5. identify which cells actually need more samples to satisfy the criterion rather than blindly expanding all cells.

No G13 acceptance yet.

## G14 / V1.4 — SWARM-141 adaptive organization

Status: `offline_prep_not_accepted`.

Latest offline artifact proves graph admission behavior: expand -> deny at `max_graph_nodes` -> retire/contract -> expand again. It explicitly sets `live_claimed=false` / `live_multi_planner_claimed=false`, so it is useful preparation only.

Do not substitute this for the live gate. Required acceptance still needs multiple real planning/review configurations contributing, evidence-driven expansion, convergence-driven contraction/merge/cancel, useful overlapping work and measured admission/resource behavior. Wait for qualified G12/G13 capacity before the live multi-planner proof.

## LIVE-142 — final V1.4 acceptance

Status: `campaign_preregistered_not_started`. `LIVE_142_CAMPAIGN_PROTOCOL.md` now freezes the campaign shape: 12 positive mission slots covering supported families/sizes, six negative scenarios, designated G14 adaptive XL mission, restart/reopen and a real 24-hour protected observation window. Exact held-out task payloads are selected only after candidate freeze so hidden answers are not exposed to workers. Runtime/security/routing changes restart affected campaign evidence.

## Future lead artifacts already advancing

These are real durable artifacts, not merely backlog notes:
- ART-V15-ARCH — distributed worker architecture: control/worker/artifact planes, durable leases, fencing, failure recovery.
- ART-V16-KNOWLEDGE-CONTRACT — provenance classes, permission-before-retrieval, contradiction/supersession/deletion and context-budget requirements.
- ART-V17-TOOL-CONTRACT — unified consequential-action envelope, payload-bound approvals and browser-session recovery contract.
- ART-V18-RECOVERY-ARCH — site authority/epoch, durable-state classes, restore/reconciliation and split-brain prevention.
- ART-V19-BETA-ACCEPTANCE — clean external installs, extension interface freeze and independently reviewed self-development PR proof.

Lead should continue deriving the next durable artifacts from these whenever current review/research capacity is available. Cursor should receive follow-on implementation packets only when they are safe/non-conflicting with the active candidate.

## Immediate next action for Cursor

CURSOR-022 ACKed LEAD-013/014 and packaged W-121A + W-131A (W-111A/B already evidenced under CURSOR-021). While W-041A waits on human login: do **not** invent remote eligibility or EVAL qualification; optional local $0 only for missing third-model L/XL n=5 screening identified by the gap map. Once CLI auth verifies, switch to W-041B then W-041C to close G10. W-121B stays blocked until two fresh zero-charge remotes verify. Do not self-accept gates or start V1.5+ implementation. No merge/spend/launch.