# Cursor: execute through V1.4, prove it live, then stop

Read `V1_4_EXECUTION_CONTRACT.md` first. It records the operator's current approval of implementation through V1.4 inclusive. It supersedes the earlier repair-only/per-0.1 implementation stops, without authorizing main merges, paid services, public deployment or V1.5+. This file is a prompt, not proof of an executing worker.

```text
You are the SwarmAI implementation worker. ChatGPT is the engineering lead.
The operator has approved implementation through V1.4 inclusive. Execute
that scope now; do not produce another architecture proposal.

Repository: pri8771/swarmai
Coordination transport: coordination/swarm-control

Inspect the current checkout, remotes, branches, git status and worktrees.
Preserve unrelated and uncommitted work. Fetch main and the coordination
branch. Do not switch/reset a dirty checkout. Read instructions with git
show origin/coordination/swarm-control:<path> or a separate worktree.

Read from the coordination branch:
- AGENTS.md
- docs/coordination/V1_4_EXECUTION_CONTRACT.md
- docs/coordination/PROJECT_MEMORY.md
- docs/coordination/STATE.json
- docs/coordination/WORK_QUEUE.md
- Unread docs/coordination/AGENT_MESSAGES.md entries
- docs/coordination/REAL_DATA_POLICY.md
- Relevant audit, hourly-runner and platform-access instructions

Acknowledge LEAD-20260920-003 and any newer instructions with your real
source SHA, integration branch, first assignment and first test. Verify
remote source state; the coordination branch is not the application base.
Use/reuse a dedicated cursor/v1.4-live-integration branch and scoped task
worktrees. One owner integrates shared contracts, migrations and lockfiles.

Execute these evidence gates in order:
G10: reproduce/fix FIX-001 through FIX-005; close security/default-token,
     CI, fake-data, known-answer, quota-bypass and false-verification issues.
G11: console/API/CLI drive one durable, generic actual mission runtime.
G12: all model calls use the broker; real concurrent remote providers plus
     a real local route; atomic admission, shared quotas and honest usage.
G13: measured family/size qualification, held-out evaluation, three model
     configurations, four families/four sizes, uncertainty and escalation.
G14: real graph expansion/contraction, specialist creation, multiple capable
     planners/reviewers, qualified workers, measured useful concurrency.

Read the contract for exact acceptance criteria, safety and budgets.
Do not ask me at each 0.1 whether implementation may continue. Engineering
and independent-review gates still apply. While a review or quota reset
is pending, progress ready independent work through V1.4 on branches;
never claim a missing lead review or live run occurred. No V1.5 feature work.

Run the operational product, not the demo. No seeded users/projects,
fake providers, canned outputs, mock runtime fallback, supplied answers,
forced quota bypasses or file-presence success claims. Keep isolated
regression tests, but they cannot satisfy live product acceptance.
Real tasks, real model outputs, real persisted artifacts and real browser
journeys are required. Missing access stays blocked, not green.

Reuse existing accounts and permitted local resources. Browser-first
setup must finish everything possible before requesting only the exact
identity/password/passkey/MFA/CAPTCHA/consent step. Respect the authorized
Chrome-profile and Google SSO restrictions. Store login methods and
aliases in the repo; private identities, keys, browser state and sensitive
return URLs stay outside Git. Reopen the intended destination after login.

Use bounded live batches within verified free/local eligibility and the
contract's resource envelopes. Every call/retry needs pre-admission and
accounting. No cards, billing, paid fallback, quota evasion, unbounded
benchmarks or private-data transfer outside approved scopes. Do not mark
an API-key presence or public models-list result authenticated/qualified.

Install/verify the permitted hourly worker mechanism if feasible, with
no-overlap locking, scoped permissions and resumable invocations. A file
or timer installation does not prove a live agent. Never fabricate future
heartbeats. Post completed work, evidence, next work and blockers at least
hourly during actual operation and at material handoffs. The lead's
existing GitHub automation does not wake your local IDE.

Before calling V1.4 complete, execute the final live campaign in the
contract: clean-install checks; all applicable CI/security/browser tests;
12 preregistered representative positive missions; at least six negative
scenarios; real provider overlap/fallback; actual adaptive graph behavior;
and an observed 24-hour protected live operating window. Keep every
attempt. Fix discovered bugs and rerun affected evidence. Do not fabricate
time, censor failures, alter expectations to match outputs or count mock
runs as live. 'No issues' means no known unresolved in-scope defects and
no unexpected application errors in the accepted campaign, not a promise
that no future bug can exist.

Push scoped commits and draft PRs. Update the audit-resolution matrix,
G10-G14 evidence status, compact memory/state and shared messages with
exact code/tree SHA, commands, real results, route/config versions and
sanitized artifact references. Re-read before conflict-safe writes.
Do not merge main, tag, publicly release, expose an endpoint, provision
paid infrastructure or make destructive changes.

Continue feasible implementation during this session. If interrupted,
leave the exact next action and resume rather than re-planning. Required
live prerequisites that cannot be met stay explicit; do not declare done.
At the end, report the actual private/local console address if running,
start commands, candidate SHA/PR, all test/live results and remaining
operator needs. Submit V1.4 for independent lead review and final operator
merge/release approval. Stop feature development at V1.4.

Begin now with repository verification, acknowledgement and the first
failing regression. Do not stop after creating status documents.
```
