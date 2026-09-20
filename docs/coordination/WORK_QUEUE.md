# SwarmAI lead work queue — approved through V1.4

Updated 2026-09-20 by LEAD-20260920-012 after CURSOR-20260920-020. Owner authorization remains V1.0 repair -> V1.4 inclusive. Evidence/independent review gate acceptance; main merge/release/public exposure/additional spend remain unauthorized. Stop feature work at V1.4.

Remote main: `b9141fa3150f853586dede0334a47b344571bc16`. Draft PR #14 current head: `c1ebf20abb10c53c0209dcc15bfa5bf89efba510`, one docs-only commit over lead-reviewed application code `6669d37827d487206ee6c71734d4e2c64b475906`. Exact-tip Actions `35543156880` is green. The reviewed application-tree run `35543013930` showed console install/lint/Vitest/build success, Ruff success, mypy 139 files, install/package success, Alembic head, and **267 passed, 2 skipped** broad non-live tests. DB integration remains honestly skipped in GitHub CI without `SWARM_DATABASE_URL`; the live-gated job is a blocked notice only.

## Lead-owned acceptance artifacts

Cursor no longer needs to define its own acceptance targets. Use:
- `V1_4_LEAD_ACCEPTANCE_PLAN.md` for exact G10-G14 exit criteria;
- `EVAL_131_QUALIFICATION_PROTOCOL.md` for frozen G13 statistical rules;
- `LIVE_142_CAMPAIGN_PROTOCOL.md` for the final 12-positive / six-negative / 24-hour campaign.

These narrow ambiguity but do not override `V1_4_EXECUTION_CONTRACT.md`.

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

## Immediate next action for Cursor

Follow LEAD-20260920-013. Finish FIX-004 authenticated Cursor heartbeat first. After G10 acceptance, rerun the exact G11 current-candidate multi-surface evidence, then close G12 remote overlap. For G13, use the frozen qualification protocol; do not invent thresholds or blanket-run every weak cell. G14 must use qualified roles/routes and produce a genuine live expansion/contraction mission. LIVE-142 starts only after integrated G10-G14 candidate freeze. No merge/spend/launch.