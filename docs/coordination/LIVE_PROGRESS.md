# SwarmAI live progress

This page is the human-readable project dashboard. Worker heartbeat pages update on every scheduler heartbeat; the lead refreshes this summary on each lead review.

## Current execution topology

| Lane | Owner | Scope | Status |
|---|---|---|---|
| A | HOST-MAC-DEV / Cursor | runtime, real V1.4 proof, durable worker/result fencing, integration | reset / fresh-session start |
| B | HOST-WIN-DEV / Cursor | product/evaluation, reviewer qualification, knowledge/tools | reset / fresh-session start |
| C | worker-pc / Claude via remote-workers | independent G13 corpus/evidence work and bounded review/fix tasks | remote-worker controlled |
| Lead | ChatGPT | architecture, independent review, assignment, acceptance, integration decisions | active |

## Heartbeat stress test

Phase 1: 5-minute effective cadence, 3 consecutive scheduler heartbeats required from A and B.  
Phase 2: 15-minute cadence for 24 real hours.  
After verified soak: hourly cadence.

See:
- `docs/coordination/status/HOST-MAC-DEV.md`
- `docs/coordination/status/HOST-WIN-DEV.md`
- `docs/coordination/HEARTBEAT_STATE.json`

## Current critical path

1. Prove autonomous repo-driven execution on A and B.
2. Pass one genuine V1.4 real end-to-end mission.
3. Freeze G13 task pool with real independent semantic depth, then qualify models/reviewers.
4. Finish V1.5 durable result acceptance + worker service.
5. Admit two zero-charge remote inference routes for G12 remote overlap.
6. Continue V1.6/V1.7, then V1.8/V1.9/V2.0 integration and acceptance.

No main merge, public release/deploy or additional spend is authorized.
