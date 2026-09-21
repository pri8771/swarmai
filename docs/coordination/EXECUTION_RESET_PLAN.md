# SwarmAI execution reset plan — single-session revision

Status: ACTIVE
Date: 2026-09-21

Owner directive supersedes the earlier multi-lane reset plan.

## Current topology

Exactly one implementation session:

- Session: `CURSOR-V17-SINGLE`
- Branch: `cursor/v17-single-session`
- Goal: current truth -> V1.7 implementation-complete/reviewable candidate
- Heartbeat: one producer, every 5 minutes while session is active
- Parallel implementation lanes: none
- Legacy A/B autonomous assignments: disabled
- worker-pc: no new dispatch
- ChatGPT: downstream V1.6-V3.0 planning/architecture help, plus review when explicitly used; not a competing implementation lane

## Current execution contract

Read:
- `SINGLE_SESSION_V17_EXECUTION.md`
- `SINGLE_SESSION_HEARTBEAT.md`
- `CURSOR_V17_START.md`

## Execution order

1. Start one heartbeat producer and disable legacy local producers.
2. Reconcile donor branches and current canonical registry.
3. Close/implement remaining V1.3 qualification machinery.
4. Repair/rerun V1.4 real E2E materialization path.
5. Finish V1.5 durable result acceptance + worker service/harness.
6. Implement V1.6 scoped reusable knowledge.
7. Implement V1.7 unified tool/browser permission/effect boundary.
8. Push a final artifact-by-artifact V1.0-repair -> V1.7 evidence/blocker report.

No V1.8+ implementation without a new owner directive.

## Future preparation

ChatGPT planning work is stored in:
- `V16_TO_V30_FORWARD_PLAN_20260921.md`
- `V16_TO_V30_TASK_BACKLOG_20260921.md`

These are planning artifacts only and do not authorize later implementation or acceptance.
