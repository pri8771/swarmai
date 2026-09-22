# R28d successor cancellation/admission review — exact-source rework

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **REWORK_FOUND**
Reviewed source: `codex/swarm-r28d3-async-gateway-20260922@86f8e0c90e399c683d68ba9628ef48af4723f33f`
Tree: `b42a7a11f298cdefe89319bfaa91f1ce91aa55d4`
Base: accepted R28d-2 `6dbf8c43463cbdbd8c87561af2abcdde59969765`
PR: #27
Live/run acceptance: **NOT GRANTED**

## Blocking finding

The independent race is confirmed by source inspection and native reproduction evidence at `codex/portfolio-review-20260922@c714825`.

At this candidate, `RevocableFenceProvider.reader()` obtains a cancellation-generation snapshot under its lock and releases that lock before `store.begin_execution()` completes the reserved -> executing admission transition. Therefore:

1. effect is reserved with cancellation generation 0;
2. admission reader can observe 0;
3. runtime cancellation can then complete and advance the local fence to generation 1;
4. the already-returned reader snapshot still satisfies the reserved row;
5. `begin_execution` admits the stale effect;
6. the adapter can create a late file and a succeeded receipt before the worker observes cancellation.

This is a pre-admission revocation race. It is distinct from an effect already admitted before cancellation; this verdict does not require revoking or rolling back already-admitted effects.

The existing test that cancels immediately before gateway admission does not cover the reproduced interleaving because it bumps the fence before the admission reader captures its value.

## Verification status

The candidate is not acceptance-ready:
- focused offline: 11 passed;
- full owned PostgreSQL: 622 passed, **2 failed**, 13 skipped, cleanup zero;
- both new runtime failures are missing test-schema setup under `SWARM_DATABASE_URL`;
- mypy174 passed;
- full Ruff still reports inherited `src/swarm/api/store.py` I001 and is not called clean.

The two schema failures are test-fixture defects, not evidence against the reproduced production race; both must be corrected in the same bounded repair so the exact-source matrix is executable.

## Required repair contract

Release only a local cancellation/admission atomicity repair plus the missing-schema test fixture correction.

### Atomicity

Add a shared **admission guard** that serializes `RevocableFenceProvider.cancel()` with the entire local `begin_execution` admission critical section:

- the guard is acquired before the admission fence snapshot used by `begin_execution`;
- it remains held through fence comparison, approval consumption where applicable, reserved -> executing CAS/state transition, and transaction/critical-section return;
- it is released **before** pre-observation or any adapter call;
- cancellation may not return while a not-yet-admitted local effect is inside this guarded admission section;
- after cancellation returns, an effect that had not completed admission must fail closed on the stale cancellation generation;
- an effect whose admission completed before cancellation may drain and be accounted for under the existing already-admitted semantics.

Preferred bounded seam: extend effect-store `begin_execution` with an optional admission-guard/context-manager callback entered before store/transaction locks; the gateway supplies the provider guard. `RevocableFenceProvider` owns the real lock-backed guard. Static and durable lease providers use a no-op guard. This avoids a gateway-only fence->store wrapper that can create reverse lock ordering with direct store callers.

Do not add a second unlocked cancellation check as the fix.

### Durable lease preservation

Do not change `LeaseFenceProvider` authority or the existing durable admission reader semantics/lock ordering. The new local guard must be a no-op for durable lease fencing. No new scheduler/lease authority is introduced.

### Required race proof

Add a deterministic barrier regression reproducing exactly:
- reader/snapshot captured at generation 0;
- cancellation starts and must remain blocked;
- admission completes or is prevented according to the serialized winner;
- if cancellation wins before admission completion, no adapter call/file/receipt and approval remains unused;
- if admission wins first, cancellation waits for admission return and the existing already-admitted drain/accounting behavior applies.

Also retain the simpler stale-snapshot negative.

### Test fixture

The two new PostgreSQL runtime tests must explicitly use the repository's owned disposable schema setup/teardown fixture rather than assuming inherited `SWARM_DATABASE_URL` already has tables. Do not change production code to make missing test schema pass.

## Holds

No successor live/model/provider run is released. The immutable failed `e9178259...` attempt consumed its one-run grant. No CP1 attempt3, scheduler change, spend, main merge, deployment, public action or Fable dispatch is authorized.
