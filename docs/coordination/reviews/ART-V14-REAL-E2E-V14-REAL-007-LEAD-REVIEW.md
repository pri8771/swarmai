# ART-V14-REAL-E2E — v14-real-007 independent lead review

Date: 2026-09-21
Reviewer: ChatGPT engineering lead
Decision: **CHANGES REQUIRED**
Artifact lifecycle decision: **no transition; remain `drafting`**

## Candidate reviewed

- Run: `v14-real-007`
- Mission: `609fc23e9cb04117a032eb3d50a0104b`
- Evidence commit: `46461a39b4903b1bdc0735fb526d0cd38c6cd8f5`
- Freeze lineage: `e2fca4c619977b021696189ff337bdf0378662a3` -> `dd3ec870efe41a1618485823bc70e7f5d9e9a1d1`
- Current single-session branch descendant at review start: `46f7a24792640da7686560bed6e3bead71a392cd`

## What is valid evidence

This run is useful operational evidence and must be preserved:

- a real persisted mission ID exists;
- local `qwen2.5-coder:14b` inference was brokered at reported spend `$0`;
- repository content was inspected and a material diff was produced in an isolated worktree;
- `tests/workspace` was selected as target-relevant verification;
- the R01 grounding guard classified the review as grounded;
- the primary checkout was not modified and no automatic apply occurred;
- the worker did not self-accept the artifact.

The R01 reviewer-grounding repair and R02 target-relevant verification selection are useful bounded improvements independent of whether this mission passes ART-V14-REAL-E2E.

## Why the mission does not pass

The artifact protocol requires the mission to identify a **real correctness, reliability, or security issue** and requires independent lead review to determine that the result is useful and correct. `v14-real-007` does not clear that bar.

The proposed patch is predominantly syntax-level typing modernization (`list`/`dict`/`set`/PEP 604 forms to `typing.List`/`Dict`/`Set`/`Optional`). That is not evidence of a real product defect.

The only substantive behavioral change converts provenance accumulation from an order-preserving list/de-duplication path:

- `provenance.extend(...)` / `append(...)`
- `list(dict.fromkeys(provenance))`

to an unordered set path:

- `provenance.update(...)` / `add(...)`
- `list(provenance)`

That can change provenance ordering and therefore changes observable output semantics without demonstrating that the prior order-preserving behavior was defective. The mission's own manifest explicitly flags this behavior-change risk and states that the reviewer claim about `typing.Set` preventing runtime mutation is incorrect.

No targeted regression demonstrates a pre-patch defect that the patch fixes. Passing the existing `tests/workspace` suite proves compatibility with those tests, not that the discovered issue is real or that the set conversion is a correct repair.

Therefore minimum protocol criteria 5 and 10 are not satisfied. A plausible, material, test-passing patch is insufficient when the claimed defect itself is not independently validated.

## Required next action

Preserve `v14-real-007` unchanged as failed independent-review evidence. Do not rewrite it into a pass.

Run a **new preregistered real mission** on a different bounded operational/runtime subsystem. Before lead acceptance, the evidence must make the discovered defect independently defensible through at least one of:

1. a reproducible pre-patch failing behavior or invariant violation;
2. a code-path contradiction that can be verified directly from source plus a targeted regression that would fail before the patch; or
3. another concrete correctness/security/reliability failure with objective evidence.

The patch must then fix that demonstrated issue, execute a target-relevant regression/check, preserve review/apply boundaries, stay at `$0`, and avoid introducing an unrelated semantic regression.

## Governance

- `ART-V14-REAL-E2E` remains `drafting`.
- This review does not accept V1.4.
- G13/G12/G14/LIVE142 gates remain separate and unchanged.
- No main merge, public release/deploy, force push, or additional spend is authorized.
