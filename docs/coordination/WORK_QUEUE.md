# SwarmAI lead work queue — approved through V1.4

Updated 2026-09-20. The owner approved V1.0 repair -> V1.4 implementation inclusive. `V1_4_EXECUTION_CONTRACT.md` is authoritative for this tranche. No repeated operator implementation approval is required at each 0.1; evidence/independent review remain mandatory. Final main merge/release/public exposure is not authorized. Stop feature work at V1.4; V1.5-V3 remain roadmap direction.

Last observed main: `b9141fa3150f853586dede0334a47b344571bc16`. Fetch current source before reproducing findings. The control branch carries coordination, not the source baseline. No Cursor ACK or completed repair was verified when this queue was updated. All new packet statuses below are assigned/queued, NOT completed.

## Execution and ownership

Use/reuse a dedicated integration branch such as `cursor/v1.4-live-integration`, with scoped task branches/worktrees. Claim a packet in AGENT_MESSAGES and STATE with base SHA and owned files. One integration owner controls shared schema, API/store conflicts, lockfiles and migration ordering. No simultaneous writers in the same worktree. Preserve unrelated work; no force-push.

Status: queued -> assigned -> in_progress -> implemented -> tests_verified -> live_verified (where required) -> lead_reviewed. Acceptance is separate from merge/release. Continue ready independent implementation while a live prerequisite or review is pending; never fabricate that missing evidence. No known-answer or operational mock path is accepted. A fail/unknown/blocked state is preferable to fake success.

## G10 / V1.0 repair

### FIX-001 — comprehensive CI and honest baseline

Status: in_progress; ACK CURSOR-20260920-001; baseline ruff 33 reproduced on b9141fa / cursor/v1.4-live-integration-11e2. P0. Audit AUD-01/11.

Reproduce Ruff failure and repair causes. Execute actual lint, typing, backend, frontend/browser and migration/install checks appropriate to the code. CI must discover all applicable suites, not just contracts/spikes. Isolate live-gated jobs and give precise skipped/blocked reasons; do not imply they passed. Use permitted resources, avoiding unverified extra CI charges. Correct current status/handoffs without rewriting the immutable historical audit.

Accept: exact candidate SHA, test inventory, commands, exit results and actual remote CI evidence. No blanket ignores, disabled security checks or deleted failing tests to obtain green status.

### FIX-002 — auth, project isolation, idempotency

Status: assigned_acknowledged (CURSOR-20260920-001); work starting. P0 security. Audit AUD-03/04/10.

Remove seeded installed-runtime identities; implement per-install auth and safe unconfigured startup. Authorize before cache/data/history access. Scope idempotency by actor/project/operation plus request digest and reject body mismatches. Validate ownership on reports, artifacts, history, approvals and workers. Coordinate API/store edits with FIX-005 and RUN-111.

Accept: negative regressions fail before the fix and pass afterward, including two principals/projects, history-backed records, key reuse and non-loopback requests with known demo credentials. No secret leakage. Keep application private/loopback until this is reviewed.

### FIX-003 — evidence-backed release/readiness

Status: assigned_acknowledged (CURSOR-20260920-001); work starting. P0 integrity. Audit AUD-02/08/09.

Remove hard-coded verification/readiness flags. File existence is packaging evidence, not a test result. Key presence/public catalog access is not authenticated or zero-charge eligibility. Add exact-route observation provenance/expiry. Separate actual timeout/cancellation/recovery behavior from helper state transitions. Lock behavioral acceptance contracts before tests.

Accept: missing/stale/failed evidence prevents the corresponding pass. Broken runtime behavior fails acceptance even with all documents present. No guessed cost eligibility, success or task suitability.

### FIX-004 — platform sessions and real hourly worker

Status: assigned; authorized local environment required. P1 parallel lane. Audit AUD-11.

Follow PLATFORM_ACCESS.md and CURSOR_HOURLY_PROMPT.md. Maintain per-platform aliases, login method/profile, private credential refs and actual session-check times. Preserve existing Google SSO restrictions. Restore the original protected destination after the essential human login step. The reported Apply URL itself is unavailable here; do not invent a reproduction. An authorized controlled expired-session test is distinct from reproducing that exact incident.

Configure one permitted local/eligible runner with lock, bounded invocations, resumable state and sanitized evidence. No cloud-agent billing. Show an actual invocation and then two actual scheduler-triggered check-ins before marking recurring operation verified. Future observations stay pending. Missing profile/auth/entitlement affects that task, not all code work.

### FIX-005 — remove operational demo dependence

Status: assigned_acknowledged (CURSOR-20260920-001); work starting. P0 product truth. Audit AUD-05/06/07/10.

Inventory default/runtime fixture imports, synthetic users/providers/activity, GOOD_FIX, canned responses and force-progress quota bypasses. Remove them from the shipped operational path. Failed output must fail or use bounded real repair/escalation. No assumption that every task is the demo parser. Integrate useful existing modules; keep missing generic capability explicitly incomplete until RUN-111. Preserve isolated tests but do not count them as live proof.

Accept: clean operational install has real empty state, no fake fallback on API failure, no supplied-answer patch and no execution after denied admission. Store/console/API show actual observations. Unimplemented features are blocked, not renamed complete.

## G11 / V1.1 — RUN-111: unified generic mission

Status: queued; implementation contracts can begin alongside independent G10 repairs, integrated acceptance depends on G10. Owner: runtime/API integration lead.

One durable mission identity across console/API/CLI; generic goals, permitted inputs/tools, graph, execution, cancellation/review and artifacts. No secondary demo executor. Reuse existing agent and persistence libraries after verifying compatibility.

Accept: three unfamiliar tasks across two families; same mission submitted/viewed across interfaces; actual service restart/reopen; wrong output rejected; unsupported task honest; no known-answer path. See G11 contract for details.

## G12 / V1.2 — INF-121: exact-route admission and concurrent pool

Status: queued; schema/adapter work may run independently, operational gate depends on G10/G11. Owner: inference lane.

Every model call/retry goes through the broker. Exact route/account identity, independently evidenced auth/eligibility/health/capabilities, atomic shared-quota reservations, deadlines/reset/cooldown and accounting. No always-true local route or unmetered hidden model calls. Reuse configured accounts; browser hand off only essential human steps.

Accept: actual overlapping calls to two independent remote providers in one mission, plus actual local inference/fallback; safe unavailable/quota behavior; failed/stale evidence denied; no double allocation. Live capacity missing = gate blocked, not simulated pass.

## G13 / V1.3 — EVAL-131: task/size evidence and selection

Status: queued; input/grade contracts may start early, integrated gate depends on G11/G12. Owner: evaluation lane.

Three actual model configurations; four task families and four sizes. Measured coverage matrix, calibration/held-out separation, predeclared quality/uncertainty and resource rules, exact prompt/tool/model versions, all outcomes and overhead. Invalid/unsupported cells remain explicit; qualify routes only where evidence supports them. Every required family/size needs at least one qualified route, not every model qualifying at every size.

Accept: routing uses observed matching profiles and handles failure via bounded repair/subdivision/escalation; compare smaller-worker pipelines with direct execution including overhead. The contract's screening minimum is not automatic qualification. No forged model results or leaked reference answers.

## G14 / V1.4 — SWARM-141: adaptive graph and organization

Status: queued; follows G11/G12 contracts and G13 qualification. Owner: orchestration lane.

Validated graph revisions for spawn/split/merge/reassign/cancel/review and multiple planning approaches; independent investigations, evidence exchange, duplicate suppression and bounded delegation. Separate logical agents, active sessions, requests and processes. Preserve permission/resource checks on every expansion.

Accept: real mission expands on discovered work and contracts on convergence; two capable planning/review configurations contribute; smaller qualified workers actually run concurrently. Separately exercise 10/50/100 logical assignments and measure permitted real inference concurrency. Compare elastic/single/fixed approaches fairly; no hash-only proof or fixed permanent team ceiling.

## G14 final — LIVE-142: clean installation and live acceptance

Status: queued; requires integrated G10-G14 behavior and current evidence. Owner: independent QA lane with lead review.

Run the final campaign in V1_4_EXECUTION_CONTRACT.md: all applicable checks, 12 preregistered positive missions across supported work, at least six specified failure scenarios, real provider overlap/fallback, real graph adaptation, actual restart and an observed 24-hour private/live operating window. Keep all attempts and triage every error. Revalidate relevant changes; do not fabricate time or cherry-pick only successes.

Accept: no known unresolved supported-V1.4 defects; no unexpected application errors in the accepted campaign; no unapproved spend/secret leakage/duplicate side effects; current independent review. Missing live prerequisite = implemented/live-blocked with precise action. Deliver candidate SHA/draft PR, actual startup commands/address, evidence index and known-issue matrix. Final main merge/release stays with operator.

## Immediate next action

Acknowledge LEAD-20260920-003. Start FIX-001/FIX-002 reproduction and FIX-004 local setup in separate ownership lanes. Follow START_CURSOR_TO_V1_4.md. Do not stop at the old repair-only instruction; do not skip the repair gates either. Continue approved implementation through V1.4 and keep the lead informed.
