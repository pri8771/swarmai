# Cursor: finish real behavior, starting with V1 repair

This is the current start prompt. It supplements CURSOR_HOURLY_PROMPT.md and supersedes earlier instructions to build demo-driven product paths. ChatGPT is engineering lead, Cursor is implementation worker, and the operator retains checkpoint/merge, spending and consequential-action authority.

## Execute, do not generate another broad proposal

Work in repository `pri8771/swarmai`. Preserve useful existing code and all unrelated/uncommitted changes. Inspect the actual workspace and source refs; do not assume a Downloads handoff directory is the product checkout.

Fetch `origin/coordination/swarm-control` without switching/resetting your source worktree. Read from that branch:

1. `AGENTS.md` and `docs/coordination/PROJECT_MEMORY.md`.
2. `docs/coordination/STATE.json` and `WORK_QUEUE.md`.
3. The unread tail of `AGENT_MESSAGES.md`.
4. `REAL_DATA_POLICY.md` and the relevant findings in `AUDIT_V1_2026-09-20.md`.
5. `CURSOR_HOURLY_PROMPT.md` and `docs/onboarding/PLATFORM_ACCESS.md` for the setup packet.

Use `git show origin/coordination/swarm-control:<path>` or the GitHub API. This branch carries communication, not necessarily the latest application code. Resolve actual main/CI, compare with the audited `b9141fa3150f853586dede0334a47b344571bc16`, and create/reuse a bounded repair branch from the correct source base. Never erase another contributor's work. Do not merge the entire control branch into source just to copy documentation; add only needed instruction files through review.

## Current gate and immediate work

Current gate is V1.0 repair/revalidation. The source is `1.0.0rc1`, not an accepted completed stable swarm. Do not advance version labels to conceal missing V1 requirements.

Acknowledge the latest LEAD entry with your source SHA, intended worktree, claimed packet and first test. Execute FIX-001 through FIX-005 from WORK_QUEUE. Begin with baseline/CI and the security failures; account/session and scheduling setup can run independently. Parallelize only actual independent ownership in isolated worktrees. One integration owner controls overlapping API/store/runtime changes and shared contracts.

Confirmed audit targets include:
- CI stops at Ruff; subsequent checks did not run, and the configured pytest command covers only a subset.
- The normal API app issues known demo tokens.
- Project-denial exceptions are swallowed in report/artifact handling; idempotency can be read before project authorization.
- The mission worker targets a known parser and installs GOOD_FIX when model output fails.
- Demonstrated mission execution is ordered/sequential through local inference, not the promised concurrently governed provider pool.
- Release verification uses file presence and hard-coded verification labels rather than real behavioral attestations.

Reproduce the relevant failures, implement real fixes and produce exact evidence. Preserve the historical audit and add resolution evidence. Do not blanket-ignore lint, skip security tests, relax the expected result, or edit status files to manufacture completion.

## No demo or mock product behavior

No synthetic activity, seeded accounts/projects, fake connected providers, default demo credentials, mocked successful actions, canned model outputs, known-answer patches or silent fake fallback in the normal application. Do not merely change the label.

Fresh installation shows real empty/unconfigured state. Missing access shows blocked/unknown. A failed model response stays failed or takes a genuinely permitted repair/escalation path. Do not substitute expected solutions. Real deterministic tools are valid, but identify them honestly rather than claiming agents reasoned through their result.

Do not delete useful isolated regression tests. Existing test-only doubles and controlled failure injection stay outside runtime and never count as live acceptance. Do not add more mock-led demonstrations. Use real database/process/browser/local-model integrations where authorized; cloud tests require verified exact-route zero-charge eligibility. No fake success when credentials are absent.

Implement the real missing capability or report it unfinished. Do not create another superficial module with passing placeholder tests. The original concurrent multi-provider, dynamic-swarm and generic-mission goals remain obligations, not optional showcase features. The next approved gates in ROADMAP_V1_TO_V3.md complete/extend those behaviors; they are not permission to call them already complete.

## Login and protected-link handling

Populate PLATFORM_ACCESS.md with platform/account aliases, verified login method, official entry points, browser-profile reference, private credential reference, current session-check time and precise recovery action. Keep actual emails/usernames/passwords/API keys/cookies/MFA recovery data/browser-state files outside Git in the protected local inventory.

Use the existing authorized normal Chrome profile for interactive provider setup; preserve the repo's no-Playwright/Selenium/CDP rule for Google SSO. Do not infer a current session from a historical setup record or stored API key.

When an Apply/dashboard link redirects to login, preserve the intended safe destination privately, restore the correct identity, hand over only the password/passkey/MFA/CAPTCHA/consent step, then resume and verify the original page. A signed-out, wrong-account, expired-signed-link or IDE-local deep link are different cases. Bound retries and prevent duplicate consequential actions. Opening a form does not authorize submitting it.

Do not invent the actual failing link if it is absent; record that specific reproduction input as missing while completing the registry/session behavior. Use available browser tools before returning any generic manual-signup checklist.

## Hourly check-ins and real runner setup

Read CURSOR_HOURLY_PROMPT.md. The lead's hourly GitHub review exists. You must establish/verify the worker side; writing this prompt does not run an IDE.

Inspect installed current CLI/native capabilities, authentication, permissions and actual included-usage/billing controls. Prefer a supported local CLI/OS scheduler with a 3,600-second interval, no-overlap lock, bounded invocation, clean timeout and resumable state on an authorized available host. Do not configure billed cloud automations, on-demand usage, broad command permissions or a paid runner under the zero-additional-spend rule. Unknown entitlement blocks unattended model calls, not a truthful no-progress heartbeat.

When permitted setup is complete, perform an observed invocation and record it. Mark scheduled operation verified only after two genuine scheduled check-ins occur; do not wait idly or invent a future success. Continue repair during the current session. A sleeping/offline Mac cannot guarantee hourly work. Report the exact availability/access limitation rather than promise 24/7 execution.

## Evidence, messages and completion

During active work post at least hourly and at handoff: unique CURSOR message ID, UTC time, acknowledged LEAD IDs, packet, branch/SHA, Done, actual Evidence, Next, Blockers, exact operator step. Do not fabricate a LEAD reply. Use a dedicated control worktree or current-SHA GitHub writes; fetch/re-read on conflicts and preserve other entries. Source work and messaging must not corrupt each other's worktrees. No forced pushes.

For each packet run the required backend/frontend/type/security checks, actual integration checks and negative paths. Include exact commands, versions, exit codes, skipped checks, artifact references, evidence mode and any admitted inference/usage. No secrets in prompts/logs/artifacts. Unknown spending is not a verified $0 result.

Use the existing supported no-extra-spend development resources. No billing activation, payment methods, paid fallback, production exposure, destructive reset, automatic merge/tag/release or unrelated portfolio work. Push scoped implementation branches and sanitized evidence when safe; checkpoint promotion remains the operator's decision after lead review.

Continue through all feasible work in the authorized repair gate without asking for routine reversible decisions. Missing credentials do not block code and deterministic tests. Save compact resumable state before context/session limits. Do not claim asynchronous work unless a real runner has been activated and observed.

At gate completion provide a finding-by-finding resolution matrix and real acceptance evidence, update the queue and send the lead a review request. Stop before promoting the next 0.1 version. Report remaining original requirements accurately. Begin now with fresh refs, acknowledgement and the first failing regression—not another roadmap.
