# Lead review — ART-V13-TASK-POOL retry 04

Review time: 2026-09-21T10:49:09Z
Artifact: `ART-V13-TASK-POOL`
Packet: `EXT-WORKER-PC-V2B-001-R2`
Worker task: `swarmai-v13-task-pool-freeze-04`
Worker branch: `worker/swarmai-v13-task-pool-freeze-04`
Worker commit: `6467552f86e40964e5bd26d85e3b3a74d03aa059`
Parent: `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
Disposition: **changes required**
Artifact lifecycle after review: **drafting**
Counted W-131B qualification authorized: **no**
Merge authorized: **no**

## Evidence independently verified

- The worker branch exists and is exactly one commit ahead of retry 02.
- Diff scope is confined to benchmark/evaluation/evidence/test paths plus benchmark attributes/README; no Session-A-owned API/store/routes/schemas/CLI/migrations/lockfiles are changed.
- Retry 04 contains a v2 input-only corpus with 16 required family/size shards and 15 records per shard, plus frozen identity/checksum files, sealed-reference interface code and negative tests.
- Exact-tip SwarmAI Actions run `35587202715` is red. Ruff, mypy, packaging and Alembic heads pass; the offline pytest step fails. Console CI passes. Default live-gated CI is notice-only and is not acceptance evidence.
- remote-workers run `35580580156` executed the submitted task and pushed the SwarmAI branch, but its `Publish sanitized results` step failed; therefore `results/swarmai-v13-task-pool-freeze-04.json` is absent.

## Positive findings

1. Worker-visible records use opaque `hidden_reference_id` handles rather than plaintext answer/grader/reference fields.
2. The corpus now reaches the numerical floor of 15 visible records per required family/size cell.
3. The sealed resolver is designed to fail closed without a bound source/digest.
4. The worker preserved retry-02/v1 history and stayed within the allowed evaluation scope.
5. Static/type/package checks are green at the exact worker commit.

## Changes required

### CR-1 — exact-tip offline pytest must pass

A frozen task pool cannot be promoted while its own verification suite fails. Reproduce and repair the exact failure without deleting, skipping or weakening the verification assertions.

### CR-2 — evidence provenance is stale

`TASK_POOL_FREEZE_V2.md` states that the work is uncommitted/unpushed and that no commit SHA exists. The real worker branch is committed/pushed at `6467552f86e40964e5bd26d85e3b3a74d03aa059`. The evidence document must be rebound to actual source, commands and CI outcomes.

### CR-3 — independence is not yet mechanically strong enough

The corpus describes `5 task variants x 3 structural loads = 15` observations per cell. Sample records within one cell reuse a common task recipe while changing ordinary scenario/domain nouns and incrementally adding clauses. The v2 normalizer currently erases uppercase synthetic identifiers and digit runs, but it does not abstract ordinary scenario nouns or otherwise bind records to a semantic task-archetype identity. Consequently seed/template siblings can evade `holdout_template_duplicate` while still being generated from the same underlying recipe.

The EVAL-131 contract requires independent held-out observations; retries or superficial regenerations do not become independent merely because IDs or surface payloads differ. The next repair must either author >=15 substantively distinct task archetypes per required cell or mechanically enforce >=15 distinct frozen semantic independence groups/archetypes per cell. Direct negatives must prove ordinary domain-name / seed-isomorphic siblings are rejected.

### CR-4 — sealed reference content is not lead-bound

The v2 evidence correctly reports `counted_qualification_ready = false` because no lead-controlled sealed bundle content digest is bound. Keep it false. The lead has preregistered `docs/coordination/G13_SEALED_REFERENCE_BINDING_PROTOCOL.md`; a real non-worker-readable bundle and binding receipt are still required before counted qualification.

## Next packet

`EXT-WORKER-PC-V2B-001-R3` at `docs/coordination/packets/EXT-WORKER-PC-V2B-001-R3.md`, based on exact retry-04 commit. Dispatch only when `worker-pc` capacity is actually free. The worker is currently occupied by an unrelated remote-workers task, so no overlapping SwarmAI dispatch is authorized.
