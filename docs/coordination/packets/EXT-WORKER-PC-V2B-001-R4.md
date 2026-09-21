# EXT-WORKER-PC-V2B-001-R4 — ART-V13-TASK-POOL semantic-independence repair

Status: ready for worker-pc when capacity is free
Story points: SP3
Artifact: `ART-V13-TASK-POOL`
Intended artifact transition: remain `drafting` until independent lead review; at most request `reviewable`.
Required base: `worker/swarmai-v13-task-pool-freeze-06@f7800332594d67c8b872b3597abd59f35987a2a0`
Expected worker branch: `worker/swarmai-v13-task-pool-freeze-07`
Authority: `docs/coordination/EVAL_131_QUALIFICATION_PROTOCOL.md`, `docs/artifacts/current/ART-V13-TASK_POOL_REPAIR_CONTRACT.md`, and the prior R3 packet.

## Independent lead disposition of retry 06

Retry 06 is useful blocker evidence, not a freeze candidate. The branch and transport commit are real, but the exact commit CI is red in the ordinary offline pytest job and the worker's own measured corpus has only **5 semantic archetypes per required family/size cell**, versus the preregistered minimum of **15 independent observations**. The other records are scenario-name substitutions and cumulative structural variants. Counted qualification remains prohibited.

The remote worker environment also hard-blocks repository Python/pytest/Ruff/mypy execution. Do not spend this packet repeatedly probing those commands. GitHub CI on the pushed branch is the execution environment for this repair; report local execution as unavailable rather than fabricating it.

## Required implementation

### R4.1 — create a mechanically auditable semantic-independence axis

Extend the held-out record/freeze contract with a versioned semantic task-archetype identity, using the simplest fail-closed design that does not weaken the existing eight independence/contamination axes.

Requirements:
- every counted-eligible held-out record carries or deterministically maps to a versioned semantic archetype / independence-group identity;
- the verifier requires at least **15 distinct semantic groups in each of the 16 required `coding/planning/reasoning/extraction x S/M/L/XL` cells**;
- duplicate semantic groups within a counted cell fail closed;
- scenario/domain noun substitutions, numeric/seed substitutions, synthetic identifier changes, and cumulative clause-only growth from the same base recipe cannot create a new group by themselves;
- preserve existing case-id, payload, prompt, normalized-template, and cross-partition contamination rejection;
- freeze/version the new checker identity and pin any changed source/spec files.

Add direct negative tests proving at minimum:
1. two records with different scenario nouns but the same semantic archetype are rejected;
2. two records differing only by numeric/seed/synthetic identifiers are rejected;
3. cumulative clause-only variants of one archetype do not satisfy two independent groups;
4. a required cell with 15 records but fewer than 15 semantic groups fails;
5. all legacy cross-partition/template contamination negatives still pass.

### R4.2 — repair the committed corpus, not just the checker

Re-author/re-mint the worker-visible held-out corpus so **every required cell contains at least 15 substantively distinct task archetypes** under the new frozen semantic-group rule.

A distinct archetype must change the actual problem/specification being solved, not merely names, numbers, seeds, prose synonyms, domain nouns, list length, or an appended copy of requirements from the same recipe.

Keep each record input-only and preserve correct S/M/L/XL classification. It is acceptable to keep exactly 15 records per cell if all 15 are genuinely distinct; do not inflate depth by replaying siblings. Preserve immutable case IDs or mint a new freeze identity/version consistently if IDs/spec semantics must change.

### R4.3 — preserve sealed-reference safety

Do not add plaintext answers, grader fixtures, rubrics, hidden tests, expected outputs, or reference solutions to the worker-visible branch. Preserve opaque hidden-reference handles and fail-closed resolution. The lead-controlled sealed bundle content digest is still not available here, so keep `counted_qualification_ready=false` and never fabricate a bundle digest.

### R4.4 — fix exact-tip offline CI without weakening tests

Retry 06 exact-tip CI `35610017583` failed only in ordinary offline pytest; Ruff, mypy, packaging/Alembic and console jobs passed. Make the new branch's ordinary offline CI green without deleting, xfail-ing, skipping, or loosening the task-pool assertions. Any test/schema updates must strengthen or faithfully adapt the semantic-independence contract.

Because local Python execution is blocked on worker-pc, do not claim local test passes. Push a coherent branch and let GitHub Actions execute the exact commit. The lead will independently inspect that run before any artifact state change.

### R4.5 — truthful provenance/evidence

Update the G13 evidence to bind:
- exact parent/base `f7800332594d67c8b872b3597abd59f35987a2a0`;
- actual changed files;
- exact semantic-group counts per required cell;
- answer-leak count and contamination status only when mechanically established;
- local commands actually executed vs denied;
- `counted_qualification_ready=false` and `counted_qualification_started=false`;
- remaining blockers.

Do not claim GitHub CI results from inside the worker session before the transport commit exists. Request lead review only.

## Scope ownership

Allowed: `benchmarks/g13/**`, `src/swarm/evals/**` only where needed for the task-pool freeze/independence contract, `tests/evals/**`, `scripts/g13_*`, and `docs/evidence/g13/**`.

Do not edit Session-A-owned API/store/routes/schemas/CLI/database migrations/lockfiles, coordination acceptance state, main/release/deployment state, provider configuration, or secrets.

## Required return

Return branch/commit if known, parent, changed files, per-cell record count and distinct semantic-group count, exact local command outcomes/denials, and remaining blockers. Do not self-accept, merge, start W-131B, or claim qualification.
