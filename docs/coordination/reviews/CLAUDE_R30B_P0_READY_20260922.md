# R30b-P0 envelope integrity + durable execution-attempt context — READY_FOR_LEAD_REVIEW

Date: 2026-09-22. Worker: Claude, resuming Codex's paused P0 WIP on the owner's explicit resume.
Assignment: `coordination/swarm-control@9c912f4`, `docs/coordination/assignments/CODEX_R30B_P0_INTEGRITY_ATTEMPT_CONTEXT_20260922.md`.
Exact source: `codex/swarm-r30b-prerequisite-20260922@11bd4b5276458b2b7adc11528f117e919524f035`, tree `33990992110084694910819d765361a50afa2762`. Base: accepted `6dbf8c43463cbdbd8c87561af2abcdde59969765`.
Draft PR: https://github.com/pri8771/swarmai/pull/28. Self-acceptance: none. Live/version acceptance: not claimed.

## Resume integrity

The four WIP files matched the paused recovery SHA256SUMS (`adad9dd`, `CODEX-R30B-P0-PAUSED-20260922`) byte-for-byte before any action. Codex's worktree was continued in place and the snapshot was not re-applied.

## Change (5 files)

- `contracts/actions.py`: adds `ActionEnvelope.canonical_payload_hash()`, which hashes integration@version, operation, destination and normalized_payload. `ensure_hashes` reuses it. Adds runtime-only `execution_attempt: int | None = Field(default=None, exclude=True)`.
- `tools/v17_gateway.py`: adds `PayloadIntegrityError(ToolAuthorizationError)`. `_require_payload_integrity` runs in both `execute_envelope` and `reconcile`, immediately after `_authorize_context` and before registry resolve, validate, policy, approval, store or I/O. An empty hash still fills. After `begin_execution`, the envelope passed to pre/execute/post is `model_copy`'d with the durable `effect["attempt_count"]`. `_reconcile_unknown` does the same with the persisted count. A caller-supplied value is never forwarded. Custom `effect_key` stays legal.
- New `tests/tools/test_gateway_envelope_integrity.py` covers a stale hash plus changed payload/destination × execute/reconcile, denied before validate/policy/store/approval. It also covers a custom key with caller attempt 999 that reaches the adapter as the durable 1, with exclusion from dumps and reload.
- New `tests/integration/db/test_execution_attempt_context.py` (owned PG): attempt 1 comes back unknown. Then the repository, gateway, adapter and envelope are reconstructed from JSON. Reconcile sees the persisted 1, the not_applied retry reaches the adapter as 2, and the row keeps attempt_count 2 with the same payload_hash/effect_key/idempotency identity. The approval is used once.
- **Compatibility change (disclosed)** in `tests/tools/test_v17_gateway_classification_fences.py::test_undeclared_operation_denied_before_adapter_action`. The test mutates `operation` after `normalize()` hashed it, so on P0 it first hits `payload_hash_mismatch`, which the spec requires because operation is part of the canonical hash. The test now asserts that stale-digest denial first, then recomputes the canonical hash and asserts the original `operation_not_declared` denial. `call_count == 0` is kept. No production change was made for this.

## Evidence (native: `docs/coordination/evidence/CLAUDE-R30B-P0-20260922/`)

| Check | Result |
|---|---|
| Red on exact base 6dbf8c4 (new tests copied onto `git archive`) | **7 failed**, each for the intended reason: durable attempt `None`≠1, missing integrity denial ×4, caller 999 forwarded ×2. PG cleanup 0 |
| First-ever durable PG run of the attempt test (plus integrity and effect_transactions) | 22 passed, cleanup 0 |
| Intermediate full run (kept in `intermediate-1-fixture-compat-red/`) | full-offline 1 failed/426; full-PG 1 failed/622. That one test is the compatibility case above. Focused exit 4 was a harness error: it named `test_local_admission_guard.py`, which exists only on fb58a751 |
| Settled focused offline | 19 passed / 4 PG skips |
| Settled full offline | **427 passed / 209 prerequisite skips** |
| Settled focused owned PG | 38 passed |
| Settled full owned PG (`/tmp/swarm-pgcheck.QxqRvZ`:56421, verified pchordia/data dir/no TCP) | **623 passed / 13 live-UI skips / 31.45s**; public tables 0; cleanup_remaining 0 |
| mypy `src/swarm` | 174 files clean |
| Ruff check + format on 5 touched files | clean |
| Ruff full repo | inherited `src/swarm/api/store.py` I001 only (unchanged file) |
| Blob hashes before and after the suites | identical; the commit contains exactly those blobs |

Interpreter: accepted r28d3 venv, with `PYTHONPATH` pinned to this worktree. Import provenance was checked (`swarm.__file__` is inside the P0 worktree). `SWARM_ALLOW_PAID=false` and `SWARM_LIVE_LOCAL=0`. No network, fixture process, HttpApiAdapter, live/model/provider action, scheduler, spend, merge or CP1 attempt.

## Independent review

Three independent read-only lenses (spec conformance, integrity bypass, compatibility), each finding adversarially re-verified. Result: **no P0 defect**. All 7 raised findings were refuted as P0 defects (the mechanics are real but pre-existing or outside the A/B scope). The compat lens reported 0 findings: `ensure_hashes` produces identical digests, no src caller mutates a hashed field after hashing, and both stores return int `attempt_count`.

Out-of-scope follow-ups for the lead to consider (not implemented, not released):
1. `make_approval` (v17_gateway.py ~109) calls `ensure_hashes` but not `_require_payload_integrity`, so a grant can be minted from a supplied stale digest. Execute would still need a matching canonical hash, but the approver could have seen a different payload than the digest binds. A one-line addition is recommended as its own packet.
2. The integrity check is point-in-time. `model_copy` is shallow, so an adapter that mutates `normalized_payload` during its own await is not re-checked (a pre-existing trust assumption about adapters).
3. A JSON-reconstructed envelope whose payload holds non-JSON-native values (e.g. datetime) hashes differently and fails reconcile closed. This is fail-closed as required, but such effects need operator disposition.
4. `adapter.validate` still sees the caller envelope before the durable override. validate is not in the spec's pre/execute/post set.

## Hosted CI (new: repos public)

Swarm Actions now execute. On the accepted fb58a751, rerun `35759392432` gave console ✅ and live-gated ✅. Offline ❌ stops at step 5, `ruff check .`, on the same inherited `api/store.py` I001, so CI mypy/pytest never run. A one-line import-sort fix in an unchanged file is **not** included; the review said no unrelated cleanup is authorized. Requested: a lead or owner release of a single-file lint packet so hosted CI can reach pytest.

## Composition note

P0 is based on 6dbf8c4 as assigned and does not contain the accepted fb58a751. Independent offline composition check (reviewer scratch copy): P0 plus the `6dbf8c4..fb58a751` diff gives **437 passed / 211 skipped / 0 failed**. No textual conflict was observed. The composition order and PG composition run need a lead release; no composed candidate was created.

Return: **READY_FOR_LEAD_REVIEW** at the exact SHA above. R30b product HttpApiAdapter and live execution remain held.
