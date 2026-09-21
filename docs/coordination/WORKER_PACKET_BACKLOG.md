# SwarmAI worker packet backlog — current

Updated by `LEAD-20260921-036`. Canonical artifact lifecycle remains in `ARTIFACT_REGISTRY.json`; this file tracks bounded execution state only. `WORK_QUEUE.md`, assignment files, and artifact acceptance contracts control ordering and scope.

## Current topology and autonomous assignments

### A / HOST-MAC-DEV / `cursor/v2-runtime-lane`
Current tip observed: `11a7e1d51c4c4d630c7d83c1af65e380c32ad80f`.
Assignment: `A-RESET-BATCH-04`, generation 4, enabled.

Execute sequentially, one bounded packet per invocation:
1. `V14-REAL-001-R` / `ART-V14-REAL-E2E` — generic model-output materialization repair plus a new real non-mock brokered mission.
2. `V2A-003c` / `ART-V15-LEASE-FENCING` — durable result acceptance fencing.

`OPS-AUTO-001-R` source repair was independently reviewed earlier at implementation `0d71520de72338b3ae38dca00258a07c134e2b2a`, exact-tip `39bba630306729b64ad4679346b1eb900f44ccaf`, CI `35609579398` green. That execution was human-prompted and therefore does **not** satisfy autonomous self-launch acceptance. Do not replay that completed repair.

### B / HOST-WIN-DEV / `cursor/v2-product-lane`
Current tip observed: `a908a0e1ff023743892ecb10cfb7bd8df4b53d53`.
Assignment: `B-RESET-BATCH-04`, generation 4, enabled.

Execute sequentially, one bounded packet per invocation:
1. `B-OPS-AUTO-SYNC-02` / `ART-OPS-AUTONOMOUS-WORKERS` — synchronize the reviewed runner repair while preserving Windows status/heartbeat features and execute coordination tests.
2. `V2B-000` / `ART-V20-INTEGRATED-CANDIDATE` — sync the reviewed integration baseline only and run the Windows baseline.
3. `V2B-001-R4` / `ART-V13-TASK-POOL` — final executable G13 remint/freeze attempt with >=15 genuine semantic archetypes in every required family/size cell.

The Windows lane is the final executable G13 implementation/test owner because the external Claude sandbox repeatedly blocks repository Python/pytest/Ruff/mypy execution. Counted qualification remains prohibited until independent lead freeze and real sealed-reference binding.

## Heartbeat owner stress test

Mode remains `stress_5m`; effective worker cadence remains 5 minutes. Only `trigger=scheduler` counts.

Latest lead-reconciled Phase-1 state:
- A: **1/3** at `15:07:07Z`. The preceding `15:05:27Z -> 15:07:07Z` gap is only 1m40s, below the required 3m minimum, so the latest receipt starts a fresh valid chain.
- B: **1/3** at `14:59:17Z`. The preceding `14:44:17Z -> 14:59:17Z` gap is 15m, above the required 8m maximum, so the latest receipt starts a fresh valid chain.
- At the latest lead observation both are within the Phase-1 12-minute stale threshold; neither has completed Phase 1.
- Phase 2 (`soak_15m_24h`) has **not started**. No soak time may be backfilled.

After both hosts independently reach 3 consecutive scheduler receipts with 3–8 minute adjacent gaps, lead may set 15-minute effective cadence and begin an exact 24-hour soak. Hourly restoration is forbidden before the full soak is verified.

## Autonomous-worker acceptance

`ART-OPS-AUTONOMOUS-WORKERS` remains drafting.

Required proof remains unchanged: A and B must each self-launch at least one repo-assigned packet through the autonomous runner and push attributable implementation evidence **without a human prompting the Cursor conversation**. Scheduler heartbeat commits/status-page commits are liveness/coordination evidence only, not autonomous implementation evidence.

No qualifying A or B self-launch + implementation push has been independently verified in this lead run.

## G13 / ART-V13-TASK-POOL

### Retry 06 — independently reviewed changes-required
External task: `swarmai-v13-task-pool-freeze-06`.
Branch/commit: `worker/swarmai-v13-task-pool-freeze-06@f7800332594d67c8b872b3597abd59f35987a2a0`.
Parent: `6467552f86e40964e5bd26d85e3b3a74d03aa059`.
Lead review: `docs/coordination/reviews/ART-V13-TASK-POOL-RETRY06-LEAD-REVIEW.md`.

Independent findings:
- real scoped branch/commit exists;
- worker-visible freeze remains input-only and counted qualification remains disabled;
- exact-tip CI `35610017583` is red because ordinary offline pytest fails, while Ruff, mypy, packaging/Alembic and console checks pass;
- committed corpus has 15 records per required cell but only **5 genuine semantic archetypes per cell**;
- scenario-name substitutions and cumulative structural variants cannot satisfy the preregistered >=15-independent-observation requirement;
- external sandbox denied repository Python/pytest/Ruff/mypy execution.

Disposition: **changes required**. `ART-V13-TASK-POOL` remains drafting. `W-131B` remains prohibited. `WORKER_PERFORMANCE.json` is not incremented for this repeated repair lineage.

### Final executable repair — local B
Packet: `V2B-001-R4` (`docs/coordination/packets/V2B-001-R4.md`).

Required outcome includes:
- >=15 genuinely distinct semantic archetypes in each of 16 required family x size cells;
- versioned fail-closed semantic independence checker in addition to existing contamination axes;
- negative tests for scenario substitutions, seed/numeric/synthetic-ID siblings, clause-prefix/containment siblings and <15-group cells;
- input-only held-out records and opaque hidden-reference handles;
- no fabricated sealed-reference digest;
- actual generator/verifier/focused tests/Ruff/mypy/offline pytest execution on Windows B;
- `counted_qualification_ready=false` until lead-controlled sealed reference binding exists.

### External retry 07 — queued support only, not final gate owner
A transport task `swarmai-v13-task-pool-freeze-07` was created from exact retry-06 base `f7800332594d67c8b872b3597abd59f35987a2a0` under R4 semantics. Dispatch commit: `3a69e1f5937b99b4f1e9a2d98b634d69a3900a94`; workflow run `35616363073` is pending.

A capacity race was discovered immediately afterward: worker-pc is already executing `swarmai-v14-materialization-audit-01` read-only diagnostic run `35616202805`. Capacity 1 is therefore still enforced; retry 07 is not executing concurrently. If retry 07 eventually executes, treat it as independent/reference evidence only; do not auto-merge it and do not let it override the executable Windows-B gate or artifact acceptance.

## V14 / ART-V14-REAL-E2E

The first genuine mission remains preserved as failed evidence: real local brokered inference produced implementation text but no material isolated-worktree diff, which was correctly rejected.

A owns `V14-REAL-001-R` implementation/rerun. worker-pc currently owns only the independent **read-only** diagnostic task `swarmai-v14-materialization-audit-01` to trace goal -> model response -> parsing/materialization -> worktree edit -> diff capture and propose generic regression coverage. No remote source edits or acceptance authority are granted.

## V15 / durable worker path

- `V2A-003b-R2`: accepted bounded claim/renew/expire repair slice.
- `ART-V15-LEASE-FENCING` remains drafting until `V2A-003c` durable result acceptance is implemented and independently reviewed.
- `V2A-H6A-R`: accepted hardening slice.
- DBOS decision remains partial reuse only; it does not replace Swarm-owned fencing/transport/schema.

After A's `V2A-003c` review: integrate only reviewed slices with a receipt, then `V2A-004` durable worker service/client and real Mac+Windows recovery/multi-host evidence.

## Other hard blockers retained

- G12 remote overlap: **0 admitted remote routes**; no paid fallback and no remote canary without exact account/model zero-charge eligibility.
- G13 reviewer calibration/held-out qualification incomplete; zero qualified cells.
- G14 role/live-adaptive proof remains blocked on G12/G13.
- LIVE-142 campaign not started; real wall clock cannot be backfilled.
- V2.0 168-hour reliability campaign not started; real wall clock cannot be backfilled.
- No main merge, public release/deploy, force push, additional spend, fabricated success or known-answer substitution.
