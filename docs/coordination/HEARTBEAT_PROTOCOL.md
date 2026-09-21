# SwarmAI coordination heartbeat protocol

Status: active
Owner: ChatGPT engineering lead
Active workers: Cursor Session A / HOST-MAC-DEV and Cursor Session B / HOST-WIN-DEV

## Purpose

The heartbeat is a coordination/liveness mechanism, not acceptance evidence.

A green heartbeat proves:
- the worker host/session lane can reach GitHub;
- its assigned branch has an observable remote SHA;
- it has fetched/referenced current coordination state;
- the durable coordination channel is alive.

A heartbeat does **not** prove:
- the foreground Cursor agent is continuously reasoning;
- a packet is correct;
- tests passed;
- an artifact is accepted;
- live model/provider evidence exists.

Meaningful work must still produce a CURSOR-A/B message with exact source/evidence SHA, tests and proposed artifact transition.

## Bootstrap cadence

Each active worker heartbeat scheduler runs every 15 minutes during bootstrap.

A worker heartbeat payload is structurally valid when it contains:
- host_alias
- session_id
- assigned branch
- current remote branch SHA
- current coordination branch SHA
- observed_at UTC
- current packet/artifact/status if known
- no fabricated work/acceptance fields

For the bootstrap cadence proof, ONLY heartbeats with `trigger = "scheduler"` count. Manual/install/working/review-request heartbeats are useful coordination events but do not advance the 15-minute streak.

A consecutive 15-minute scheduler heartbeat is one whose timestamp is 10–25 minutes after the prior counted scheduler heartbeat from the same session.

Required before graduation:
- HOST-MAC-DEV / Session A: 3 consecutive valid 15-minute heartbeats
- HOST-WIN-DEV / Session B: 3 consecutive valid 15-minute heartbeats
- ChatGPT lead observes/reconciles both histories in a scheduled review

Only after BOTH worker lanes satisfy the 3-heartbeat requirement may the lead set global mode to `hourly`.

## Lead cadence limitation

ChatGPT scheduled Automations cannot run more frequently than once per hour.

Therefore:
- worker/host heartbeats bootstrap at 15-minute effective cadence;
- ChatGPT lead review remains hourly;
- the hourly lead review inspects every heartbeat and commit since its prior run, so it can verify the full 15-minute history after the fact;
- do not claim that ChatGPT itself executed three 15-minute scheduled runs.

This is a platform scheduling limit, not a worker limitation.

## Scheduler independence

Manual/forced packet heartbeats must never reset or suppress the scheduler cadence clock. The heartbeat client keeps scheduler timing separately from work-status updates.

## Hourly graduation

Canonical state: `docs/coordination/HEARTBEAT_STATE.json`.

When the lead verifies 3 consecutive bootstrap heartbeats for both A and B:
1. set `mode = "hourly"`;
2. set `worker_effective_cadence_minutes = 60`;
3. record `graduated_at`;
4. record the exact heartbeat timestamps used for each session.

Worker OS schedulers may continue waking every 15 minutes, but the heartbeat client must self-throttle and publish only when the effective cadence is due. This avoids fragile scheduler rewrites while making the observable/check-in cadence hourly.

## Durable heartbeat files

- `docs/coordination/heartbeats/HOST-MAC-DEV.json`
- `docs/coordination/heartbeats/HOST-WIN-DEV.json`

Workers update only their own heartbeat file through GitHub's contents API / `gh api`. They do not git-checkout the coordination branch in their application worktree.

Each file keeps a small rolling history so missed/late heartbeats are auditable.

## Worker behavior

At session start:
1. fetch/pull assigned branch safely;
2. fetch `coordination/swarm-control`;
3. read `SESSION_INSTRUCTIONS.md` on the assigned branch;
4. read canonical registry/queue/backlog/new lead messages;
5. install/verify the local heartbeat scheduler;
6. publish a forced heartbeat with current packet/status.

Before starting a packet:
- publish heartbeat context `working` with packet + artifact.

After a meaningful push:
- publish heartbeat context `review_requested` or `working_next`;
- append CURSOR-A/B coordination message;
- immediately fetch current coordination state and continue the next dependency-ready packet unless blocked.

When blocked:
- heartbeat status `blocked`;
- record precise blocker;
- switch to another dependency-ready packet if available.

Do not stop merely because one artifact waits for lead review.

## Lead hourly loop

Every lead automation run:
1. fetch current A/B/integration refs and CI;
2. read both heartbeat histories;
3. validate cadence and update HEARTBEAT_STATE;
4. alert on stale heartbeat:
   - bootstrap mode: no valid heartbeat for >35 minutes
   - hourly mode: no valid heartbeat for >90 minutes
5. review every new CURSOR message/commit/evidence since the last lead run;
6. update ARTIFACT_REGISTRY first;
7. update worker performance from reviewed evidence only;
8. update queues / next packets;
9. keep >=3 dependency-ready SP1–SP3 packets per active lane when practical;
10. notify the operator of meaningful changes, review decisions, blockers, stale heartbeat or required human action.

## Notification semantics

Cursor cannot directly push an event into a currently idle ChatGPT conversation.

The durable notification path is:
Cursor heartbeat/commit/message -> GitHub coordination branch -> hourly ChatGPT lead automation -> operator notification/review.

This means notifications are durable and reviewed within the lead's hourly scheduling window, not guaranteed instant push notifications.

## Security

Heartbeat payloads must not contain:
- passwords/API keys/tokens/cookies;
- private browser/session state;
- raw environment dumps;
- sensitive URLs;
- personal identity mappings.

Only safe host alias, branch/SHA, packet/artifact/status and sanitized notes.
