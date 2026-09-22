# ART-V17-TOOL-CONTRACT — R28d-2 independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED ENGINEERING SLICE ACCEPTED — R28d-2**
Reviewed exact source: `codex/swarm-r28d1-local-sandbox-20260922@6dbf8c43463cbdbd8c87561af2abcdde59969765`
Tree: `36aadba9c0fdb63c015784bee311df7976e68c4f`
Base: accepted R28d-1 `a2cfb3c1d5e326a1b15d7d23cfe3c91ea2e40bf4`
PR: #26
Live/checkpoint acceptance: **NOT YET — live_local evidence still required**

## Exact-SHA verdict

The candidate satisfies the released R28d-2 engineering wiring.

### Operational worker boundary

`RepoWorker` now requires explicit project id, action gateway and actor context. The production worker module no longer directly calls subprocess or writable file APIs for worker effects.

Worker writes go through `fs.write_text`; worker commands go through `proc.run`. The action request is bound to the authenticated actor/project plus mission/task/attempt context and the gateway's current fence/policy claims.

Each effect uses the released key shape:
`project:mission:task:attempt:operation:sequence`.
The sequence is reset per task attempt and incremented per effect, so intentional repeated writes are distinct effects rather than accidental replay.

### Worktree binding

The mission runtime constructs the local action boundary and supplies an action-gateway factory. Once an isolated worktree exists, the worker rebinds the local sandbox adapter to that exact worktree path before implement/verify effects. Worktree creation/removal remains trusted control-plane setup.

When `SWARM_DATABASE_URL` exists, the runtime uses `DurableEffectRepository`; otherwise the released idempotent/low local operations may use the in-memory effect store. The current static fence/policy seam matches the native R28d packet and does not claim the later lease integration.

### Sync boundary and evidence propagation

`ConsequentialToolGateway.execute_envelope_sync` runs the async gateway only when no event loop is active and fails with `sync_call_inside_running_loop` otherwise.

`WorkerResult.action_receipt_ids` collects effect receipts. Mission timeline task-finished entries, worker-result serialization and mission result serialization carry the receipt identifiers.

The new adverse tests cover required gateway/project construction, direct-effect AST absence, path/symlink and command denial, repeated-write distinct receipts, nonzero process exit handling and sync-loop rejection.

## Evidence considered

Native evidence at `codex/swarm-r28d2-evidence-20260922@42d4c11504ee3d29e022a136f89c168684c1622f` reports:
- focused mission/API: **69 passed**;
- full offline: **421 passed / 208 environment skips / 23.39s**;
- full owned disposable PostgreSQL: **616 passed / 13 existing environment skips / 27.68s**;
- owned PostgreSQL public-schema tables after teardown: **0**;
- Ruff clean;
- mypy clean on the changed mission/gateway surfaces.

This lead review independently inspected the exact two-commit diff, runtime construction, worker effect path, sync gateway, receipt propagation, adverse tests and native evidence. It did not rerun the 616-test suite.

No brokered live_local mission was part of this evidence, so this verdict is engineering-only.

## Scope boundary

This accepts R28d-2 engineering at exact SHA `6dbf8c43463cbdbd8c87561af2abcdde59969765`.

It does not yet complete parent R28d or grant a V1.7 live checkpoint. CP1 attempt3 remains unauthorized and unrelated.

## Next evidence step

The owner has separately granted bounded private incremental-$0 live testing using existing accounts/subscriptions and available owned machines, while keeping spending, public posting/messages, real job submissions, destructive actions and CAPTCHA/MFA bypass behind separate approval.

Therefore the native R28d `live_local` evidence step is now **RELEASED TO CODEX** from this exact accepted engineering SHA.

The run must be a single real brokered local mission on a throwaway target, incremental cost $0, with no public/external effect. It must prove non-empty `action_receipt_ids` and bind every mission file change to an `fs.write_text` receipt. It is labeled `live_local`, not CP1/ART-V14.

If no eligible $0 private route is available, stop with an exact blocker; do not spend or silently substitute a paid/public route.


## Remote CI addendum — 2026-09-22

Supplemental exact-source evidence: `codex/swarm-r28d2-evidence-20260922@0720b430081286e67cf8ad87af3d62bf394dd4d`.

GitHub Actions run `35722809270` contains three failed jobs (`offline`, `console`, `live-gated`) with no executable step list. The native evidence records runner_id 0 and GitHub's account billing/spending-limit annotation for each job.

Lead disposition:
- **do not claim hosted CI green**;
- **do not merge on the basis of this review**;
- the hosted result is an external CI-account infrastructure gate, not observed source-test failure;
- it does **not revoke or block the already-issued R28d-2 bounded engineering acceptance**, because that verdict is explicitly grounded in exact-source executed local/owned-PostgreSQL evidence and hosted GitHub Actions is not an authoritative acceptance prerequisite;
- the project is moving away from GitHub Actions as an authoritative runner. Future CI replacement must produce its own exact-SHA executable evidence before being counted as independent CI.

The R28d `live_local` assignment remains released under the owner's bounded private incremental-$0 testing grant. It remains a separate genuine evidence gate and must not be inferred from engineering tests or R730 host qualification.

R730 host qualification, if separately evidenced, establishes host readiness only. No service/model/mission execution on that host is inferred here.
