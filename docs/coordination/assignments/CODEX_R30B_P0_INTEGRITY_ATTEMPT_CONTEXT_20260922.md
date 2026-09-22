# Codex assignment — R30b-P0 envelope integrity + durable execution-attempt context

Date: 2026-09-22
Worker: Codex direct.
Expected base: accepted `6dbf8c43463cbdbd8c87561af2abcdde59969765`.
Contract: `docs/coordination/reviews/R30B_CONTRACT_DISPOSITION_20260922.md`.
Scope: shared prerequisite only; no HttpApiAdapter implementation and no network/live execution.

## A. Canonical payload integrity

Add one shared V1.7 gateway integrity check used by both execute and reconcile entry paths.

Canonical expected payload hash is the existing payload_hash over:
- integration id@version;
- operation;
- destination;
- normalized_payload.

Behavior:
- if payload_hash is empty, existing fill behavior may populate it;
- if non-empty and not equal to the recomputed canonical value, fail closed with a dedicated authorization/integrity error before adapter.validate, policy lookup, approval lookup, reserve or any I/O;
- cover changed normalized_payload and changed destination while stale non-empty payload_hash is retained.

Do not force effect_key to the default formula. Existing custom mission effect keys remain legal.

## B. Durable execution-attempt runtime context

Add `execution_attempt: int | None = None` to ActionEnvelope as runtime-only metadata.

It must not enter payload hashing, approval matching, effect binding, or persisted logical identity.

After `store.begin_execution` returns, copy its durable `attempt_count` into the envelope passed to adapter pre-observation, execute and post-observation.

When reconciling an unknown effect, pass the persisted effect `attempt_count` to adapter.reconcile through the same runtime field.

A consequential retry that returns through begin_execution must expose the incremented attempt count. Prove this with durable PostgreSQL, including reconstruction/repository reload rather than adapter instance memory.

## Required tests

- stale supplied payload_hash + changed payload fails before adapter/store mutation;
- stale supplied payload_hash + changed destination fails before adapter/store mutation;
- valid custom effect_key still works when payload hash is canonical;
- execution attempt 1 reaches adapter as 1;
- unknown reconciliation sees the persisted attempt;
- confirmed not_applied consequential retry reaches adapter as attempt 2;
- durable reload/reconstruction retains the correct attempt identity;
- existing R27/R28/R29/R28d compatibility remains green.

Run focused tests, affected actual-PostgreSQL checks, full offline and owned-PostgreSQL suites, Ruff on touched files and mypy. Report inherited unrelated lint separately.

No network, fixture process, HttpApiAdapter/config implementation, live/model/provider action, scheduler change, spend, merge, deployment, CP1 attempt or Fable dispatch.

Return exact-SHA READY_FOR_LEAD_REVIEW.
