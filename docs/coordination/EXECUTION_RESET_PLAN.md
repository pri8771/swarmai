# SwarmAI execution reset plan — 2026-09-21

## Objective

Maximize useful parallel throughput while reducing coordination churn.

Three execution lanes only:
- A Mac runtime/acceptance;
- B Windows product/evaluation;
- C worker-pc independent audit/support;
plus ChatGPT lead.

## Phase 0 — execution reset and visibility

1. Start fresh A and B Cursor sessions from their canonical branches.
2. Each reads branch SESSION_INSTRUCTIONS + current coordination state.
3. Reinstall current 5-minute heartbeat scheduler.
4. Reinstall/verify autonomous worker daemon.
5. Before meaningful work, publish heartbeat context naming current packet/artifact.
6. Human-readable host status page must update on every scheduler heartbeat.
7. Lead dashboard `LIVE_PROGRESS.md` refreshes at each hourly lead review.

Success:
- A and B each 3/3 scheduler receipts at 5m cadence.
- Then lead starts 24h 15m soak.
- No need to stop code work while heartbeat test runs.

## Phase 1 — close immediate V1.4/V1.5 critical path

### Lane A
A1. V14-REAL-001-R
- repair generic model-output -> isolated-worktree materialization;
- deterministic unrelated regressions;
- new preregistered real local brokered mission on a different subsystem;
- actual material diff + actual test/check + review boundary;
- no known answer/fallback.

A2. V2A-003c
- durable result acceptance;
- generation/project/lease/task/source/revision/cancellation fences;
- duplicate/race exactly-one semantics.

Lead reviews A1/A2 independently.

After A2 acceptance:
A3. reviewed-slice integration receipt;
A4. V2A-004 durable worker service/client;
A5. real multi-host worker proof.

### Lane B
B0. propagate accepted autonomous-runner repair and validate Windows coordination tests.
B1. sync reviewed integration baseline.
B2. take final ownership of ART-V13-TASK-POOL:
- use worker-pc retry06 only as defect evidence/reference;
- re-mint at least 15 genuinely independent semantic archetypes per required family x size cell;
- add explicit semantic-archetype/scenario-substitution/prefix-containment checks;
- no hidden answers on worker-visible branch;
- run generator/verifier/pytest/ruff/mypy locally;
- freeze exact digests/versions/provenance;
- request lead freeze.

B3. reviewer calibration/freeze.
After lead freezes B2:
B4. counted held-out qualification in 5-observation batches.
After reviewer design freeze:
B5. reviewer-role held-out qualification.

Then continue V16/V17.

### Lane C — worker-pc
Use only when independent useful work exists:
- review A/B pushed branches;
- inspect artifacts for scope/evidence/truth defects;
- generate non-executable benchmark/evidence improvements;
- branch fixes only if required verification is possible elsewhere and clearly handed off.
Lead dispatches automatically; user does not manually manage this lane.

## Phase 2 — close G12 remote

In parallel after A1/A2 pressure reduces:
- verify exact free-tier status for at least two remote providers/routes;
- exact model IDs and zero-price eligibility;
- bounded zero-charge canaries;
- fail-closed no-paid fallback;
- run actual overlapping governed calls + reconciliation.

No remote route is admitted from public docs/auth metadata alone.

## Phase 3 — V1.6/V1.7

B:
- V16 provenance -> permission-first retrieval -> supersession/context budget.
- V17 approval binding -> integration manifest -> session recovery -> permission negatives.

A:
- shared schema/integration deltas only after review.
- continue durable worker/recovery foundation.

## Phase 4 — V1.8/V1.9/V2.0

A:
- site epoch;
- backup/restore/reconcile;
- split-brain/outage drills.

B/C:
- install/beta/extensions/selfdev evidence;
- external clean installs;
- security/performance support.

Lead:
- integrate reviewed artifact set;
- freeze V2 candidate;
- start real 7-day reliability campaign;
- final security/performance/release review.

## Automation contract

### Local A/B
Assignment JSON is executable queue.
Daemon:
- polls every minute;
- executes one bounded packet at a time;
- commits/pushes;
- publishes working/review_requested/blocked context;
- never self-selects new priorities;
- never self-accepts.

### Heartbeat updates
Every scheduler heartbeat writes:
- JSON ledger;
- human-readable host status markdown.

The status update must say at minimum:
- current packet/artifact;
- working/review_requested/blocked;
- branch SHA;
- last agent activity;
- short note such as "still working on V14 materialization repair".

### Lead automation
Every hour:
- recompute heartbeat phase;
- update LIVE_PROGRESS.md;
- review every new A/B/worker-pc result;
- update ARTIFACT_REGISTRY first;
- issue new assignment generations;
- dispatch worker-pc when useful/idle;
- notify user on meaningful change or blocker.

## Lane-count policy

Stay at 3 execution lanes until all are true:
- autonomous A/B self-launch proven;
- lead review backlog <2 packets;
- no integration conflicts;
- each lane has independent dependency-ready work.

Only then consider a fourth verifier lane.
