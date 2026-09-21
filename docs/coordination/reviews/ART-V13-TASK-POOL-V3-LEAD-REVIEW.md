# ART-V13-TASK-POOL v3 — independent lead review

Decision: **REVIEWABLE / FREEZE WITHHELD**  
Lead review: LEAD-20260921-037  
Reviewed source: `cursor/v2-product-lane@534476393257794c4e8ebf8d65f44fd090ab28eb`  
Exact-tip CI: Actions `35625964121` — success  
Candidate identity: `g13-pool-freeze-v3`

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
- frozen EVAL-131 protocol and `V2B-001-R4` packet.

## Semantic findings

The v3 candidate is materially stronger than retry06. It contains 240 held-out inputs over all 16 required family x size cells and mechanically requires 15 distinct semantic archetypes per cell. Source inspection found materially different objectives rather than the rejected pattern of five recipes expanded by scenario substitution, numeric reseeding or cumulative clauses. The independence checker fails closed on duplicate case/payload/prompt/template identity, duplicate semantic-archetype identity, scenario-substitution stems, clause-prefix/containment siblings and cross-partition contamination.

Direct tests cover scenario siblings, digest/template reseed collision, cumulative clauses, a 15-record/5-archetype failure, hidden-answer-key refusal and fail-closed sealed-reference resolution. Calibration and held-out identities are separate. Worker-visible held-out records expose opaque reference handles only. The sealed reference content digest is intentionally not fabricated, so `counted_qualification_ready=false` and `w131b_started=false` remain correct. The frozen one-sided 90% Wilson policy is unchanged.

B reported generator/verifier success, Ruff clean, mypy clean over 145 source files, 17 focused tests passed and 295 offline tests passed. Exact-tip GitHub Actions `35625964121` independently succeeded.

## Why freeze is withheld

`V2B-001-R4` and the fixed execution topology make **actual HOST-WIN-DEV** the final implementation/test owner of this gate. The implementation session that produced the above executable report explicitly identified its host OS as Linux while using the HOST-WIN-DEV coordination identity. Green GitHub CI and the strong source review do not substitute for the required final executable Windows-lane evidence.

Therefore `ART-V13-TASK-POOL` is **reviewable**, not yet verified/frozen. Packet `V2B-001-R5` now defines the bounded actual-Windows verification gate. If the real Windows run exposes no portability defect, the v3 bytes should remain unchanged and the lead can freeze the existing candidate. Any semantic v3 change requires a new version and new independent review.

## External retry07

`worker/swarmai-v13-task-pool-freeze-07@02cd0a2ea23342c331e83efd78b7682617dd16d3` is a real one-commit G13 support branch with Actions `35625433324` green. It remains support/reference evidence only and is not auto-merged or substituted for local-B v3.

## Remaining gates

No W-131B counted qualification is authorized. First obtain actual HOST-WIN-DEV executable verification and independent lead freeze. Then bind a real lead-controlled sealed-reference bundle content digest without exposing answers. Reviewer calibration may be developed separately, but reviewer held-out qualification also remains gated by its own benchmark/scorer freeze.
