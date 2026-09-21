# ART-V13-TASK-POOL retry 06 — independent lead review

Date: 2026-09-21
Lead run: LEAD-20260921-036
Artifact: `ART-V13-TASK-POOL`
Task: `swarmai-v13-task-pool-freeze-06`
Worker: `worker-pc` / Claude
Branch: `worker/swarmai-v13-task-pool-freeze-06`
Commit: `f7800332594d67c8b872b3597abd59f35987a2a0`
Parent: `6467552f86e40964e5bd26d85e3b3a74d03aa059`
Disposition: **CHANGES REQUIRED — DO NOT FREEZE; artifact remains drafting**

## Evidence independently verified

- The worker branch exists and the transport produced commit `f7800332594d67c8b872b3597abd59f35987a2a0` from parent `6467552f86e40964e5bd26d85e3b3a74d03aa059`.
- Diff scope is limited to four benchmark/evidence files: the v2 task-pool manifest, its checksum cover, and two G13 evidence documents. No Session-A runtime/API/store/schema/migration/CLI/lockfile path was changed.
- The sanitized remote-workers result is useful as a self-report only after branch verification. It accurately states that worker-local Python/pytest/Ruff/mypy/uv execution was denied and that the delivered work is a scoped partial.
- Retry 06 corrected stale provenance from retry 04 and explicitly withdrew the earlier claim of 15 semantically independent observations per cell.
- Its own measured corpus evidence reports only **5 distinct semantic archetypes per required family/size cell**, a deficit of 10 against the preregistered minimum of 15. The remaining records are produced through scenario-name substitutions and cumulative structural variants.
- The existing `g13-independence-checker-v2` normalizes uppercase synthetic identifiers and digit runs and rejects exact normalized-template collisions, but it does not mechanically collapse ordinary scenario/domain substitutions or cumulative clause-only siblings into a shared semantic archetype. Therefore the current mechanical `15 records/cell` result cannot be accepted as `15 independent observations/cell`.
- Exact-tip GitHub Actions run `35610017583` completed **failure**. Ruff, mypy, packaging/install, Alembic-head checks and the console job passed; the ordinary offline pytest step failed.

## Acceptance decision

`ART-V13-TASK-POOL` remains `drafting`. No lead freeze is granted. `W-131B` counted qualification remains prohibited. Retry 06 is preserved as useful blocker/provenance evidence, not rewritten as success.

The result cannot become reviewable/frozen because both of these independent blockers remain:

1. semantic held-out depth is 5 archetypes/cell, not >=15 genuinely independent archetypes/groups/cell;
2. exact-tip ordinary offline pytest is red.

The sealed-reference boundary remains intentionally unresolved for counted qualification: no lead-controlled sealed bundle content digest has been bound, so `counted_qualification_ready=false` remains the only valid state.

## Required repair

Proceed with `EXT-WORKER-PC-V2B-001-R4` from exact base `f7800332594d67c8b872b3597abd59f35987a2a0`:

- add a versioned fail-closed semantic archetype/independence-group axis;
- mechanically require >=15 distinct semantic groups in every required cell;
- re-author/re-mint the committed input-only corpus so all 16 cells actually satisfy that rule;
- add negative tests for scenario-name, numeric/seed/synthetic-ID and cumulative-clause siblings plus 15-record/<15-group failure;
- preserve all existing cross-partition ID/payload/prompt/template contamination checks and hidden-reference safety;
- keep counted qualification disabled until a real sealed reference bundle is lead-bound;
- make exact-tip GitHub CI green without weakening tests.

Because worker-pc is known to deny repository Python execution, GitHub Actions on the transport-created commit is the required executable verification environment for the next remote attempt. Worker self-report remains insufficient for acceptance.
