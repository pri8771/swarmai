# R27b — atomic reserve, compare-and-swap execute, binding-mismatch rejection

Packet: R27b · Artifact: ART-V17-APPROVAL-BINDING · Worker engine: fable (epoch fable-v17-20260922-01)
Base source SHA: `939ab596c578b083b11aa465ae6ae894d81c2905` · Tested source SHA: see `verify-receipt.json`.

## Source changes (not re-verification)
- `src/swarm/tools/effects.py`
  - `DurableEffectRepository.reserve`: `INSERT … ON CONFLICT (uq_action_effect_project_key) DO NOTHING RETURNING effect_id`; then select and compare stored `integration_id/integration_version/operation/destination_digest/payload_hash` with the envelope (`effect_key_binding_mismatch`); returns the row plus `created` (true only for the inserting caller).
  - `DurableEffectRepository.mark_executing(*, project_id, effect_key, executor_id)`: one `UPDATE … WHERE state='reserved' OR (state='failed' AND state_reason='not_applied') RETURNING`; zero rows → exactly one of `effect_not_found`, `effect_already_succeeded`, `effect_unknown_requires_reconcile`, `effect_already_executing`, `effect_terminal:<state>`. Sets `executor_id`, increments `attempt_count`, clears `state_reason`.
  - `InMemoryEffectStore` mirrors both rules (same error strings; guarded by a process lock so unit tests see the same single-winner semantics).
  - Shared helpers `_executable`, `_not_executable`, `_binding_of`, `_check_binding`.
- `src/swarm/tools/v17_gateway.py`: passes `executor_id=new_id("exe_")`. No other gateway change.
- `tests/integration/db/test_effect_reservation_atomic.py`: the seven spec negatives; 8 real threads, one Session each, commit after every repository call, released by a `threading.Barrier`.
- `scripts/coordination/hb.sh`: manual heartbeat helper for the Fable engine (coordination tooling, not product code).

Consequence already in force: a `failed` effect without `state_reason='not_applied'` is terminal (closes E6 now; R28a will be the only writer of `not_applied`).

## Checks (this packet's own runs, real PostgreSQL `swarmai_v17_test`)
- `uv run pytest tests/integration/db/test_effect_reservation_atomic.py -v` × 5 consecutive → 7 passed each (`pytest-run-1..5.txt`).
- Full suite `uv run pytest -q` → 407 passed, 2 skipped (pre-existing `tests/ui` skips).
- `uv run ruff check .` clean; `uv run mypy src/swarm` clean.

## Not claimed
No live checkpoint. Transaction ownership still belongs to the caller until R27c; approval consumption is still non-atomic until R27c. Hosted CI: blocked (EXT-ACTIONS-BILLING).
