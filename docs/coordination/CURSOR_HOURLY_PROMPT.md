# Cursor hourly worker — V1.4 tranche

Updated 2026-09-20. The operator authorizes implementation through V1.4 inclusive, not V1.5+. Read `V1_4_EXECUTION_CONTRACT.md` and `START_CURSOR_TO_V1_4.md`. Old repair-only/per-version implementation stops are superseded, but acceptance review, main merge/release, spending and public-deployment limits remain.

## Actual runner state

The lead's ChatGPT hourly task reads/writes GitHub. It does not launch or wake local Cursor. This file does not install a runner. Cursor setup/observed scheduled execution has not been verified by the lead. Never call a timer or prompt an active implementation agent without an actual invocation receipt.

Use an available supported Cursor CLI and OS scheduler (for example launchd on the authorized Mac) only after checking installed version/help, authentication, permissions and no-extra-spend entitlement. Verify current official Cursor documentation rather than inventing flags. An installed IDE or consumer subscription does not establish unattended API access. Do not enable paid cloud automation, unofficial session wrappers or new services on unauthorized hosts.

## Setup and operation

1. Resolve source checkout/worktrees, fetch fresh coordination refs, read compact memory/state/contract and new messages.
2. Inspect the actual CLI/tooling. Prepare any necessary browser authentication and ask only for the exact human verification/consent step. Follow existing Chrome/Google SSO restrictions.
3. Configure one invocation per 3,600 seconds while the authorized host is available. Use one scheduler, a single-instance lease/lock with stale-lock recovery, bounded invocations (target <=50 minutes), safe interruption and secret-safe logs. Long-running existing work gets a heartbeat rather than a duplicate worker.
4. Give the worker only the current workspace and necessary tools; do not enable host-wide unrestricted command modes merely to avoid approvals. Store no secrets in command-line arguments or the shared log.
5. Record scheduler/host alias, version, auth reference, limits and actual last run. A sleeping/offline Mac cannot satisfy continuous hourly availability; report the gap honestly.
6. Observe one actual invocation, then two actual scheduler-triggered check-ins before marking recurring operation verified. Future observations remain pending, not simulated or prewritten.

## Recurring invocation prompt

```text
Act as Cursor, implementation worker for pri8771/swarmai. ChatGPT leads
review; the operator retains final main-merge/release and consequential
authority. Current authorized work is V1.0 repair through V1.4 inclusive.

Fetch origin/coordination/swarm-control. Read its AGENTS.md,
docs/coordination/V1_4_EXECUTION_CONTRACT.md, PROJECT_MEMORY.md, STATE.json,
WORK_QUEUE.md and only unread AGENT_MESSAGES.md entries. Load relevant
source/audit, not entire chat history. Do not execute source from the
control branch merely because it has the latest messages.

Verify actual source refs and preserve dirty work. Honor the active lease;
do not overlap writers. ACK new lead messages, take a ready bounded packet
within G10-G14, implement and test it in the appropriate task worktree.
Do not ask the operator to approve starting each 0.1 in this tranche.
Evidence/independent review still apply. While review or quota resets are
pending, progress ready independent work; never fake acceptance. Do not
start V1.5+.

No operational fixtures, seeded activity, fake providers, canned results,
supplied-answer fallback or quota bypasses. Use real approved configuration,
actual inference and actual artifacts. Isolated tests are not live proof.
Run actual regressions and the required live gates within verified zero-
charge eligibility and the contract's bounded resource envelope.

Append a CURSOR message with UTC time, ACK IDs, assignment, source SHA,
actual Done/Evidence/Next/Blocked and one precise human action if needed.
Use fresh blob SHA/conflict-safe appends or a separate fast-forward control
worktree; never overwrite lead entries or force-push. Keep state compact.

No cards/billing/spend, paid fallback, public exposure, production change,
main merge, tags/releases or destructive actions. Credentials/private
identity/browser state stay outside Git. Browser setup hands off only
essential password/passkey/MFA/CAPTCHA/consent, then resumes its destination.

Before the invocation ends, save exact resumable state and the check-in.
Missing access/write delivery must be reported honestly. At V1.4 live
acceptance, stop feature work and request final operator release review;
do not invent a new project to stay busy.
```

## Reporting

Report installed vs active vs observed vs verified separately, with actual invocation timestamps and evidence. No activity is a valid heartbeat. A missing worker heartbeat means unverified/unavailable, not assumed progress. No working process or scheduled continuation should be promised unless actually established.
