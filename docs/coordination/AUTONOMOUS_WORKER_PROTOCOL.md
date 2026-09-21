# SwarmAI repo-driven autonomous worker protocol

Status: active design / bootstrap
Owner: ChatGPT engineering lead
Active workers: HOST-MAC-DEV / A and HOST-WIN-DEV / B

## Goal

Turn each active Cursor lane into a self-waking bounded executor driven by GitHub coordination state.

Repo assignment update -> local daemon notices -> Cursor CLI `agent -p` executes exactly one bounded packet -> worker pushes evidence -> lead reviews -> lead updates assignment -> loop.

Cursor's CLI supports non-interactive automation. Each worker still uses its existing dedicated application branch; the daemon does not create an unbounded swarm by itself.

## Canonical assignments

- `docs/coordination/assignments/HOST-MAC-DEV.json`
- `docs/coordination/assignments/HOST-WIN-DEV.json`

Only ChatGPT lead / operator coordination should advance assignment generation.

## Assignment identity

Every assignment has:
- assignment_id
- generation
- enabled
- host/session/branch
- packet_id
- artifact_id
- instruction_path and/or queue source
- max_runtime_seconds
- zero-spend / no-main-merge / no-public-deploy boundaries

The daemon executes each `(assignment_id, generation)` at most once. To retry after a failed or blocked run, the lead increments generation or creates a new assignment.

## Worker loop

1. Poll the canonical assignment file.
2. If disabled or already completed, do nothing.
3. Acquire a local single-instance lock.
4. Require the assigned worktree to be clean; never reset/clean/stash destructively.
5. Fetch and fast-forward only the assigned worker branch plus coordination refs.
6. Read `SESSION_INSTRUCTIONS.md` and current coordination state.
7. Publish autonomous-start heartbeat context.
8. Invoke Cursor CLI non-interactively for exactly one assignment.
9. Cursor agent must implement/test/commit/push only its owned packet and must not self-accept.
10. Publish autonomous-finished or blocked heartbeat context.
11. Wait for a new assignment generation.

## Safety / authority

- no main merge or release tag;
- no public deploy;
- no paid fallback/additional spend;
- no force push;
- no destructive clean/reset of unrelated work;
- no secret values in logs, commits or heartbeat notes;
- no self-acceptance;
- no changing frozen acceptance thresholds after results;
- no executing a second packet just because the first completed early;
- human-only MFA/login/consent produces a blocker and returns control to the lead/operator.

## Concurrency

Default: one autonomous runner per active branch/host. A local lock prevents overlap.

Current intended topology:
- A = runtime/control-plane/integration
- B = evaluation/product/knowledge/tools
- ChatGPT = planner/reviewer/assignment scheduler

A third autonomous implementation lane is not enabled by default. Add one only when the review/integration queue is healthy and there is a genuinely independent bottleneck.

## Heartbeat relationship

Heartbeat proves liveness; autonomous runner proves bounded execution. They are separate.

The runner uses the same heartbeat client for `autonomous_start`, `autonomous_finished` and `blocked` context, but only scheduler-authored heartbeats count toward cadence proof.

## Authentication

Cursor CLI must be installed and authenticated on the host (`agent login` or an already-authorized API-key mechanism). The daemon never stores credentials in Git.

If CLI authentication is absent, mark blocked and request only the exact human login step.

## Review loop

Lead automation reviews new worker commits/evidence, updates ARTIFACT_REGISTRY first, and then advances that host's assignment generation to the next dependency-ready packet.

This creates continuous execution without giving the worker authority to choose project priorities or accept its own work.
