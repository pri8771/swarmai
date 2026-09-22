# Codex assignment — R28d local cancellation/admission atomicity repair

Date: 2026-09-22
Worker: Codex direct isolated repair.
Expected base: PR27 exact `86f8e0c90e399c683d68ba9628ef48af4723f33f`.
Lead rework: `docs/coordination/reviews/ASTRA_R28D_SUCCESSOR_REWORK_LEAD_20260922.md`.

Implement only the confirmed local cancellation/admission race repair plus the two missing-schema test-fixture corrections.

## Repair

1. Introduce an admission-guard seam owned by the fence provider.
2. Effect-store `begin_execution` must enter the optional guard **before** acquiring its store/transaction locks and retain it through the committed admission return.
3. `RevocableFenceProvider` uses its local cancellation lock for that guard; `cancel()` uses the same lock.
4. The fence reader used inside admission must observe state while that guard is held.
5. Release the guard before adapter pre-observation/execute.
6. StaticFenceProvider and LeaseFenceProvider use a no-op guard. Do not alter durable lease authority, DB lease reader behavior, or its lock ordering.
7. Do not fix this with a second unlocked generation check.

Required deterministic race test: pause after the local admission guard/read has been acquired but before admission returns; start cancellation and prove it cannot return through that window. Exercise both serialized winners. Cancellation-before-admission must yield zero adapter/file/receipt and no approval use; admission-before-cancellation may drain under existing already-admitted accounting.

Correct the two new runtime PostgreSQL tests to create/teardown the owned schema using the existing test fixture pattern. No production fallback for missing schema.

Run focused race/runtime tests, full owned PostgreSQL, full offline, Ruff and mypy. Report inherited unrelated lint separately if still present; do not call it green.

No live/model/provider run, scheduler change, spend, merge, deploy, public action, CP1 attempt3 or Fable handoff. Return exact-SHA READY_FOR_LEAD_REVIEW.
