# SwarmAI lead work queue — approved through V1.4

Updated 2026-09-20. The owner approved V1.0 repair -> V1.4 implementation inclusive. `V1_4_EXECUTION_CONTRACT.md` is authoritative for this tranche. No repeated operator implementation approval is required at each 0.1; evidence/independent review remain mandatory. Final main merge/release/public exposure is not authorized. Stop feature work at V1.4; V1.5-V3 remain roadmap direction.

Remote main remains `b9141fa3150f853586dede0334a47b344571bc16`. Draft PR #14 latest tip is `643e38bf3f08e998936aad21bff3cb9a10541f4e`; the newest commit adds G13 holdout evidence only and does not close G10. Current GitHub Actions run `35536776956` is red: console lint/test/build passed, Ruff passed, then mypy failed at `src/swarm/mission/runtime.py:46`; install/Alembic/offline pytest did not run on this exact tip. Lead review LEAD-20260920-007 also found remaining G10 defects in non-mission idempotency/auth ordering, bootstrap demo principals, evidence-file validation, provider readiness and the parser-specific normal mission runtime. Earlier green SHAs remain evidence only for those SHAs.

## Execution and ownership

Use/reuse the dedicated integration branch `cursor/v1.4-live-integration-11e2`, with scoped task branches/worktrees. Claim a packet in AGENT_MESSAGES and STATE with base SHA and owned files. One integration owner controls shared schema, API/store conflicts, lockfiles and migration ordering. No simultaneous writers in the same worktree. Preserve unrelated work; no force-push.

Status: queued -> assigned -> in_progress -> implemented -> tests_verified -> live_verified (where required) -> lead_reviewed. Acceptance is separate from merge/release. Continue ready independent implementation while a live prerequisite or review is pending; never fabricate that missing evidence. No known-answer or operational mock path is accepted. A fail/unknown/blocked state is preferable to fake success.

## G10 / V1.0 repair

### FIX-001 — comprehensive CI and honest baseline

Status: `implemented_current_tip_ci_failed`; PR #14 tip `4021c2de32b040e0760e3f771820380e2581aa4e`; current CI `35536709246` fails mypy after Ruff, while console CI passes. P0. Audit AUD-01/11.

Required now: fix the broker typing regression and obtain a full green current-tip offline pipeline (Ruff, mypy, install, Alembic, broad offline pytest) plus console lint/test/build. Preserve DB/live blocks honestly.

Accept: exact current candidate SHA, complete backend/frontend inventory, commands/results and current remote CI evidence. Earlier green SHAs do not certify a newer red tip.

### FIX-002 — auth, project isolation, idempotency

Status: `partial_changes_required`; mission isolation improved, but LEAD-20260920-007 found remaining bare-key idempotency and auth-after-cache paths on provider/evaluation/worker mutations at `4021c2de32b040e0760e3f771820380e2581aa4e`. P0 security. Audit AUD-03/04/10.

Remove seeded installed-runtime identities; implement per-install auth and safe unconfigured startup. Authorize before cache/data/history access. Scope idempotency by actor/project/operation plus request digest and reject body mismatches. Validate ownership on reports, artifacts, history, approvals and workers. Coordinate API/store edits with FIX-005 and RUN-111.

Accept: negative regressions fail before the fix and pass afterward, including known demo bearer tokens in operational/non-loopback mode, two principals/projects, history-backed records, key reuse and request-body mismatches. No secret leakage. Keep application private/loopback until this is reviewed.

### FIX-003 — evidence-backed release/readiness

Status: `partial_changes_required`; hard-coded yes is removed, but release verification still treats evidence-file presence as a behavioral pass and provider readiness still violates fail-closed requirements. P0 integrity. Audit AUD-02/08/09.

Remove hard-coded verification/readiness flags. File existence is packaging evidence, not a test result. Key presence/public catalog access is not authenticated or zero-charge eligibility. Add exact-route observation provenance/expiry. Separate actual timeout/cancellation/recovery behavior from helper state transitions. Lock behavioral acceptance contracts before tests.

Accept: missing/stale/failed evidence prevents the corresponding pass. Broken runtime behavior fails acceptance even with all documents present. No guessed cost eligibility, success or task suitability.

### FIX-004 — platform sessions and real hourly worker

Status: `partial_scheduler_verified_worker_auth_blocked`; repeated scheduled check-ins are evidenced, but the scheduler currently skips the Cursor probe and `cursor agent status` remains Not logged in, so unattended worker spawning is not verified. P1. Audit AUD-11. LaunchAgent installed; recurring_verified=true; **cursor agent status still Not logged in** after operator claim (loginDeepControl pending); unattended spawn not resumed.

Follow PLATFORM_ACCESS.md and CURSOR_HOURLY_PROMPT.md. Maintain per-platform aliases, login method/profile, private credential refs and actual session-check times. Preserve existing Google SSO restrictions. Restore the original protected destination after the essential human login step. The reported Apply URL itself is unavailable here; do not invent a reproduction. An authorized controlled expired-session test is distinct from reproducing that exact incident.

Configure one permitted local/eligible runner with lock, bounded invocations, resumable state and sanitized evidence. No cloud-agent billing. Show an actual invocation and then two actual scheduler-triggered check-ins before marking recurring operation verified. Future observations stay pending. Missing profile/auth/entitlement affects that task, not all code work.

### FIX-005 — remove operational demo dependence

Status: `partial_changes_required`; GOOD_FIX substitution and scale force-progress bypass are repaired, but normal `swarm mission run` still enters the parser-specific RepoWorker dogfood path. P0 product truth. Audit AUD-05/06/07/10.

Inventory default/runtime fixture imports, synthetic users/providers/activity, GOOD_FIX, canned responses and force-progress quota bypasses. Remove them from the shipped operational path. Failed output must fail or use bounded real repair/escalation. No assumption that every task is the demo parser. Integrate useful existing modules; keep missing generic capability explicitly incomplete until RUN-111. Preserve isolated tests but do not count them as live proof.

Accept: clean operational install has real empty state, no fake fallback on API failure, no supplied-answer patch and no execution after denied admission. Store/console/API show actual observations. Unimplemented features are blocked, not renamed complete.

## G11 / V1.1 — RUN-111: unified generic mission

Status: `in_progress_not_accepted` on `cursor/v1.4-live-integration-11e2`; durable identity/restart/review-control evidence exists, but G10 remains open and the normal operational mission command is not yet unified onto this generic path. Owner: Cursor.

One durable mission identity across console/API/CLI; generic goals, permitted inputs/tools, graph, execution, cancellation/review and artifacts. No secondary demo executor. Reuse existing agent and persistence libraries after verifying compatibility.

Accept: three unfamiliar tasks across two families; same mission submitted/viewed across interfaces; actual service restart/reopen; wrong output rejected; unsupported task honest; no known-answer path. See G11 contract for details.

## G12 / V1.2 — INF-121: exact-route admission and concurrent pool

Status: `in_progress_local_only_not_accepted` — local concurrent broker/fallback evidence exists; required dual remote overlap remains blocked and provider readiness must be repaired first. Owner: Cursor/inference.

Every model call/retry goes through the broker. Exact route/account identity, independently evidenced auth/eligibility/health/capabilities, atomic shared-quota reservations, deadlines/reset/cooldown and accounting. No always-true local route or unmetered hidden model calls. Reuse configured accounts; browser hand off only essential human steps.

Accept: actual overlapping calls to two independent remote providers in one mission, plus actual local inference/fallback; safe unavailable/quota behavior; failed/stale evidence denied; no double allocation. Live capacity missing = gate blocked, not simulated pass.

## G13 / V1.3 — EVAL-131: task/size evidence and selection

Status: `provisional_underpowered_not_accepted` — local screening exists but required family/size coverage and uncertainty/sample criteria are not met. Owner: Cursor/evaluation.

Three actual model configurations; four task families and four sizes. Measured coverage matrix, calibration/held-out separation, predeclared quality/uncertainty and resource rules, exact prompt/tool/model versions, all outcomes and overhead. Invalid/unsupported cells remain explicit; qualify routes only where evidence supports them. Every required family/size needs at least one qualified route, not every model qualifying at every size.

Accept: routing uses observed matching profiles and handles failure via bounded repair/subdivision/escalation; compare smaller-worker pipelines with direct execution including overhead. The contract's screening minimum is not automatic qualification. No forged model results or leaked reference answers.

## G14 / V1.4 — SWARM-141: adaptive graph and organization

Status: `offline_prep_not_accepted` — graph/10-50-100/elastic-vs-fixed artifacts are offline preparation only; live multi-planner adaptive proof is absent. Owner: orchestration lane.

Validated graph revisions for spawn/split/merge/reassign/cancel/review and multiple planning approaches; independent investigations, evidence exchange, duplicate suppression and bounded delegation. Separate logical agents, active sessions, requests and processes. Preserve permission/resource checks on every expansion.

Accept: real mission expands on discovered work and contracts on convergence; two capable planning/review configurations contribute; smaller qualified workers actually run concurrently. Separately exercise 10/50/100 logical assignments and measure permitted real inference concurrency. Compare elastic/single/fixed approaches fairly; no hash-only proof or fixed permanent team ceiling.

## G14 final — LIVE-142: clean installation and live acceptance

Status: queued; requires integrated G10-G14 behavior and current evidence. Owner: independent QA lane with lead review.

Run the final campaign in V1_4_EXECUTION_CONTRACT.md: all applicable checks, 12 preregistered positive missions across supported work, at least six specified failure scenarios, real provider overlap/fallback, real graph adaptation, actual restart and an observed 24-hour private/live operating window. Keep all attempts and triage every error. Revalidate relevant changes; do not fabricate time or cherry-pick only successes.

Accept: no known unresolved supported-V1.4 defects; no unexpected application errors in the accepted campaign; no unapproved spend/secret leakage/duplicate side effects; current independent review. Missing live prerequisite = implemented/live-blocked with precise action. Deliver candidate SHA/draft PR, actual startup commands/address, evidence index and known-issue matrix. Final main merge/release stays with operator.

## Immediate next action

Follow LEAD-20260920-007. First restore a green **current-tip** PR by fixing the mypy regression and rerunning the complete offline + console CI. Then close G10 source gaps before acceptance: scope every operational idempotency call after authorization; remove fixed known principals from normal bootstrap; validate behavioral evidence by exact SHA/config/commands/results/freshness rather than file existence; make provider auth/price/health/qualification fail closed; and make the parser-specific dogfood runtime fixture-only or replace the normal `swarm mission run` path with RUN-111's generic durable execution. Post exact pushed SHA, CI run/jobs and fail-before/pass-after regressions. Later G12–G14 work may remain on the branch but cannot substitute for closing G10.