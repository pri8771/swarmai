# SwarmAI coordination heartbeat protocol

Status: active
Owner: ChatGPT engineering lead
Active local workers: Cursor Session A / HOST-MAC-DEV and Cursor Session B / HOST-WIN-DEV

## Purpose

Heartbeat is coordination/liveness evidence only. It proves that the host/session lane can reach GitHub and publish its branch/coordination state. It does not prove task correctness, model evidence, CI success or artifact acceptance.

Only heartbeats with `trigger = "scheduler"` count for cadence qualification. Manual/install/work/review heartbeats are useful context but never advance a cadence streak.

## Active session epoch

The owner stopped all prior interactive lanes and started fresh sessions.

Current epoch: `reset-20260921-new-lanes-01`.

Old heartbeat ledger entries remain historical evidence only. They MUST NOT count toward the current heartbeat stress test.

A fresh lane becomes eligible for counting only after it explicitly registers the current epoch by publishing a manual/install heartbeat context containing:

- packet/artifact for its current assignment;
- status `session_started`;
- note containing `session_epoch=reset-20260921-new-lanes-01`.

Only scheduler heartbeats whose inherited session context comes from that registered fresh-session event count toward the current Phase-1 streak.

This prevents old background scheduler jobs from being mistaken for the new interactive lanes.

## Current owner-directed stress test — 2026-09-21

The previously verified hourly cadence is intentionally superseded for a fresh reliability exercise.

### Phase 1 — 5-minute burst proof

Both A and B publish at an effective **5-minute** cadence.

A counted heartbeat must:
- be scheduler-authored;
- carry the correct host/session/branch;
- carry observable branch SHA + coordination SHA;
- contain no fabricated work/acceptance fields.

A consecutive Phase-1 interval is **3–8 minutes** after the prior counted scheduler heartbeat.

Required:
- A: 3 consecutive counted scheduler heartbeats;
- B: 3 consecutive counted scheduler heartbeats.

The lead must verify both histories. ChatGPT scheduled automation remains hourly, so Phase-1 graduation may be recognized retrospectively on the next lead review; never claim ChatGPT itself checked every five minutes.

### Phase 2 — 24-hour 15-minute soak

After both A and B satisfy Phase 1, the lead sets:
- `mode = "soak_15m_24h"`;
- `worker_effective_cadence_minutes = 15`;
- `soak.started_at` to the transition time;
- `soak.ends_at` exactly 24 hours later.

During the soak:
- each worker publishes at effective 15-minute cadence;
- a normal consecutive interval is **10–25 minutes**;
- a gap >25 minutes is a missed interval and is preserved as evidence;
- host-unavailable events may be labeled with the real reason, but they still prevent a clean 24-hour success claim unless the owner explicitly waives/restarts the soak;
- manual heartbeats never substitute for scheduler receipts.

Success requires a complete real 24-hour observation window with no unresolved cadence miss for either required worker.

### After the 24-hour soak

Only after the lead verifies the full elapsed window may it restore the prior hourly effective cadence:
- `mode = "hourly"`;
- `worker_effective_cadence_minutes = 60`;
- record exact soak start/end and verification decision.

Do not backfill missed time.

## Scheduler strategy

The OS-level heartbeat schedulers wake every **5 minutes**. The heartbeat client reads `HEARTBEAT_STATE.json` and self-throttles to the current effective cadence:
- Phase 1: publish every 5m;
- Phase 2: publish every 15m;
- after soak verification: publish every 60m.

This avoids rewriting OS scheduler jobs at every phase transition.

Manual/forced packet updates use a separate clock and must never reset/suppress the scheduler cadence clock.

## Durable files

- `docs/coordination/HEARTBEAT_STATE.json`
- `docs/coordination/heartbeats/HOST-MAC-DEV.json`
- `docs/coordination/heartbeats/HOST-WIN-DEV.json`

Each worker updates only its own heartbeat ledger through GitHub API / authenticated `gh`.

## Worker session start

1. safely pull assigned branch;
2. read branch `SESSION_INSTRUCTIONS.md`;
3. fetch/read current coordination registry/state/queue/backlog/messages;
4. reinstall/verify the heartbeat scheduler from the current branch;
5. publish one install/manual context heartbeat;
6. continue assigned project work without waiting for heartbeat qualification.

Heartbeat testing must not block useful dependency-ready implementation.

## Lead review

Every lead automation run:
1. read both ledgers;
2. recompute the current phase and consecutive scheduler streaks;
3. transition Phase 1 -> Phase 2 only when both are verified;
4. during Phase 2 verify actual 15-minute history and elapsed wall clock;
5. notify on misses, stale host, phase transition, 24-hour success/failure or human action;
6. keep project work/reviews/assignments moving independently.

Stale thresholds:
- Phase 1 5m: >12 minutes;
- Phase 2 15m: >35 minutes;
- hourly: >90 minutes.

## Notification semantics

Durable path:
worker heartbeat/commit/message -> GitHub coordination -> hourly lead automation -> operator.

Notifications are durable but not guaranteed instant.

## Security

Never publish passwords, keys, tokens, cookies, private browser state, raw env dumps or private identity mappings. Heartbeats contain only sanitized host/session/branch/SHA/packet/artifact/status metadata.
