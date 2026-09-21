# SwarmAI execution queue — reset 2026-09-21

Canonical lifecycle: `ARTIFACT_REGISTRY.json`.
Audit: `FULL_AUDIT_2026-09-21.md`.
Plan: `EXECUTION_RESET_PLAN.md`.
Live dashboard: `LIVE_PROGRESS.md`.

## Fixed topology

### Lane A — Mac / runtime + real acceptance
Branch: `cursor/v2-runtime-lane`
Assignment: `A-RESET-BATCH-04`

1. `V14-REAL-001-R` — generic materialization repair + new real end-to-end mission.
2. `V2A-003c` — durable result acceptance fencing.
3. After lead review: reviewed-slice integration receipt -> `V2A-004` durable worker service -> real multi-host/recovery.

### Lane B — Windows / product + evaluation
Branch: `cursor/v2-product-lane`
Assignment: `B-RESET-BATCH-04`

1. `B-OPS-AUTO-SYNC-02` — synchronize reviewed runner repair and validate coordination tests.
2. `V2B-000` — sync reviewed integration baseline.
3. `V2B-001-R4` — final executable G13 task-pool remint/freeze with >=15 genuine semantic archetypes per required cell.
4. After lead freeze: reviewer calibration/freeze -> counted qualification -> V16/V17.

### Lane C — worker-pc / independent support
Infrastructure: `pri8771/remote-workers`.
Current task: `swarmai-v14-materialization-audit-01` read-only diagnostic support for Lane A.

Lane C does not own SwarmAI acceptance and does not own Python/test-dependent gates when its executor cannot run required verification.

## Heartbeat stress test

Phase 1:
- A/B effective cadence 5m.
- only scheduler heartbeats count.
- 3 consecutive receipts each; valid gaps 3–8m.

Phase 2:
- after both pass, effective cadence 15m for 24 real hours.
- valid gaps 10–25m.
- unresolved miss fails the clean soak.

After verified soak:
- return to hourly.

Every heartbeat updates its host status page:
- `status/HOST-MAC-DEV.md`
- `status/HOST-WIN-DEV.md`

Lead refreshes `LIVE_PROGRESS.md` hourly.

## Critical acceptance path

1. Prove local autonomous self-launch on A and B.
2. Pass one genuine V1.4 real end-to-end mission.
3. Freeze G13 task pool, then qualify workers/reviewers.
4. Finish V1.5 result acceptance and durable worker service/multi-host evidence.
5. Admit two exact zero-charge remote routes and run G12 remote overlap.
6. Complete V1.6/V1.7.
7. Complete V1.8/V1.9/V2.0 integration and real elapsed acceptance campaigns.

No main merge, public release/deploy or additional spend is authorized.
