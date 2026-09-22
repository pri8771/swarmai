# R27d — approval integrity: insert-only, monotonic revocation, legacy rows non-operational

Packet: R27d · Artifact: ART-V17-APPROVAL-BINDING · Worker engine: fable (epoch fable-v17-20260922-01)
Base source SHA: `9ff6859d3920106af9a55937c78937b785506ede` · Tested source SHA: see `verify-receipt.json`.

## Source changes (not re-verification)
- `src/swarm/tools/effects.py`
  - `put_approval` is insert-only in both stores: existing id → `EffectConflictError("approval_already_exists")` (unique-key violation mapped); `used_count` forced to 0 on insert; a grant object carrying `revoked_at` → `EffectStoreError("approval_insert_revoked")`. `session.merge` removed.
  - New `revoke_approval(*, project_id, approval_id, revoked_by, reason) -> bool`: `UPDATE approvals SET revoked_at=now() WHERE id=:a AND project_id=:p AND revoked_at IS NULL`; who/why stored under `constraints.revocation`. Nothing clears `revoked_at`.
  - `get_approval(approval_id, *, project_id)` filters by project and returns `None` when any of `project_id/integration_id/integration_version/operation/policy_version` is NULL. All `or "<default>"` fallbacks removed (`_operational`, strict `_grant_from_row`).
- `src/swarm/tools/v17_gateway.py`: project-filtered approval lookup (other-project or legacy rows → `unknown_approval`, no existence signal); `revoke_approval` convenience; `make_approval(revoked=True)` removed.
- Tests: new `tests/integration/db/test_approval_integrity.py` (six spec negatives); `tests/tools/test_v17_gateway_negatives.py` revokes through `revoke_approval`; R27c one-shot test constructs its key-less grant directly instead of re-putting (re-put is now rejected, which is the point).

## Checks (this packet's own runs, real PostgreSQL `swarmai_v17_test`)
- `uv run pytest tests/integration/db/test_approval_integrity.py -v` → 6 passed (`pytest-output.txt`).
- Full suite → 422 passed, 2 skipped (pre-existing `tests/ui` skips). Ruff clean; mypy clean.
- Exit grep: `session.merge` / `or "v17-policy-1"` in `effects.py` → no matches.

## Not claimed
No approvals API/CLI (shared wiring, later). No live checkpoint. Hosted CI blocked (EXT-ACTIONS-BILLING).
