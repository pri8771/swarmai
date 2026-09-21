# SwarmAI worker packet backlog — current

Updated by `LEAD-20260921-036`. Canonical artifact lifecycle remains in `ARTIFACT_REGISTRY.json`; this file tracks bounded execution state only. `WORK_QUEUE.md`, assignment files, and artifact acceptance contracts control ordering and scope.

## Current topology and autonomous assignments

### A / HOST-MAC-DEV / `cursor/v2-runtime-lane`
Current tip observed: `11a7e1d51c4c4d630c7d83c1af65e380c32ad80f`; exact-tip CI `35615739781` green.
Assignment: `A-RESET-BATCH-04`, generation 4, enabled.

Execute sequentially, one bounded packet per invocation:
1. `V14-REAL-001-R` / `ART-V14-REAL-E2E` — generic model-output materialization repair plus a new real non-mock brokered mission.
2. `V2A-003c` / `ART-V15-LEASE-FENCING` — durable result acceptance fencing.

`OPS-AUTO-001-R` source repair was independently reviewed earlier at implementation `0d71520de72338b3ae38dca00258a07c134e2b2a`, exact-tip `39bba630306729b64ad4679346b1eb900f44ccaf`, CI `35609579398` green. That execution was human-prompted and therefore does **not** satisfy autonomous self-launch acceptance. Do not replay it.

No generation-4 autonomous source push is visible yet.

### B / HOST-WIN-DEV / `cursor/v2-product-lane`
Current tip observed: `a908a0e1ff023743892ecb10cfb7bd8df4b53d53`; exact-tip CI `35615750755` red at Ruff in the offline job; console checks are green.
Assignment: `B-RESET-BATCH-04`, generation 4, enabled.

Execute sequentially, one bounded packet per invocation:
1. `B-OPS-AUTO-SYNC-02` / `ART-OPS-AUTONOMOUS-WORKERS` — synchronize reviewed runner repair while preserving Windows heartbeat/status changes and restore exact-tip CI.
2. `V2B-000` / `ART-V20-INTEGRATED-CANDIDATE` — sync reviewed integration baseline only and run the Windows baseline.
3. `V2B-001-R4` / `ART-V13-TASK-POOL` — final executable G13 remint/freeze with >=15 genuine semantic archetypes in every required family/size cell.

Windows B remains final executable G13 implementation/test owner. Counted qualification remains prohibited until independent lead freeze and real sealed-reference binding.

No generation-4 autonomous source push is visible yet.

## Heartbeat stress test

Mode remains `stress_5m`; effective worker cadence remains 5 minutes. Only `trigger=scheduler` counts.

Latest independently reconciled Phase-1 state:
- A: **1/3** at `15:52:14Z`; `15:37:12Z -> 15:52:14Z` is ~15m02s, above the 8m maximum.
- B: **1/3** at `15:44:17Z`; `15:29:17Z -> 15:44:17Z` is 15m, above the 8m maximum.
- Both ledgers are fresh at the evidence cutoff, but neither is producing the required 3–8m spacing.
- The host status markdown pages are stale despite new ledger receipts.

Current branch heartbeat installers configure 5m OS wake intervals and current heartbeat source publishes a human-readable status page after each ledger write. The observed ~15m spacing + stale status pages indicate stale installed host copies/jobs until disproven. Reinstall/verify the current heartbeat and autonomous-worker services on both hosts.

Phase 2 (`soak_15m_24h`) has **not started**. No soak time may be backfilled. After both hosts reach 3 consecutive valid 5m receipts, lead may set 15m effective cadence and begin an exact 24-hour soak. Hourly restoration is forbidden before the full soak is verified.

## Autonomous-worker acceptance

`ART-OPS-AUTONOMOUS-WORKERS` remains drafting.

Required proof is unchanged: A and B must each self-launch at least one repo-assigned packet through the autonomous runner and push attributable implementation evidence **without a human prompting the Cursor conversation**. Scheduler heartbeat/status commits are liveness only.

No qualifying A or B self-launch + implementation push has been independently verified in this run.

## G13 / ART-V13-TASK-POOL

### Retry 06 — independently reviewed changes-required
External branch/commit: `worker/swarmai-v13-task-pool-freeze-06@f7800332594d67c8b872b3597abd59f35987a2a0`.

Findings retained:
- exact-tip ordinary offline pytest is red (`35610017583`);
- corpus has 15 records/cell but only 5 genuine semantic archetypes/cell;
- input-only/opaque-reference direction is useful, but independence depth is insufficient;
- counted qualification remains disabled;
- external Claude sandbox denied repository Python/pytest/Ruff/mypy execution.

Disposition: **changes required**. `ART-V13-TASK-POOL` remains drafting. `W-131B` remains prohibited.

### Final executable repair — local B
Packet: `V2B-001-R4`.

Required outcome includes:
- >=15 genuinely distinct semantic archetypes in each of 16 required family x size cells;
- versioned fail-closed semantic independence checker in addition to existing contamination axes;
- negative tests for scenario substitutions, seed/numeric/synthetic-ID siblings, clause-prefix/containment siblings and <15-group cells;
- input-only held-out records and opaque hidden-reference handles;
- no fabricated sealed-reference digest;
- actual generator/verifier/focused tests/Ruff/mypy/offline pytest execution on Windows B;
- `counted_qualification_ready=false` until lead-controlled sealed reference binding exists.

### External retry 07 — support/reference only
Task: `swarmai-v13-task-pool-freeze-07`.
Dispatch commit: `3a69e1f5937b99b4f1e9a2d98b634d69a3900a94`.
Workflow run: `35616363073`, **in progress**.
Base: `worker/swarmai-v13-task-pool-freeze-06@f7800332594d67c8b872b3597abd59f35987a2a0`.

No retry-07 result JSON or SwarmAI branch exists yet. If one appears, it is independent/reference evidence only and cannot override Windows-B executable ownership or artifact acceptance.

## V14 / ART-V14-REAL-E2E

The first genuine mission remains preserved as failed evidence: real local brokered inference produced implementation text but no material isolated-worktree diff, which was correctly rejected.

The read-only worker-pc audit `swarmai-v14-materialization-audit-01` completed successfully at `2026-09-21T15:09:06Z`. Lead independently confirmed two generic repair targets:
- prompt/parser mismatch: `_implement` requests raw full-file source while `_extract_python_file` generically requires fenced code;
- empty-diff classification: `_implement` can report `implement_applied` after a write attempt despite no material git diff.

Lane A owns the repair. Preserve git diff as material authority, add unrelated temp-repo regressions, and rerun a separately preregistered real mission against a different subsystem. No target-specific known answer is permitted.

## V15 / durable worker path

- `V2A-003b-R2`: accepted bounded claim/renew/expire repair slice.
- `ART-V15-LEASE-FENCING` remains drafting until `V2A-003c` result acceptance is implemented and independently reviewed.
- `V2A-H6A-R`: accepted hardening slice.
- DBOS decision remains partial reuse only.

After A's `V2A-003c` review: integrate only reviewed slices with a receipt, then `V2A-004` durable worker service/client and real Mac+Windows recovery/multi-host evidence.

## Other hard blockers retained

- G12 remote overlap: **0 admitted remote routes**; no paid fallback and no remote canary without exact account/model zero-charge eligibility.
- G13 reviewer calibration/held-out qualification incomplete; zero qualified cells.
- G14 role/live-adaptive proof remains blocked on G12/G13.
- LIVE-142 campaign not started; real wall clock cannot be backfilled.
- V2.0 168-hour reliability campaign not started; real wall clock cannot be backfilled.
- No main merge, public release/deploy, force push, additional spend, fabricated success or known-answer substitution.
