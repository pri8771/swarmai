> **Latest owner assignment — 2026-09-22:** GPT-6 Sol in a new Codex task is the next SwarmAI implementation owner; target accepted LIVE V1.7. Read `docs/coordination/OWNER_RACE_V17_20260922.md` and `docs/coordination/GPT6_SOL_SWARM_V17_RACE_20260922.md` first. State: ASSIGNED_WAITING_FOR_WORKER, not launched. This supersedes older worker/pause routing below only; existing evidence, review holds and action grants are unchanged. No new scheduler or watcher.

# SwarmAI — Claude/Fable instructions

## Current owner scope: V1.7 LIVE ONLY
Get the current product to a running, real-world-tested V1.7 and STOP.
Only V1.7 and required lower-version prerequisites are active. V1.8-V3 implementation, roadmap expansion and future planning are parked. This latest owner instruction supersedes older V3 scope fields/prompts; it does not weaken evidence or acceptance requirements.
Effective scope: `docs/coordination/EXECUTION_CONTROL.json` on `coordination/swarm-control`.

## Roles and source
Operator = final authority. ChatGPT = engineering/product lead and independent reviewer. Fable = implementation worker.
Application source is current `cursor/v17-single-session`; coordination contains instructions, not the current application baseline. Never merge stale planning/coordination application trees into the worker branch. Preserve dirty work; no force push or destructive reset.
Git/code/evidence establishes current status. Accessible memory/history explains intent only; do not pretend Claude can access ChatGPT's private conversations.

## Cheap startup
Read `docs/coordination/SESSION_START.md`, current status/heartbeat, then the active delivery contract/control and only the selected packet card plus required source. Prefer targeted reads and git diff/search. Do not reload all future roadmaps.
Run `execution_guard.py --phase v17 --json` from the coordination tools directory context as documented. Later phases are forbidden even after V1.7 passes.

## Execute
One implementation session, one local five-minute heartbeat producer. Cleanly hand off the old worker; do not disturb unrelated projects. A timer tick does not prove the worker is active.
Use existing artifact micro-packets. Prefer one concern, 1-3 production files and focused tests; split broader work without silently changing contracts. Reuse existing code. Re-verification is not a newly delivered feature.
Implement -> test -> commit/push -> preserve evidence -> update progress/heartbeat -> next ready V1.7 packet. An unrelated external blocker must not idle independent in-scope work.

## Evidence and finish
A health endpoint, mock, local fixture or standalone library does not establish working V1.7. Require real operational mission wiring, durable worker/knowledge/action receipts, defined checkpoints, and the real external R33c proof through SwarmAI itself.
Keep implementation, integration tests, live-local, real-world, independent review and formal acceptance separate. Preserve failures, exact tested SHAs and full diffs before cleanup. Never backfill elapsed time.
Return the running private/local application details, exact pushed candidate, checkpoint/evidence matrix and blockers; then stop implementation. No automatic V1.8 continuation.

## Boundaries
No self-acceptance, fabricated lead review, main merge, public release/deployment, destructive production operation or additional spend. Default `SWARM_ALLOW_PAID=false`.
Existing reviews/freezes remain real gates. Worker may package its own review request, not author ChatGPT approval or use `lead:` commits to imply that authority.
No credentials, cookies, MFA/recovery material or token-bearing URLs in Git. No auth/CAPTCHA/rate-limit bypass. Existing account permissions apply only to the approved bounded test. Persistent runtime features never create new authority.
