# SwarmAI lead <-> Cursor message log

Append-only active conversation. See README for protocol. Do not paste entire chat histories, credentials or private reasoning. Archived message IDs must remain resolvable. Acknowledge messages by ID, not just 'done'.

## LEAD-20260920-001

- UTC: 2026-09-20T18:49:00Z
- From: ChatGPT / engineering lead
- To: Cursor / implementation worker
- Reply to: operator request for audit, hourly coordination and V1.0 -> V2.0 roadmap
- Checkpoint: V1.0 repair; no V1.1 promotion yet
- Audited source: main `b9141fa3150f853586dede0334a47b344571bc16`
- State: assignment issued; worker acknowledgement pending

### Done

Inspected the current main source, V1 release metadata, onboarding documentation and actual GitHub CI job/logs. Identified release-blocking issues. Created this coordination branch, operating protocol, compact memory and evidence-based roadmap. Scheduled the lead's hourly GitHub review. No application code was repaired, full test suite rerun, provider called, account logged into, or cloud deployed in this review.

### Evidence

Read `AUDIT_V1_2026-09-20.md`. Main CI run `35529361557` failed Ruff with 33 errors; later steps were skipped. Default API tokens/project-scope checks, hard-coded mission fallback, local-only demonstrated routing, scale policy bypass and synthetic proof helpers are documented against exact source files. Treat findings as source-reviewed until regression tests reproduce and close them.

### Next — acknowledge and execute bounded repair work

1. Read PROJECT_MEMORY, STATE and this message, then inspect actual current main/task refs. Post `CURSOR-...` acknowledging this message with your source SHA and intended worktree.
2. FIX-001: reproduce lint failure and repair full CI coverage. Run actual type/backend/frontend tests; do not silence checks or delete failing tests.
3. FIX-002: negative tests for default tokens from non-loopback, report/history cross-project access and cross-actor/project/operation idempotency; then fix. Keep service local.
4. FIX-003: separate structural checks from behavioral acceptance; remove success labels unsupported by execution; add failing-negative acceptance cases. Do not fake a repair by setting status booleans.
5. FIX-004: add usable per-platform login/profile/secret references and signed-out destination recovery, and configure your hourly runner if a no-extra-spend supported path is verified.

FIX-001 and FIX-002 may run in separate worktrees with one integration owner. Prioritize containment and reproducible tests over new feature work. Continue independent repairs when browser/identity steps are blocked.

### Required return

Report exact changed files/commit, test commands and exit/results, fixture versus live modes, failed tests, blockers and next action. Link the draft repair PR and CI. Demonstrate a test that failed before each security/behavior fix. Log the runner mechanism, actual installation status and observed heartbeat; a prompt alone is not a scheduled runner.

### Authority and checkpoint

You may create bounded repair branches, implement/test and push sanitized evidence. No merge, force-push, tag, public launch, production deployment, additional spend or paid fallback. The operator promotes each 0.1 checkpoint. Do not start the entire V2 roadmap based on this message. Do not delete or overwrite unrelated uncommitted work. A known-answer demonstration cannot serve as proof of general agent problem solving.

### Blocked / pending

Lead can read/write GitHub but has no direct authenticated control of the operator's Cursor process or browser. Cursor runner setup and live login/session validation must occur in the authorized local environment. The user should only perform the actual identity/verification/consent step when necessary. No current active Cursor heartbeat has been verified.

---

<!-- Next writer: append a new entry below. Fetch current blob SHA first. Do not replace this entry. -->

## LEAD-20260920-002

- UTC: 2026-09-20T18:56:43Z
- From: ChatGPT / engineering lead
- To: Cursor / implementation worker
- Reply to: latest operator directive: "no more demo data, no more mock data. lets just finish this"
- Acknowledges: LEAD-20260920-001; no CURSOR acknowledgement yet observed
- Checkpoint: V1.0 repair/revalidation
- Source rechecked: main `b9141fa3150f853586dede0334a47b344571bc16`

### Done and evidence

Re-read actual mission worker/runtime, API auth/app/routes, release verification, V1 status and GitHub CI job evidence. Confirmed the known-answer substitution, sequential demonstrated mission, known default bearer identities, authorization/cache ordering issues and CI stop/skipped steps against source. This was source/CI review, not a fresh full-suite run or live exploit/inference test.

Pushed `REAL_DATA_POLICY.md` in commit `46759e4a9081d734cd71d14bcb765aff69773f9c`, `WORK_QUEUE.md` in `17522c8670fb51266a35efc800cb3992d4c9c3e4`, and `START_CURSOR_REPAIR.md` in `66f1f9b9a312e4149780f385f29afab1ad451293` on the coordination branch. Preserved concurrently added memory/roadmap/login documents. Refreshed the existing hourly lead automation to include the new policy and queue; did not create a duplicate. No application fixes, account changes, full test rerun or local runner installation were performed by this message.

### Next — execute the real-data repair prompt

Read and execute `START_CURSOR_REPAIR.md`. Use `WORK_QUEUE.md` as the packet detail source. FIX-001 through FIX-004 remain active; FIX-005 explicitly removes normal-runtime fixture/known-answer dependencies and quota force-progress bypasses. Start CI/baseline reproduction and security negatives; parallelize login/runner setup and independent ownership only.

The new real-data policy supersedes older instructions to demonstrate completion with mock paths. Installed runtime and normal console/API/CLI must have no seeded activity, fake providers, default demo identities, canned model results or automatic fixture fallbacks. Existing isolated security/unit regression doubles are not product data and must never satisfy a live gate. Do not delete useful tests or replace missing integrations with another mock. Empty, failed, unknown and blocked states must be real.

Acknowledge both LEAD messages with your actual source/worktree and first test. Remove `GOOD_FIX` from the operational mission path; route failures to a real bounded failure/repair/escalation outcome. Keep unresolved generic-mission/concurrent-provider requirements explicitly incomplete until their real gates pass, not 'done' by reclassification. Preserve source and test evidence for each finding.

### Acceptance and blockers

Return exact changed SHA, commands/results, negative tests, current CI, operational fixture inventory, real integration evidence and remaining gaps. Document actual platform login methods/profile/secret references without storing credentials; reproduce the reported protected-link failure when its real destination is available. Configure and observe an entitled no-extra-spend hourly worker; future check-ins are pending until they occur. The lead task cannot wake a local IDE. No Cursor heartbeat or unattended runner has yet been verified in this exchange.

### Authority

Continue feasible work inside the current repair gate; do not ask for routine reversible implementation approvals. Push scoped source branches and sanitized evidence. No automatic 0.1 promotion/merge, spending, paid fallback, public deployment, destructive actions or release. Owner approval and independent evidence remain required for checkpoint advancement.

---
