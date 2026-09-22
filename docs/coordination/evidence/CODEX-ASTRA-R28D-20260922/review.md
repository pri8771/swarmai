# Exact R28d-3/-4 mechanical review: REWORK_FOUND

Reviewed source: 86f8e0c90e399c683d68ba9628ef48af4723f33f; tree b42a7a11f298cdefe89319bfaa91f1ce91aa55d4. Clean before/after. No source edit, model invocation, live mission, external effect or formal acceptance.

## Concrete production finding (P1)

`RevocableFenceProvider.reader` takes and releases `_lock` while returning a generation snapshot (src/swarm/tools/fences.py:135-146). `cancel` uses that same lock only to bump memory state (118-125). Neither operation synchronizes with the subsequent effect-state CAS/transaction commit in `begin_execution` (memory effects.py:237-272; durable effects.py:546-571). Therefore cancellation can finish while an effect is still reserved, and admission can subsequently use the stale snapshot to execute the effect.

The standalone deterministic probe in fence-admission-probe.py adds a pause after the actual fence reader returned its snapshot. A separate thread invokes the actual cancellation method and confirms the effect remains reserved before releasing the pause. On unchanged exact source: snapshot generation0; current generation1; cancel returned while effect reserved; late local file exists; effect succeeded with receipt; worker only notices cancellation after receipt. This is an offline concurrency reproduction, not product-path live proof. It does not pretend to revoke an already-admitted operation: cancellation completed before admission CAS.

Recommendation: do not recommend acceptance of this exact cancellation repair until the admission race is addressed and reviewed. Smallest boundary candidate is a local revocable-provider admission guard shared by cancellation and the gateway's `store.begin_execution` call, held through its return/commit only, released before adapter work. The guard must be reentrant or avoid nested locking because reader runs inside it. Ordinary fence providers can retain current semantics through a no-op guard; durable/lease authority remains with its existing DB-owning provider. Cancellation acquiring the guard before admission must cause stale-envelope denial; admission completing first may execute but must remain drained and receipt-accounted. Do not merely add another unlocked pre-execute check. A database-owned revocation row could also serialize the transition but would expand scope; ask the lead before that expansion. Root must independently reproduce and decide scope.

## Checks

- Focused offline runtime/no-auto-promote: 11 passed.
- Full real PostgreSQL: 622 passed, 2 failed, 13 skipped.
- Failures: new runtime bridge direct-gateway test sees missing action_effects; already-admitted-effect cancellation test then times out for same absent schema. These unmarked runtime tests inherit SWARM_DATABASE_URL and construct DurableEffectRepository but do not prepare tables. Existing earlier integration tests drop schema in teardown. Test environment cause is distinct from the production race.
- Fixture proposal only in test-fixture-proposal.patch: create/drop Base metadata when PostgreSQL is explicitly supplied; keep ordinary offline behavior when absent. This follows tests/product/test_product.py's durable_schema pattern, retains actual PostgreSQL dialect, makes no monkeypatch bypass, and must only run on the approved disposable DB. Proposal not applied or tested.
- Full mypy: passed, 174 source files.
- Full Ruff: inherited I001 src/swarm/api/store.py; no source diff for that file versus accepted base6dbf8c4.
- Diff check passed; source remains clean.
- All commands/check exits recorded in verify.py and checks.json. Explicit PYTHONPATH points to exact candidate src; uv --no-sync prevents environment rebinding.
- Existing owned Unix-socket PostgreSQL port56421 was used; no server start or stop. Unique DB created for this run; public tables after suite0; DB removed and remaining count0. No other DB touched. postgres.json records ownership and options.
- 13 skips listed individually in skipped-tests.json: 11 disabled live fixture cases plus2 unavailable console-node cases. These are not passes.

Stop condition reached at first concrete production defect. No deeper defect hunt or source change performed.
