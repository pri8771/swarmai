# SwarmAI lead work queue

Updated 2026-09-20. Current authorized work: V1.0 repair/revalidation, not automatic V1.1–V2.0 promotion. Source audit: main `b9141fa3150f853586dede0334a47b344571bc16`; recheck current main and relevant changes before reproducing findings. The control branch is not the source baseline. ChatGPT reviews; Cursor implements; the operator promotes checkpoints.

Latest owner directive is mandatory: no demo/mock runtime data. Read REAL_DATA_POLICY.md before any packet. Preserve existing isolated unit/security tests; never use test doubles, prewritten answers or replayed success as evidence that the actual swarm works.

## Execution rules

Claim a packet by appending a CURSOR message and recording branch/base/owned files. Use separate worktrees for independent tasks. Do not let two workers edit the same module, shared schema or lockfile without one integration owner. The lead may reorder packets based on evidence. A stopped worker leaves a compact next action and releases its lease. No fake heartbeat or claim of live verification.

Status progression: assigned -> in_progress -> implemented -> tests_verified -> lead_reviewed. Checkpoint promotion is separate and requires the operator. A failed or missing required result blocks that result, not unrelated safe implementation work. Never erase the failure by changing the definition after seeing it.

## FIX-001 — Full CI and an honest baseline

Status: assigned to Cursor; implementation evidence not yet received.

Priority: P0. Audit: AUD-01, AUD-11. Ownership: CI, lint/type fixes coordinated with module owners, release-status/handoff truth. Preserve the pinned historical V1 report; add current correction rather than rewrite history.

Do: reproduce the actual lint failure; fix causes without blanket excludes; run independent lint, types, backend and frontend checks; cover all applicable suites rather than only contracts/spikes. Separate gated live checks so absent credentials do not silently become passes. Pin source and dependency versions. Use local tests when extra CI billing is unverified; report real GitHub CI state without rerunning chargeable jobs blindly.

Accept: exact commands, exit codes, backend/frontend test inventory and skipped-test reasons are saved; no disabled security tests; correct CI is run at the candidate SHA under permitted resources. Structural docs-only checks remain separate. Correct stale current handoffs/version wording.

## FIX-002 — Authentication, project boundaries and real startup

Status: assigned to Cursor; implementation evidence not yet received.

Priority: P0 security. Audit: AUD-03/04/10. Ownership: API auth/routes/store; coordinate FIX-005 fixture removal in these modules.

Do: remove seeded demonstration identities from installed runtime; use per-install auth with safe unconfigured behavior. Authorize before caches/data. Scope idempotency by actor/project/operation/request digest; reject mismatched payload reuse. Apply real owner/project checks to reports, artifacts, history, approvals and worker operations. Distinguish missing resource from forbidden resource.

Accept: negative regressions reproduce and close the known failures; two independently authorized principals cannot cross project boundaries through any tested route or key reuse. Historical/file-backed records are not an authorization escape hatch. Known demo tokens fail under operational configuration, including a non-loopback client. No source tokens/passkeys/secrets in logs. Keep deployment loopback-only pending review.

## FIX-003 — Behavioral acceptance, not success labels

Status: assigned to Cursor; implementation evidence not yet received.

Priority: P0 integrity. Audit: AUD-02/08/09. Ownership: release verification/evidence schemas/readiness; coordinate provider model with broker owner.

Do: replace hard-coded `offline_tested=yes` and helper flags with actual current evidence. Remove the assumption that key presence means authentication/free eligibility/task competence. Structural packaging checks must not imply tests ran. Mark historical simulated recovery/timeout/scale proofs accurately. Define real process-failure/cancellation/recovery tests using the actual runtime; leave unexecuted ones blocked.

Accept: a missing/stale/failed test attestation prevents verification for that item. Breaking actual runtime behavior fails the acceptance gate even when docs/manifests exist. Unsupported live checks show unknown/blocked, not green. Provider statuses keep configured/authenticated/inference-tested/qualified separately. No guessed zero-charge eligibility.

## FIX-004 — Login/session records and actual hourly worker

Status: assigned to Cursor; local environment needed.

Priority: P1; perform alongside non-conflicting repair. Ownership: onboarding docs, private access mapping, local scheduler configuration and sanitized evidence.

Do: follow ../onboarding/PLATFORM_ACCESS.md. Populate real login methods/profile aliases/private secret references using the authorized browser; sanitize existing tracked private identity fields without rewriting history. Reproduce the reported Apply-link failure when its actual destination is available, restore the right session, and resume the intended page. Do not ask the user to redo all signup steps. Do not fabricate the failed link.

Set up CURSOR_HOURLY_PROMPT.md on one supported, verified no-extra-spend runner. A normal browser profile, local CLI or task scheduler is not assumed available merely because it is documented. Inspect tool/auth/entitlement first. No paid cloud agent activation. Use no-overlap locks, timeout, resumable work and secret-safe logs. A scheduling instruction alone is not a running worker.

Accept: real session-expiry/resume evidence with no duplicate side effect; private identity map remains outside Git. First actual invocation recorded, then two real scheduler-triggered check-ins observed before marking the hourly runner verified. Missing future executions remain pending; do not claim them prospectively. If an operator verification is unavoidable, prepare the exact page/step and continue other tasks.

## FIX-005 — Remove demo dependence from normal operation

Status: assigned to Cursor; implementation evidence not yet received.

Priority: P0 product truth. Audit: AUD-05/06/07/10. Ownership: mission worker/planner/runtime, fixture adapter boundaries, release/console wiring in coordination with FIX-002/003.

Do: inventory all operational imports/defaults for fixtures/fakes/demo routes/GOOD_FIX/hash-only swarm claims. Remove known-answer substitution and the assumption that every problem is the parser bug. A failed model output must fail, retry within policy, subdivide or escalate—never install a supplied answer. Remove unconditional force-progress dispatch when quota admission denies work. Delete normal-mode fixture seeding and fake ready/connected values; show real empty/error states.

Integrate existing generic execution/broker/store modules when they are ready. Do not add a second runtime or replace an absent integration with another mock. If a real generic capability is not yet wired, report unsupported/blocked and retain it as an explicit unfinished original requirement; do not claim the repaired baseline is a finished stable swarm. Completing that capability is planned in V1.1, not a retroactive V1 success.

Accept: clean operational install contains no synthetic users/projects/provider activity. Invalid model output cannot trigger GOOD_FIX or accepted task status. Denied quota never executes. Live product screens show actual data or actual absence. No fake fallback when API fails. Real local/remote evidence is separate from isolated tests. Status and README state exactly what is still missing.

## Integration and review gate

After independent packets pass, integrate fixes into one repair branch based on the latest verified source. Re-run cross-module checks on that combined SHA. Append a CURSOR message with changes, actual evidence, remaining original requirements and requested lead review. Keep old audit immutable; add a resolution matrix with finding ID, fix SHA, regression evidence and reviewer status.

The V1 repair gate certifies a safe, honest baseline only. It does not rename unimplemented swarm behavior as complete. The first full real generic mission is V1.1; concurrent qualified remote sources are V1.2; later gates are in ROADMAP_V1_TO_V3.md. No next-version merge, tag, public release or deployment without operator promotion.

## Immediate action

Begin FIX-001 baseline reproduction and FIX-002 security negatives; run FIX-004 setup independently. Assign FIX-005 with explicit shared-file coordination. Do not spend the whole session rewriting plans. Do not start another portfolio project. Post an acknowledgement and actual work evidence to AGENT_MESSAGES.md.
