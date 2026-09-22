# R27a — durable immutable action receipts + effect bookkeeping columns

Packet: R27a · Artifact: ART-V17-APPROVAL-BINDING · Worker engine: fable (epoch fable-v17-20260922-01)
Base source SHA (before this packet): `ab958d7a4b4d6198b143e7e79ecf69ff367cb10e` · Tested source SHA: recorded in `verify-receipt.json` after commit.

## Source changes (not re-verification)
- `migrations/versions/a17effect004b0001_art_v17_action_receipts.py` — new revision after `a17effect004a0001`: four bookkeeping columns on `action_effects` (`state_reason`, `attempt_count`, `executor_id`, `approval_consumed_at`) and new `action_receipts` table with `UNIQUE(effect_id, attempt_number)` `uq_action_receipt_effect_attempt`, FK to `action_effects`, index `(project_id, effect_key)`. Downgrade drops table then columns.
- `src/swarm/db/models.py` — `ActionReceiptRow`; four columns on `ActionEffectRow`.
- `src/swarm/tools/effects.py` — receipts are insert-only in both stores (`store_receipt`, `get_receipt`, `list_receipts`, `terminal_receipt`); `DurableEffectRepository` no longer holds a receipts dict; `attempt_number` computed under `SELECT … FOR UPDATE` on the effect row; `durable` class flag.
- `src/swarm/tools/v17_gateway.py` — replay of a succeeded effect returns the original receipt via `terminal_receipt` (fail-closed `succeeded_effect_missing_receipt` if absent); `_reconcile_unknown` reads prior receipts from the store; `_receipt_from_effect` deleted.
- `src/swarm/contracts/actions.py` — `ActionReceiptV17.attempt_number`.
- `tests/integration/db/test_action_receipts_durable.py` — the six spec negatives.

## Checks (this packet's own run, real PostgreSQL `swarmai_v17_test`)
- `uv run pytest tests/integration/db/test_action_receipts_durable.py -v` → 6 passed (`pytest-output.txt`).
- `uv run alembic heads` → single head `a17effect004b0001` (`alembic-heads.txt`); test also drives upgrade→downgrade→upgrade.
- Full suite `uv run pytest -q` with `SWARM_DATABASE_URL` set → 400 passed, 2 skipped (skips: pre-existing `tests/ui` node_modules gate).
- `uv run ruff check .` clean; `uv run mypy src/swarm` clean (169 files).
- Exit grep: `self.receipts` appears only inside `InMemoryEffectStore`.

## Not claimed
No live checkpoint. Reserve/execute atomicity (R27b), transaction ownership and approval consumption (R27c), approval immutability (R27d) and the crash window (R27e) are still open. Hosted CI is account-blocked (EXT-ACTIONS-BILLING); hosted CI status for this SHA is "blocked", not green.

## Side finding (not fixed here)
Running the full suite mutates tracked files (`tests/release/test_v1.py` re-freezes `schemas/v1/*`; a fix-004 runner test rewrites `docs/evidence/fix-004/*`). Reverted with `git checkout --` before committing; proposed as a small hygiene packet.
