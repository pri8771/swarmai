# SwarmAI compact project memory

Curated 2026-09-20 after LEAD-20260920-012 / CURSOR-20260920-020. Read this, STATE, V1_4_EXECUTION_CONTRACT and unread/new message pointers; do not reload whole chats. This stores accepted decisions and verified observations, not secrets or proof of unperformed work.

## Owner authorization and product direction

Implementation is approved continuously through V1.4 inclusive: V1.0 repair -> V1.1 -> V1.2 -> V1.3 -> V1.4. Do not ask the operator to start each 0.1. Independent evidence review still gates acceptance. Main merge, release/tag/publication, public deployment, new billing/spend, destructive actions and V1.5+ implementation are not authorized. Stop feature work after V1.4.

SwarmAI is a reusable self-hostable elastic problem-solving runtime. Multiple capable planners/reviewers may coordinate smaller task-qualified workers. Approved inference routes should operate concurrently. Agents can propose specialists/splits/alternatives; software enforces permissions, dependencies and resource admission. Ordinary code/tools are first-class. CrewAI is not mandatory. Reuse sound libraries.

No operational demo data, fake providers/activity, supplied answers, mock-success fallback or quota bypass. Test fixtures may exist only as isolated test/dev fixtures and never count as live proof. The operator prefers zero additional spend; bounded verified-zero-charge live validation is authorized by the V1.4 contract.

## Verified source and CI

Audited main remains `b9141fa3150f853586dede0334a47b344571bc16`. Draft PR #14 current tip is `c1ebf20abb10c53c0209dcc15bfa5bf89efba510`. Its only change over lead-reviewed code tip `6669d37827d487206ee6c71734d4e2c64b475906` is `docs/evidence/GATE_MATRIX.md`; application code is unchanged.

Exact-tip Actions `35543156880` is green. The reviewed application-tree PR run `35543013930` showed console npm install/lint/Vitest/build success, Ruff success, mypy **139 source files**, install/package success, Alembic head `9eb193b10f4e`, and broad non-live pytest **267 passed, 2 skipped**. CI DB integration remains an honest skip without `SWARM_DATABASE_URL`; prior local PostgreSQL evidence was worker-reported, not rerun by lead. The live-gated job is a blocked notice, not live product evidence.

## G10 review — source/CI repaired, checkpoint NOT accepted

LEAD-012 independently verified FIX-002, FIX-003 and FIX-005 at the current code tree:

- Operational bootstrap uses install-local project identity and rejects fixed demo project IDs; demo principals are fixture-only.
- Worker/approval ownership and inspected operational idempotency paths are project-scoped and authorization precedes cache/action access.
- ProductStore/API/capacity default operational state is empty/unknown rather than mock; fixture mode is explicit; demo side-effect route is fixture-gated.
- Console defaults live, does not merge mock fixtures into operational snapshots or recover errors with fixtures; Expand/Contract fixture mutations appear only in explicit mock mode.
- Release evidence requires exact candidate SHA, command/result, mode, freshness and evidence-kind identity, with negative regressions for missing/wrong/stale/failed values.

**Only G10 contractual blocker now recorded is FIX-004:** `cursor agent status` and `cursor agent whoami` remain **Not logged in**. Scheduler/probe-only check-ins exist but there are zero authenticated unattended worker receipts. Keep `SWARM_HOURLY_SKIP_CURSOR_PROBE` until auth succeeds. Then capture one bounded authenticated manual worker invocation and two genuine hourly scheduler-triggered authenticated worker invocations. G10 is not accepted before that evidence.

## Later gates

G11/RUN-111: real $0 local evidence now includes three unfamiliar extract/triage missions on actual Ollama responses with shared durable IDs across API/CLI and a console-shaped snapshot. **Not accepted.** Current evidence is not an actual browser console create/observe journey. Older restart/reopen evidence reports `execution_mode: mock`, and older acceptance-control artifacts are not bound to the current repaired candidate; relevant source changes invalidate them as final proof. Re-run actual console/API/CLI, restart/reopen, cancel, unsupported and wrong-output evidence in operational mode on the exact candidate. Use task-defined hidden/deterministic acceptance checks where feasible; no grader answer visible to workers.

G12/INF-121: local admission/reconcile is useful preparation. Three brokered local calls settle and the next is honestly denied on exhausted quota. Required overlapping real calls through **two independently authorized remote providers** remain absent. No G12 acceptance.

G13/EVAL-131: latest screening covers about **60 provisional cells** across S/M/L/XL, six families and three local model configurations at small n. Screening only. Before more volume, preregister qualification/uncertainty rules and total planning/retry/review overhead. No qualified profiles accepted.

G14/SWARM-141: offline expand -> admission denial -> contract -> expand-after-contract is useful preparation and explicitly not live multi-planner evidence. G14 remains unaccepted. LIVE-142 (12 positive, 6 negative, 24-hour observed protected live window) has not started.

## Coordination and login

`coordination/swarm-control` is transport, not source baseline. ChatGPT leads/reviews; Cursor implements/tests. Use fresh SHAs, isolated worktrees and conflict-safe writes. LEAD-012 is in `docs/coordination/messages/LEAD-20260920-012.md`. The lead review automation does not wake local Cursor.

Use platform aliases/methods/profile references in Git; keep real identities, keys, cookies/browser state, MFA/recovery data and sensitive return URLs outside Git. Existing Chrome rule: normal Priyansh/Default profile; no Playwright/Selenium/CDP for Google SSO. Current operator action for FIX-004 is only completing a fresh `cursor agent login` browser/passkey/MFA/consent flow with the CLI waiter active, then verifying `status` + `whoami`. No paid cloud automation.
