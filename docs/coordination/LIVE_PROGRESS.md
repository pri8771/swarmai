# SwarmAI live progress

Updated: 2026-09-21T17:47:50Z

## Current operating model

Repository authority is the active single-session directive:

| Role | Identity | Scope |
|---|---|---|
| Implementation | `CURSOR-V17-SINGLE` | Current truth -> V1.7 implementation-complete/reviewable candidate |
| Heartbeat | `CURSOR-V17-SINGLE` | Exactly one 5-minute scheduled producer |
| Operator | owner | Final authority |
| ChatGPT | planning / coordination / independent review | No competing implementation lane |

Implementation branch: `cursor/v17-single-session`.
Legacy A/B assignments are disabled and their branches are donor/evidence branches only.

## Heartbeat

- Protocol: `SINGLE_SESSION_HEARTBEAT.md`.
- Epoch: `single-v17-20260921-01`.
- Current session heartbeat: **not registered / awaiting session start**.
- `cursor/v17-single-session` currently points to `9ce727842446b98cfa55c28c7e70808f57f17d7b`; exact-tip CI `35632562088` is green.
- Legacy publishers are still writing after supersession: HOST-MAC-DEV was observed at `2026-09-21T17:37:30Z`; HOST-WIN-DEV at `2026-09-21T17:28:46Z`. They are historical noise and do not count.
- Required startup correction: stop legacy A/B heartbeat/autonomous processes, start exactly one `CURSOR-V17-SINGLE` producer, publish `session_started`, then continue implementation.

## Current artifact truth

Canonical source is `ARTIFACT_REGISTRY.json`.

- `ART-V13-TASK-POOL` is **reviewable, not verified/frozen** in the canonical registry at `cursor/v2-product-lane@534476393257794c4e8ebf8d65f44fd090ab28eb`.
- Remaining G13 gate: actual HOST-WIN-DEV execution evidence for generator/verifier/Ruff/mypy/offline pytest, then independent lead freeze; sealed-reference content binding remains pending. W-131B counted qualification is prohibited.
- `STATE.json` currently overstates this artifact as verified/frozen and must be treated as stale derived state until reconciled to the registry.
- `ART-V14-REAL-E2E` remains incomplete: generic materialization repair + new genuine real mission required.
- V1.5 durable result acceptance and worker service/recovery evidence remain incomplete.
- G12 remote overlap remains blocked at 0 admitted remote routes.

## Background support

worker-pc task `swarmai-v13-task-pool-v3-audit-01` completed read-only against `534476393257794c4e8ebf8d65f44fd090ab28eb` at `2026-09-21T17:14:12Z`. It confirmed useful static fail-closed/sealed-reference properties, modified no SwarmAI code, and could not inspect CI or run project Python/pytest/ruff/mypy in the Claude sandbox. It does not change artifact acceptance.

No new worker-pc dispatch is authorized under the active single-session directive.

## Top next actions

1. Start `CURSOR-V17-SINGLE` from `CURSOR_V17_START.md`, stopping legacy A/B heartbeat/autonomous processes first.
2. Reconcile derived `STATE.json` against canonical `ARTIFACT_REGISTRY.json` before making G13 status claims.
3. Execute the single-session queue: G13 reviewer/qualification machinery with honest environment blockers, V1.4 materialization repair/rerun, then V1.5 durable result/worker work toward V1.7.

## Human action

Start exactly one Cursor implementation session using `docs/coordination/CURSOR_V17_START.md`. On that machine, disable/stop the old A/B SwarmAI heartbeat and autonomous-runner processes before registering the single-session heartbeat.

No main merge, public release/deploy, force push, or additional spend is authorized.
