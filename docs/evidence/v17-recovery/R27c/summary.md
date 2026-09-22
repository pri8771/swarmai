# R27c — repository-owned transactions, committed admission, atomic approval consumption

Packet: R27c · Artifact: ART-V17-APPROVAL-BINDING · Worker engine: fable (epoch fable-v17-20260922-01)
Base source SHA: `0130105e826f02d5e2a5809072712fc310b96274` · Tested source SHA: see `verify-receipt.json`.
**Review hold:** per EXECUTION_CONTROL `review_before`, R27e and R28a wait for the lead's review of this diff (`diff-tracked.patch` = tracked-file diff at the base; the new files are in the commit).

## Source changes (not re-verification)
- `src/swarm/tools/effects.py` (rewritten)
  - `DurableEffectRepository(session_factory)`; every public method is one `session_scope` transaction and commits before returning; no method takes or returns a live Session; `durable = True` / `InMemoryEffectStore.durable = False`.
  - `begin_execution(envelope, *, executor_id, fence_reader=None)` — one transaction: `SELECT … FOR UPDATE` effect row → optional fence reader called **inside** the transaction (`fence_changed_before_execute`) → approval consumption: `UPDATE approvals SET used_count=used_count+1 WHERE id=:a AND project_id=:p AND revoked_at IS NULL AND expires_at>now() AND used_count<max_effect_count RETURNING id` (zero rows → `approval_not_consumable`), `approval_consumed_at=now()` on the effect; a re-attempt with `approval_consumed_at` already set never consumes again but still requires not revoked/not expired → R27b compare-and-swap to `executing` (private `_cas_to_executing`) → commit. Only after it returns may the gateway call the adapter.
  - `finalize_with_receipt(...)` — one transaction: CAS `WHERE state IN ('executing','unknown')` (zero rows → `finalize_state_conflict`) + insert the immutable receipt (R27a rules).
  - Public `mark_executing`, `finalize`, `record_approval_use` deleted from both stores. In-memory store mirrors all semantics under a process lock.
- `src/swarm/tools/v17_gateway.py`: sequence is now validate → authorize → policy → fences → read-only `get()` (succeeded → original receipt; unknown → reconcile) → exact approval pre-check → `reserve` → `begin_execution` → observe/execute/observe → `finalize_with_receipt`. `record_approval_use` removed; `approval_not_consumable` maps to `ApprovalInvalidError("approval_expired_or_revoked_or_exhausted")`. Pre-check treats an approval already consumed **by this same effect** as not a second use (`ApprovalGrant.is_active(ignore_usage=...)`), otherwise a legitimate not-applied retry would be denied by the read-only check while the durable UPDATE (the authority) would admit it.
- `src/swarm/contracts/actions.py`: `is_active(ignore_usage=False)`.
- Tests: new `tests/integration/db/test_effect_transactions.py` (8 spec cases, 9 with parametrization) + `_effect_tx_child.py` (spawned second OS process pausing inside the adapter); R27a/R27b tests and the legacy durable test migrated to the factory API (same assertions).

## Semantics stated honestly (delivery contract §5)
Committed `begin_execution` is the **admission** point. Cancellation/fence changes before it deny admission. Cancellation after it may race an already-admitted remote action; that is reconciled, not retracted. Nothing here claims to retract in-flight external effects.

## Checks (this packet's own runs, real PostgreSQL `swarmai_v17_test`)
- `test_effect_transactions.py` + `test_effect_reservation_atomic.py` × 5 consecutive → 16 passed each (`pytest-run-1..5.txt`).
- Full suite → 416 passed, 2 skipped (pre-existing `tests/ui` skips). Ruff clean; mypy clean.
- Exit grep: `session.flush`/`self.session` inside `DurableEffectRepository` → 0 matches.

## Not claimed
No live checkpoint. R27d (approval immutability/revocation API), R27e (crash window), R28a (fail-closed outcomes) still open. Hosted CI blocked (EXT-ACTIONS-BILLING).
