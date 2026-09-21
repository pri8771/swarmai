# SwarmAI single-session heartbeat protocol

Status: ACTIVE OWNER DIRECTIVE
Date: 2026-09-21
Session: `CURSOR-V17-SINGLE`
Implementation branch: `cursor/v17-single-session`

This supersedes the old A/B heartbeat stress/soak topology for current work.

## Rule

ONE active Cursor implementation session.
ONE scheduled heartbeat producer.
ONE heartbeat stream.
No lead heartbeat automation.
No second worker heartbeat.
No 24-hour two-lane soak requirement for this execution model.

Heartbeat is liveness/progress evidence only. It does not accept code or artifacts.

## Cadence

While the Cursor implementation session is active:
- scheduler wakes every 5 minutes;
- at most one scheduled heartbeat is published per 5-minute interval;
- manual status updates may be written when meaningful, but they are not a second scheduler/producers;
- if work is still ongoing, heartbeat must still say what is happening even when no code was pushed.

If the session is intentionally stopped, heartbeat may stop.

## Canonical heartbeat files

- machine-readable ledger: `docs/coordination/heartbeats/CURSOR-V17-SINGLE.json`
- human status: `docs/coordination/status/CURSOR-V17-SINGLE.md`

Each scheduled heartbeat updates BOTH as one logical heartbeat.

Do not update old HOST-MAC-DEV/HOST-WIN-DEV ledgers for current execution.

## Required fields

Machine-readable heartbeat should include:
- schema_version;
- session_id = CURSOR-V17-SINGLE;
- session_epoch;
- branch;
- branch_sha;
- coordination_sha if known;
- timestamp_utc;
- trigger = scheduler;
- status = session_started|working|testing|review_requested|blocked|stopped;
- current_packet;
- current_artifact;
- short_note;
- last_meaningful_activity_at;
- blocker if any;
- spend_usd known for this work, default 0 only when actually known;
- no secrets/private identity.

Human status should show:
- current packet/artifact;
- current status;
- branch SHA;
- what changed since prior heartbeat;
- if no change: "still working on <specific thing>";
- tests/checks currently running or last result;
- blocker/human action if any;
- next immediate action.

## Exactly-one producer startup

At session start:

1. Detect/stop legacy SwarmAI heartbeat schedulers on this machine that target A/B or the same repo.
2. Detect duplicate current-session heartbeat processes.
3. Acquire a local single-instance lock/PID guard.
4. Install/start one scheduler process only.
5. Publish a session_started heartbeat.
6. Continue implementation immediately; heartbeat qualification does not block work.

A duplicate producer is a coordination defect. Fail closed: keep one, stop the others, record the correction.

## Repository write behavior

Heartbeat writes must be narrow:
- only the two canonical single-session heartbeat/status files plus necessary heartbeat metadata;
- no source-code mutation;
- no artifact acceptance transitions;
- no generated secrets/log dumps.

Avoid triggering unnecessary CI for heartbeat-only coordination updates if repository workflow filters support that.

## Failure semantics

If heartbeat publish fails:
- implementation may continue locally;
- retry at the next cadence;
- record the real publish error;
- do not backfill fake historical timestamps.

If the session is blocked:
- heartbeat continues every 5 minutes while the session remains active;
- status must name the blocker and the exact human/external action needed.

## Security

Never publish:
- API keys/tokens;
- cookies/session blobs;
- passwords;
- private env dumps;
- raw private identity mappings;
- hidden held-out answers.
