# SwarmAI execution queue — reset 2026-09-21

Canonical lifecycle: `ARTIFACT_REGISTRY.json`.  
Audit: `FULL_AUDIT_2026-09-21.md`.  
Plan: `EXECUTION_RESET_PLAN.md`.  
Live dashboard: `LIVE_PROGRESS.md`.

## Fixed topology

### Lane A — Mac / runtime + real acceptance

Branch: `cursor/v2-runtime-lane`  
Current observed tip: `11a7e1d51c4c4d630c7d83c1af65e380c32ad80f`; exact-tip CI `35615739781` green.  
Assignment: `A-RESET-BATCH-04`, generation 4, enabled.

1. `V14-REAL-001-R` — generic materialization repair + new real end-to-end mission.
2. `V2A-003c` — durable result acceptance fencing.
3. After independent review: reviewed-slice integration receipt -> `V2A-004` durable worker service -> real multi-host/recovery.

No reset-generation autonomous implementation push is visible yet. A's ledger is active but the fresh epoch is not registered and the human-readable status page is stale, so the current installed heartbeat/autonomous services must be refreshed before self-launch evidence can be trusted.

### Lane B — product + evaluation

Branch: `cursor/v2-product-lane`  
Current observed tip: `534476393257794c4e8ebf8d65f44fd090ab28eb`; exact-tip CI `35625964121` green.  
Assignment: `B-RESET-BATCH-05`, generation 5, enabled.

Completed and reviewed:
- `B-OPS-AUTO-SYNC-02` — runner repair synchronized; CI `35624109265` green.
- `V2B-000` — reviewed integration baseline `9ce727842446b98cfa55c28c7e70808f57f17d7b` synchronized into the product lane; no integration promotion claimed.
- `V2B-001-R4` — authoritative G13 v3 task-pool freeze implementation; lead freeze accepted.

Current:
1. `V2B-002` — calibration-only reviewer benchmark/scorer repair + freeze candidate.
2. After independent reviewer-benchmark freeze and real sealed-reference binding: W-131B product counted qualification and separately versioned reviewer held-out qualification.
3. Then V16/V17 product lane packets.

Generation 4 must not replay. The completed source work was human-prompted; an autonomous `V2B-001-R4` attempt exited without an attributable source push, so B autonomous self-launch acceptance is still not proven.

The implementation session reported Linux while using HOST-WIN-DEV coordination identity. Platform-neutral evaluation contracts may rely on exact-tip CI; this session must not be used as Windows-specific runtime/install evidence.

### Lane C — worker-pc / independent support

Infrastructure: `pri8771/remote-workers` only; no SwarmAI acceptance authority.

Completed support:
- `swarmai-v14-materialization-audit-01` — useful read-only V14 diagnosis.
- `swarmai-v13-task-pool-freeze-07` — real branch `worker/swarmai-v13-task-pool-freeze-07@02cd0a2ea23342c331e83efd78b7682617dd16d3`; one G13-scoped commit from retry06; CI `35625433324` green. Retained as support/reference only; not integrated over local-B v3.

Current execution:
- `swarmai-v13-task-pool-v3-audit-01` — read-only adversarial audit of exact local-B v3 tip `534476393257794c4e8ebf8d65f44fd090ab28eb`.
- Remote-workers dispatch commit `31b0234a93fe2043b250af91a0f97c6b8561504d`; workflow `35629554863` in progress.

Lane C does not own Python/test-dependent acceptance gates and cannot self-accept artifacts.

## G13 current decision

`ART-V13-TASK-POOL` is **verified/frozen** as `g13-pool-freeze-v3` at `cursor/v2-product-lane@534476393257794c4e8ebf8d65f44fd090ab28eb`.

Independent lead review confirmed:
- 240 held-out inputs total;
- 15 genuinely distinct semantic archetypes in every required coding/planning/reasoning/extraction x S/M/L/XL cell;
- versioned fail-closed semantic sibling/contamination rejection;
- separate calibration IDs/hashes;
- input-only worker-visible held-out records and opaque hidden-reference handles;
- no fabricated sealed bundle content digest;
- `counted_qualification_ready=false`, `w131b_started=false`;
- B reported generator/verifier + Ruff + mypy + focused/offline pytest passes;
- exact-tip GitHub Actions `35625964121` succeeded.

Review record: `docs/coordination/reviews/ART-V13-TASK-POOL-V3-LEAD-REVIEW.md`.

**W-131B remains prohibited** until ChatGPT lead binds a real sealed-reference bundle content digest to the frozen IDs without exposing answers. Reviewer-role calibration/freeze is also required before reviewer held-out qualification.

## V14 current diagnosis

`ART-V14-REAL-E2E` remains drafting. The first genuine mission remains useful failed evidence: real brokered local inference produced no material isolated-worktree diff and was correctly rejected.

Repair targets remain generic:
- `_implement` requests raw full-file source while `_extract_python_file` generically expects fenced code;
- `_implement` can label a write attempt `implement_applied` despite an empty material git diff.

Lane A must repair generically, preserve git diff as material-result authority, add unrelated temporary-repo regressions, then run the separately preregistered new real mission on a different subsystem. No known-answer substitution is allowed.

## Heartbeat stress test

Phase 1 remains active; worker effective cadence is 5 minutes and only `trigger=scheduler` counts.

- A: **0/3 counted**. Latest ledger receipt `16:52:23Z` is fresh, but there is no required fresh-epoch `session_started` registration; `status/HOST-MAC-DEV.md` is stale.
- B: **verified 3/3** on `16:17:56Z -> 16:22:59Z -> 16:28:03Z`; current status publishing is healthy.
- Phase 2 has **not started**. It begins only after A also passes Phase 1, then runs 15-minute cadence for 24 real elapsed hours. No backfill.

## Critical acceptance path

1. Restore A's reset-aware heartbeat/autonomous daemon and prove A repo-driven self-launch on `V14-REAL-001-R`.
2. Pass one genuine V1.4 real end-to-end mission.
3. Freeze reviewer benchmark + bind real sealed references; run G13 product/reviewer qualification.
4. Finish `V2A-003c`, durable worker service and real multi-host/recovery evidence.
5. Admit two exact zero-charge remote routes and run G12 remote overlap.
6. Complete V1.6/V1.7.
7. Complete V1.8/V1.9/V2.0 integration and real elapsed acceptance campaigns.

No main merge, public release/deploy or additional spend is authorized.
