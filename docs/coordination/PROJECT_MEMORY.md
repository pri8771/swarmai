# SwarmAI compact project memory

Last curated: 2026-09-20. Read this plus STATE and unread AGENT_MESSAGES before loading other context. Target <=1,200 words. This is accepted project context, not a transcript, credential store or independent proof that execution occurred.

## User direction

SwarmAI is a reusable self-hostable product, distinct from the operator's personal portfolio. It should let an elastic swarm tackle a problem. Multiple capable planners/reviewers may supervise or collaborate with smaller task-qualified workers. Use all approved inference sources concurrently, not just a sequential fallback list. Swarm should create/retire/reorganize agents dynamically according to useful work, dependencies, measured model fitness and resource capacity. Ordinary code/tools are first-class; every action need not use AI. CrewAI was an idea, not mandatory.

Build around existing open-source libraries rather than duplicating infrastructure. Evaluate models on standard task families and sizes; count all delegation/repair/review overhead. Context should load relevant accepted knowledge and evidence, not entire histories. Distinguish actual execution from catalog entries, fixtures, simulated load and prewritten answers.

The operator's deployment preference is free cloud coordination where feasible, with optional local workers/inference and tested local recovery. R730/T640/Mac are optional resources, not a requirement that the home machine always be online. Free resources have limits. No additional spending, card attachment, paid fallback, top-ups or unapproved production exposure.

## Governance

Operator: Priyansh. ChatGPT is engineering lead; Cursor is implementation worker. Both should check in at least hourly when their actual scheduled runners are available, describing completed work and next work. Lead reviews evidence and sets bounded assignments. Operator retains each 0.1 promotion/merge and consequential external-action approval. Roadmap is not blanket authorization to rush to V2.

Coordination-only branch: `coordination/swarm-control` in `pri8771/swarmai`. Source branches remain separate. Read fresh refs, preserve unrelated local changes, use isolated worktrees and conflict-safe message appends. Never force-push. Keep messages concise with IDs/acknowledgements; archive acknowledged history with pointers.

## Verified repository snapshot

Source audit pinned at main `b9141fa3150f853586dede0334a47b344571bc16`, 2026-09-20. Repository package/status is `1.0.0rc1`, no public launch, not a verified stable V1 product. V1 RC PR #12 was merged, and a later status PR #13 produced this main snapshot. This history does not itself prove feature completion.

Main CI run `35529361557`, job `106127102217`, failed lint with 33 errors; mypy/pytest were skipped in that run. Workflow only scheduled contracts/spikes pytest, not the full product suite. Main metadata reported unprotected; full administrative ruleset settings were not audited.

Targeted source audit found: known demo tokens in default app; cross-project report/history and idempotency problems; file-presence release checks presenting broader verification; parser-specific mission with prewritten fallback answer; local-only sequential demonstrated mission routing; hash-oriented scale harness with force-progress admission bypass; registry treating configured/unprobed values as readiness; synthetic recovery/timeout helpers; disconnected in-memory API fixtures versus separate CLI mission execution. Do not assume every component is defective; integrate/reuse useful contracts, broker, tests and tooling.

Audit scope: source and CI evidence, not a full local test rerun, live-provider audit, full security certification or browser reproduction. No provider keys/accounts were inspected or tested by the lead in this audit. Do not claim a measured production exploit or spend event.

Details and pinned sources: `AUDIT_V1_2026-09-20.md`.

## Current execution priority

V1.0 repair gate before feature-version promotion. Cursor assignments: FIX-001 full truthful CI; FIX-002 auth/project isolation with negative tests; FIX-003 meaningful acceptance/evidence gates; FIX-004 platform login documentation/session recovery and verified hourly worker runner. Parallelize only independent file ownership. No public deployment while security blockers remain.

Roadmap after repair: 1.1 unified generic runtime; 1.2 concurrent inference pool; 1.3 task/size qualification; 1.4 elastic graph; 1.5 durable distributed workers; 1.6 scoped memory; 1.7 reliable tools/browser sessions; 1.8 cloud-first/local recovery; 1.9 independent beta/self-development; 2.0 accepted elastic product. V3 direction: ongoing goals across many missions with governed learning, fleet/resource coordination and controlled self-development.

## Login and browser context

Existing onboarding docs require normal Priyansh/Default Chrome for interactive provider setup; do not automate Google SSO through Playwright/Selenium/CDP. Prior onboarding reports claim many accounts/keys were configured; those are historical reports, not a fresh session guarantee. User encountered an Apply link while logged out; the actual failed destination/browser session has not been reproduced here.

Record per-platform account aliases, login method, official entry points, browser-profile reference and last verification. Keep real email/username mappings, passwords, keys, cookies, auth state and sensitive return URLs outside Git in secure local storage. Existing inventory contains a personal email and stale status text; Cursor should sanitize current documents without rewriting history automatically. See `../onboarding/PLATFORM_ACCESS.md`.

Restore the right identity/session and resume the intended page; ask only for the essential MFA/passkey/password/CAPTCHA/consent step. Distinguish a normal protected HTTPS page from an IDE-specific or expired signed link. Opening a page is not applying/submitting/deploying.

## Automation state

The ChatGPT lead review was successfully scheduled hourly in America/New_York on 2026-09-20. It checks GitHub and can append review messages; it does not control or wake Cursor locally. No available Cursor connector was found in the plugin search. Cursor's actual recurring runner is pending local setup/verification. Cursor native cloud automations exist but are billed; do not assume they fit zero-additional-spend. A local scheduled CLI is a candidate after verifying authentication, entitlements, permissions, no-overlap locking and host availability. Mark missing heartbeats explicitly.

Never place secrets, full conversations or private reasoning in this memory file. Supersede stale facts with dated evidence rather than silently carrying them forward.
