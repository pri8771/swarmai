# EXT-WORKER-PC-V2B-001-R3 — ART-V13-TASK-POOL repair

Status: ready when `worker-pc` capacity is free
Story points: SP2
Artifact: `ART-V13-TASK-POOL`
Intended artifact transition: `drafting -> reviewable` only; lead independently decides any later `verified`/freeze transition.
Required base: `worker/swarmai-v13-task-pool-freeze-04@6467552f86e40964e5bd26d85e3b3a74d03aa059`
Expected worker branch: `worker/swarmai-v13-task-pool-freeze-05`

## Why this repair exists

Retry 04 produced a real scoped branch and materially improved the task-pool design, but it is not freeze-ready:

1. exact-tip SwarmAI CI `35587202715` is red because the offline pytest step fails, even though Ruff, mypy, packaging and Alembic-head checks pass;
2. `TASK_POOL_FREEZE_V2.md` says the worker branch was uncommitted/unpushed, but the actual worker branch exists at `6467552f86e40964e5bd26d85e3b3a74d03aa059`; evidence must match the real source/evidence state;
3. the corpus construction still treats families of scenario-name substitutions / incremental structural loads as independent observations, while the current normalizer only erases uppercase synthetic identifiers and digit runs. Ordinary domain-noun/template siblings can therefore evade `holdout_template_duplicate`. That is not strong enough for the frozen EVAL-131 requirement that qualification observations be independent;
4. `counted_qualification_ready` correctly remains false because the sealed reference bundle content digest is not lead-bound. No counted W-131B run is authorized by this packet.

## Required implementation

### R3.1 — make exact-tip offline verification green

Reproduce the exact offline pytest failure from Actions `35587202715`, fix the defect without weakening the assertions, and keep Ruff/mypy/packaging/Alembic green. Run at minimum:

- `uv run ruff check .`
- `uv run mypy src/swarm`
- focused `tests/evals/test_task_pool_freeze_v2.py`
- the repository's ordinary non-live pytest suite if available within the bounded task window.

Do not delete, xfail or blanket-ignore failing task-pool verification.

### R3.2 — evidence provenance must be exact

Update the v2 evidence document to report the actual worker branch/commit, exact commands actually executed, exact CI run/job results, and remaining blockers. Remove stale claims that the branch is uncommitted or was not pushed. Never claim a command passed if it was denied/not run.

### R3.3 — mechanically stronger independence

The qualification pool must provide at least 15 genuinely independent held-out observations in each required `coding/planning/reasoning/extraction x S/M/L/XL` cell.

A scenario/domain noun substitution, numeric substitution, seeded identifier change, or cumulative addition/removal of clauses from the same base recipe MUST NOT by itself create a new independent observation.

Implement one of these bounded approaches, preferring the simplest mechanically auditable design:

- author at least 15 substantively distinct task archetypes/specifications per required cell; OR
- add a versioned `independence_group_id` / archetype identity derived from a frozen semantic task specification and require at least 15 distinct groups per cell, with the checker rejecting multiple counted observations from the same group.

In either approach, the checker must fail closed when ordinary scenario-name substitutions or seed-isomorphic siblings share the same task archetype. Add direct negative tests showing such siblings are rejected. Preserve cross-partition ID/payload/prompt/template contamination checks.

Do not redefine the preregistered EVAL-131 statistical threshold or call retries on one semantic task independent observations.

### R3.4 — preserve sealed-reference boundary

Worker-visible records remain input-only. No plaintext answers, grader fixtures, rubrics or reference solutions may be placed on the worker-visible branch. Preserve opaque `hidden_reference_id` semantics and fail-closed resolution.

The lead-owned sealed bundle content digest is not available on this worker branch. Keep `counted_qualification_ready = false` until a lead-controlled non-worker-readable bundle is actually created and bound. Do not fabricate that digest and do not run counted W-131B qualification.

## Scope ownership

Allowed paths are benchmark/evaluation/evidence/test paths needed for this repair. Do not edit Session-A-owned API/store/routes/schemas/CLI/database migrations/lockfiles and do not touch main/release/deployment state.

## Required return

Return exact commit and parent, changed files, exact command outcomes, exact CI URL/run if available, per-cell distinct independence-group/archetype counts, contamination statistics, answer-leak count, sealed-reference status, and remaining blockers. Request lead review only; never self-accept or merge.
