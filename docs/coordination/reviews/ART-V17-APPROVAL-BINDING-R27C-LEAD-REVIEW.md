# ART-V17-APPROVAL-BINDING — R27c lead review

Decision: **CHANGES REQUIRED**
Reviewed source: `cursor/v17-single-session@8dbe5d810d732f17806ac9611bec78383201ac82`
Evidence bundle tip: `9ff6859d3920106af9a55937c78937b785506ede`
Artifact lifecycle: unchanged (`drafting`)

## What is accepted as useful evidence

R27c materially improves the durable effect path: repository-owned short transactions, committed admission before adapter execution, atomic single-winner effect execution, atomic receipt finalization, replay of terminal success without re-running the adapter, and a real spawned second-process visibility test. The bound local receipt reports 16 focused tests x5, 416 passed / 2 skipped full suite, Ruff clean and mypy clean. Hosted Actions run `35673524977` is external non-evidence because all three jobs have zero steps and `runner_id=0`.

## Blocking finding 1 — operational gateway does not use the durable fence reader

`DurableEffectRepository.begin_execution()` supports a `fence_reader` and checks it while holding the effect row lock inside the admission transaction. However, the actual `ConsequentialToolGateway.execute_envelope()` path calls `begin_execution(..., fence_reader=None)`. Its earlier `_check_generations()` only compares the envelope to gateway-local integer fields before reservation/admission.

Therefore R27c does **not** yet prove that a durable lease/cancellation authority change occurring between the local pre-check and committed admission is fenced before the adapter runs. The direct repository test proves the optional callback works when manually supplied; it does not prove the operational gateway wires an authoritative durable fence reader.

Required repair:
- inject/wire the authoritative durable lease/cancellation fence reader into the operational consequential gateway admission path;
- keep the read inside the same transaction as approval consumption and execution CAS;
- add an integration regression that changes the durable generation after the initial gateway pre-check but before committed admission and proves: admission fails closed, adapter call count remains zero, and no approval use is consumed.

## Blocking finding 2 — replacing an approval on a previously-attempted effect can bypass the new grant's use count

For an existing effect, `reserve()` does not update the persisted `approval_id`. `_consume_approval()` increments the supplied approval only when `row.approval_consumed_at is None`. If the effect already consumed approval A and a retry supplies a distinct valid approval B, the `approval_consumed_at` branch only checks B is still valid; it does not increment B and does not rebind the effect to B.

That is inconsistent with the contract's maximum-effect-count authority and can leave a newly supplied broad approval reusable after it already authorized a new execution attempt.

Required repair:
- make approval consumption attributable per execution attempt, or otherwise atomically rebind/record the approval used for the newly admitted retry;
- every distinct grant that authorizes a new execution attempt must consume exactly one permitted effect, while a retry under the *same already-consumed grant for the same effect* must not double-consume;
- add an integration regression: attempt with approval A fails with provable `not_applied`; retry same effect with fresh approval B (`max_effect_count=1`) succeeds/admitted and B becomes used exactly once; B must then be unable to authorize a second different effect.

## Preserve

Do not regress the current good properties: one-shot two-effect race has one winner, same-effect/same-grant retry does not double-consume, revoked/expired retry is denied, denied requests leave no durable effect row, successful replay returns the original immutable receipt, unknown outcomes reconcile rather than blind-retry, and finalization stays atomic with receipt insertion.

## Verification required for R27c-R1

At the repaired source SHA:
1. focused effect-transaction/reservation tests at least x5;
2. new durable-fence TOCTOU regression;
3. new replacement-approval consumption regression;
4. full offline pytest;
5. Ruff;
6. mypy.

Hosted CI remains non-evidence until GitHub Actions actually allocates a runner and executes steps.

## Scheduling decision

`R27d` may continue because it is approval-immutability work and was explicitly outside the R27c hold. `R27e` and `R28a` remain held. After R27d, use dependency-independent packets while `R27c-R1` is prepared/repaired; do not treat R27c or `ART-V17-APPROVAL-BINDING` as accepted.
