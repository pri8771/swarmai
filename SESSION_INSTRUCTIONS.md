# SESSION_INSTRUCTIONS — Cursor Session A / HOST-MAC-DEV

This is the standing entrypoint for this Cursor session.
Role: runtime/control-plane/distributed workers/recovery/shared integration.
Working branch: `cursor/v2-runtime-lane`
Integration branch you own: `cursor/v2-integration`
Lead: ChatGPT via `coordination/swarm-control`.

## On every pull / continue
1. Preserve dirty work; never reset/clean unrelated work.
2. `git fetch --all --prune` and inspect `git status`, current branch and HEAD.
3. If clean: `git pull --ff-only origin cursor/v2-runtime-lane`.
4. Read fresh control state from `origin/coordination/swarm-control`:
   - `docs/coordination/HEARTBEAT_PROTOCOL.md`
   - `docs/coordination/HEARTBEAT_STATE.json`
   - `docs/coordination/ARTIFACT_REGISTRY.json`
   - `docs/coordination/WORK_QUEUE.md`
   - `docs/coordination/WORKER_PACKET_BACKLOG.md`
   - newest `docs/coordination/AGENT_MESSAGES.md`.
5. Newest coordination state overrides older prompt text.

## Heartbeat — required
Install/verify once: `bash scripts/coordination/install_heartbeat_macos.sh`.
Before a packet, publish context with:
`python3 scripts/coordination/heartbeat.py --host HOST-MAC-DEV --session A --branch cursor/v2-runtime-lane --packet <PACKET> --artifact <ARTIFACT> --status working --force`
After push/review request publish again with `--status review_requested`.
The scheduler wakes every 15 minutes during bootstrap and the client self-throttles to hourly only after the lead verifies three consecutive valid 15-minute heartbeats for BOTH active lanes.
Heartbeat is liveness/coordination only, not acceptance evidence.

## Current lead audit — V2A-003b-R still changes-required
Latest submitted source: `e764834a69315d1c2c85f00322c3392aa5037fd9`.
Evidence-binding tip before coordination-only heartbeat/session commits: `c6e0a8f0634eddc473fe66aa1d3cb55352dc25a6`.
Good work already present: current claim authority, dependency readiness, >32 pagination, project-scoped renew, renewable horizon cap, and cancelled-mission expiry handling.

Remaining A0-R2 findings:
1. `renew_lease()` must explicitly reject a terminal/incompatible task or attempt even when the mission remains runnable. Fence accepted/rejected/failed/cancelled/superseded task states and terminal/accepted attempt state.
2. Expiry must compare the lease/attempt stored task revision, source revision and cancellation generation to current durable authority before requeue. Current task-only expiry authority can miss source drift when TaskRow payload lacks the original source marker.
3. Add DB regressions: terminal task -> renew denied; terminal/accepted attempt -> renew denied; mission source/cancellation/revision changes after claim -> expired stale lease never returns task to ready; existing focused tests remain green.
4. Rebind evidence to the new source SHA and run exact-tip CI. Do not self-accept.

Artifact `ART-V15-LEASE-FENCING` stays drafting; V2A-003c result acceptance fencing is still required after this slice is lead-verified.

## Work while review waits
Do not idle. Next independent packet is `V2A-H6A-R / SP1`: owner-only compose secret-file permissions and safe fresh-config overwrite semantics; `--force` must not masquerade as safe credential rotation of an initialized DB.
If still waiting and no newer lead instruction, take `V2A-003X / SP2` isolated DBOS reuse spike only.
Do not start V2A-003c before lead verification unless a newer lead message says so.

## Continuous work rule
After every packet: push exact source/evidence, post CURSOR-A message, publish heartbeat `review_requested`, fetch coordination, and claim the next dependency-ready A packet.
Only lead-reviewed slices enter `cursor/v2-integration`; never bulk-merge the runtime lane.
No main merge/public release/deploy/paid fallback/force push/mock-success/invented acceptance.
