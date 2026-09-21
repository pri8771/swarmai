# SwarmAI execution queue — reset 2026-09-21

Canonical lifecycle: `ARTIFACT_REGISTRY.json`.
Audit: `FULL_AUDIT_2026-09-21.md`.
Plan: `EXECUTION_RESET_PLAN.md`.
Live dashboard: `LIVE_PROGRESS.md`.

## Fixed topology

### Lane A — Mac / runtime + real acceptance
Branch: `cursor/v2-runtime-lane`
Current observed tip: `11a7e1d51c4c4d630c7d83c1af65e380c32ad80f`; exact-tip CI `35615739781` green.
Assignment: `A-RESET-BATCH-04`, generation 4.

1. `V14-REAL-001-R` — generic materialization repair + new real end-to-end mission.
2. `V2A-003c` — durable result acceptance fencing.
3. After lead review: reviewed-slice integration receipt -> `V2A-004` durable worker service -> real multi-host/recovery.

### Lane B — Windows / product + evaluation
Branch: `cursor/v2-product-lane`
Current observed tip: `a908a0e1ff023743892ecb10cfb7bd8df4b53d53`; exact-tip CI `35615750755` red at Ruff on the unsynchronized autonomous-runner source.
Assignment: `B-RESET-BATCH-04`, generation 4.

1. `B-OPS-AUTO-SYNC-02` — synchronize the independently reviewed runner repair while preserving Windows status/heartbeat features; restore exact-tip coordination-source CI.
2. `V2B-000` — sync reviewed integration baseline and run Windows baseline.
3. `V2B-001-R4` — final executable G13 task-pool remint/freeze with >=15 genuine semantic archetypes per required cell and actual Windows verification.
4. After lead freeze: reviewer calibration/freeze -> counted qualification -> V16/V17.

### Lane C — worker-pc / independent support
Infrastructure: `pri8771/remote-workers` only; no SwarmAI acceptance authority.

Current execution:
- `swarmai-v14-materialization-audit-01` — read-only diagnostic support for Lane A; workflow `35616202805` is in progress.

Queued transport:
- `swarmai-v13-task-pool-freeze-07` — workflow `35616363073` is pending behind the occupied capacity-1 worker. Because Windows B is now the executable/final G13 owner, any retry-07 output is reference evidence only: no automatic integration and no acceptance claim.

Lane C does not own Python/test-dependent acceptance gates when its Claude executor cannot run the required repository verification.

## G13 current decision

Retry 06 is independently **changes-required** at `worker/swarmai-v13-task-pool-freeze-06@f7800332594d67c8b872b3597abd59f35987a2a0`:
- exact-tip CI `35610017583` is red in ordinary offline pytest;
- the frozen corpus has 15 records/cell but only 5 genuine semantic archetypes/cell;
- counted qualification remains disabled;
- `ART-V13-TASK-POOL` stays drafting and W-131B may not start.

Independent review: `docs/coordination/reviews/ART-V13-TASK-POOL-RETRY06-LEAD-REVIEW.md`.
Final executable repair packet: `docs/coordination/packets/V2B-001-R4.md` on Windows B after its runner sync and baseline packet.

## Heartbeat stress test

Phase 1 is active:
- A/B effective cadence 5m.
- only scheduler heartbeats count.
- each host needs 3 consecutive receipts; adjacent valid gaps are 3–8m.
- current lead-reconciled state: A **1/3** at `15:07:07Z`; B **1/3** at `14:59:17Z`.
- both prior adjacent gaps were outside the 3–8m window, so neither earlier receipt can extend the current chain.

Phase 2:
- starts only after both pass Phase 1;
- effective cadence 15m for 24 real elapsed hours;
- valid gaps 10–25m;
- unresolved >25m miss prevents a clean soak-success claim;
- no backfill.

After independently verified Phase 2 only:
- return worker effective cadence to hourly.

Every heartbeat updates its host status page:
- `status/HOST-MAC-DEV.md`
- `status/HOST-WIN-DEV.md`

## Critical acceptance path

1. Prove local autonomous self-launch on A and B.
2. Pass one genuine V1.4 real end-to-end mission.
3. Freeze G13 task pool, then qualify workers/reviewers.
4. Finish V1.5 result acceptance and durable worker service/multi-host evidence.
5. Admit two exact zero-charge remote routes and run G12 remote overlap.
6. Complete V1.6/V1.7.
7. Complete V1.8/V1.9/V2.0 integration and real elapsed acceptance campaigns.

No main merge, public release/deploy or additional spend is authorized.
