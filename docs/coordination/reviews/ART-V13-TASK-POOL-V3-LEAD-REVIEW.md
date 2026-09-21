# ART-V13-TASK-POOL v3 — independent lead freeze review

Decision: **VERIFIED / FROZEN TASK-POOL CONTRACT**  
Lead review: LEAD-20260921-037  
Reviewed source: `cursor/v2-product-lane@534476393257794c4e8ebf8d65f44fd090ab28eb`  
Exact-tip CI: Actions `35625964121` — success  
Freeze: `g13-pool-freeze-v3`

## Scope reviewed

- `benchmarks/g13/pool_freeze_v3/**`
- `src/swarm/evals/g13_corpus_v3_*`
- `src/swarm/evals/g13_independence_v3.py`
- `src/swarm/evals/g13_prompt_v3.py`
- `src/swarm/evals/g13_sealed_reference_v3.py`
- `src/swarm/evals/g13_size_classifier_v3.py`
- `src/swarm/evals/task_pool_freeze_v3.py`
- `scripts/g13_freeze_task_pool_v3.py`
- `tests/evals/test_task_pool_freeze_v3.py`
- `docs/coordination/EVAL_131_QUALIFICATION_PROTOCOL.md`
- `docs/coordination/packets/V2B-001-R4.md`

## Acceptance findings

1. The frozen v3 corpus declares and verifies the required four product families (`coding`, `planning`, `reasoning`, `extraction`) across S/M/L/XL.
2. There are 240 held-out inputs total and the implementation requires exactly 15 distinct semantic archetypes in every required cell.
3. Independent source inspection of the authored objective catalogue shows materially different objectives rather than the retry-06 pattern of five recipes expanded by scenario substitutions/cumulative clauses. Examples span distinct algorithms/data structures, distinct operational planning problems, distinct reasoning problem classes, and distinct extraction document/field contracts.
4. The v3 independence checker fails closed on duplicate case/payload/prompt/template identity, duplicate semantic-archetype identity, scenario-substitution stems, clause-prefix/containment siblings, and cross-partition contamination. Per-cell archetype depth is mechanically enforced.
5. Direct tests cover scenario-substitution siblings, digest/template reseed collision, cumulative clause siblings, a 15-record/5-archetype failure, hidden-answer-key refusal, and fail-closed sealed-reference resolution.
6. Calibration and held-out records are separately identified; v3 reports 16 calibration records and 240 held-out records.
7. Worker-visible held-out records contain opaque hidden-reference handles only. Plaintext expected outputs, grader fixtures, rubrics and reference solutions are rejected by the prompt boundary.
8. The sealed reference bundle content digest is intentionally **not** fabricated or bound in this source slice. The manifest therefore keeps `counted_qualification_ready=false` and `w131b_started=false`.
9. The one-sided 90% Wilson z value remains `1.2815515655446004`; this packet does not alter the frozen threshold policy.
10. B reported executable verification: generator and verifier successful; Ruff clean; mypy clean over 145 source files; focused G13/coordination tests 17 passed; offline pytest excluding integration 295 passed. The exact source tip independently passed GitHub Actions run `35625964121`.

## Platform truth

The active B implementation session explicitly reported a **Linux** execution host while using the `HOST-WIN-DEV` coordination identity. This does not invalidate this platform-neutral evaluation-contract freeze because exact-tip CI independently passed and the gate is corpus/scorer/identity semantics, not Windows runtime behavior. It **does** mean this work must not be cited as Windows-specific install/runtime/multi-host evidence.

## External retry-07 disposition

`worker/swarmai-v13-task-pool-freeze-07@02cd0a2ea23342c331e83efd78b7682617dd16d3` is a real, one-commit, G13-scoped support branch from retry 06; Actions `35625433324` is green. It repairs the older v2 design with a semantic-group axis and 15 groups/cell, but Windows-B/local-B v3 remains the authoritative final implementation for the frozen task pool. No retry-07 code is auto-merged or substituted for v3.

## Freeze decision and remaining gate

`ART-V13-TASK-POOL` transitions **drafting -> verified** and `g13-pool-freeze-v3` is frozen for the next qualification tranche. Do not mutate v3 in place; any semantic change requires a new freeze/version and a new lead review.

This decision does **not** authorize W-131B counted qualification yet. Before the first counted observation, the lead must bind a real sealed-reference bundle content digest to the frozen reference IDs without exposing answers to workers. Reviewer-role calibration/freeze is separately required before reviewer held-out qualification.
