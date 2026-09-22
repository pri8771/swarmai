# CP3 run cp3-20260922T013226Z — durable worker / result path (R17a)

- Source SHA (pushed, clean tree): `e5bd6350569fb10146517430ca6f7fa097de84a4`
- Mode: separate OS processes (`multiprocessing` spawn) sharing one real PostgreSQL database (`swarmai_v17_test`, disposable; the harness drops/creates schema).
- Result: **pass** — all nine requirements `demonstrated: true` (`receipt.json → requirements`).
- Spend: $0. Self-accept: false. Independent review: pending.

## What ran
1. victim worker (separate process) enrolls + claims → `SIGKILL` → `expire_leases` → survivor process re-claims the same task under a new lease and submits → zombie process (victim's stale credentials) submits and its accept is rejected (`lease_not_current:expired`) → survivor's result accepted → competing stale accept rejected → exactly one accepted row.
2. **cancellation_fence (new):** worker process claims; control plane bumps the durable mission `cancellation_generation`; worker submits → accept rejected `cancellation_generation_stale`; worker renew rejected `cancellation_generation_stale`; advisory `cancel_active_lease` applied afterwards → accept rejected `lease_not_current:cancelled`; zero accepted rows.
3. **concurrent_duplicate_accept (new):** 20 iterations; each: worker process submits two results on one lease; two acceptor processes race `accept_result` behind a `Barrier(2)`; exactly one accepted per iteration (winner PIDs listed in `receipt.json`).

## Finding (honest gap, not fixed here)
`LeaseLifecycleService.cancel_active_lease` cancels one lease but does not increment the mission's durable `cancellation_generation`, and no mission-cancel service method exists. The harness (acting as control plane) performed the durable bump directly. Follow-up: a small packet adding a mission-cancel method that bumps the generation before advisory lease cancellation.

## Not claimed
Physical multi-host evidence (`EXT-V15-SECOND-HOST`) remains external. CP3 "on a real operational mission" (delivery contract §5) needs the leased execution mode of `MissionRuntime` (R17b) — this run uses the durable worker service with harness-seeded tasks, not a mission produced by the product's mission path.
