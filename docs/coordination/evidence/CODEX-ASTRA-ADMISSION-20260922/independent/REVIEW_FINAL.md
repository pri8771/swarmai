# Bounded independent SwarmAI admission-atomicity review — 2026-09-22

Engineering recommendation: **RECOMMEND_ACCEPT** for exact staged tree `4fd0b56f909c8026e4893540d587d93d5180c73b`, contingent on settled root-owned checks and actual lead disposition. No blocking production finding remains in the reviewed three-file change. This is not formal acceptance, a new live grant, or CP1 attempt3 authorization.

Source: `/private/tmp/swarm-r28d3-repair-20260922`, base `86f8e0c90e399c683d68ba9628ef48af4723f33f`. Native bounded assignment: `origin/coordination/swarm-control:docs/coordination/assignments/CODEX_R28D_ADMISSION_ATOMICITY_20260922.md` (released at `69d06a6`). Exact staged tree `4fd0b56f909c8026e4893540d587d93d5180c73b` was read back after source review. Staged whitespace check is clean and there are no unstaged changes. Final reviewed content fingerprints are in adjacent `final_reviewed_file_hashes.json`.

## Source findings

- `InMemoryEffectStore.begin_execution`: optional provider guard is the first context, before the store RLock. Binding/fence validation, approval consumption and transition to executing occur while both locks are held. Return copies the admitted row; contexts then unwind before caller resumes.
- `DurableEffectRepository.begin_execution`: provider guard precedes `session_scope` and all DB acquisition. Python unwinds contexts in reverse order, so `session_scope` commit (or exception rollback and close) completes before the provider guard releases. Approval consumption and CAS remain inside this transaction.
- `RevocableFenceProvider`: admission guard and `cancel()` use the same RLock; the fence reader can reenter through `current()` without deadlock. Cancellation cannot cross the local admission transaction after admission wins the lock, and stale cancellation generations reject before approval consumption if cancellation wins first.
- `ConsequentialToolGateway`: passes the provider-owned guard to the existing sole admission call. Adapter pre-observation, execute, post-observation and receipt handling occur after `begin_execution` returns, outside the guard. Already-admitted effect accounting remains unchanged.
- `StaticFenceProvider` and `LeaseFenceProvider` provide no-op guards. Durable lease read/authority checks and existing mission -> lease -> attempt ordering are unchanged. No second unlocked generation check was introduced.

## Tests and evidence inspected

- New race regression covers both serialized winners against memory and owned PostgreSQL stores. Admission winner pauses inside the guarded fence read, verifies cancellation cannot return, then verifies cancellation finishes before paused adapter pre-observation and sees admitted state/one approval use. Cancellation winner pauses before admission, finishes cancellation, then asserts no file/receipt/approval use.
- Reviewer found the first test draft patched nonexistent `adapter.observe`; integration owner corrected both accesses to `observe_pre_state`. Corrected code was reread.
- Reviewer independently ran only memory variants with `SWARM_DATABASE_URL` unset: **2 passed, 2 deselected, 0.31 seconds**. This used only a temporary local file adapter and memory effect store. No PostgreSQL or external service was accessed by reviewer.
- Runtime async bridge schema fixture now follows the existing create/drop pattern only when a test PostgreSQL URL is explicitly supplied. There is no production missing-schema fallback. Future-authority test double delegates the new guard seam.
- Root owns PostgreSQL, full offline, Ruff and mypy verification. Root reports preserving initial hook error and demonstrating the corrected regression fails against exact old source; attach root's settled evidence separately.

Reviewer made no source/test edits, did not duplicate the full suite, and did not make live model/provider/mailbox/scheduler/public actions. All source/evidence remains Swarm-specific; the completed Jobs final review remains unchanged.

Final test-only delta: bounded effect_key/idempotency_key is set after normalization and before approval, matching RepoWorker task/sequence key construction. This avoids the long pytest temporary-path default key exceeding inherited VARCHAR(192); no production/schema workaround was introduced. Root owns rerunning PostgreSQL and full checks after this fixture correction. Production fingerprints are unchanged from the initial review.
