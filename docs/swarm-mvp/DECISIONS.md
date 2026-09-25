# SwarmAI MVP decisions

## DEC-TH-001 — Two-host deployment topology

| Field | Value |
|---|---|
| Decision ID | DEC-TH-001 |
| Topic | Deployment architecture |
| Decision Maker | Operator via Project coordinator mandate |
| Decision | R730 always-on server; Mac connector worker; authenticated `swarm.splitsignal.ai`; Compose per host |
| Context | Planning bundle was local-only; hardware roles now specified |
| Options Considered | (1) local-only Mac, (2) two-host R730+Mac, (3) immediate cloud SaaS |
| Why | Always-on product without Mac dependency; keep cloud-ready contracts |
| Date Recorded | 2026-09-25 |
| Actual Start Date | 2026-09-25 |
| Status | accepted |
| Consequences | Supersedes local-only deploy scope; R730/CF access become gates |
| Related Files | `ADR-002-two-host-architecture.md`, `deploy/compose/server.yml`, `deploy/compose/mac-connector.yml` |
| Related Prompt | two-host-architecture-update |
| Related Jira/Linear | pending — see `LINEAR_RECONCILIATION.md` |

## DEC-TH-002 — Parallel lane vs V1.7

| Field | Value |
|---|---|
| Decision ID | DEC-TH-002 |
| Topic | Ownership / branching |
| Decision Maker | Implementation worker (per mandate: do not overwrite other worker) |
| Decision | Use isolated branch/worktree `cursor/two-host-mvp-b28d`; leave `cursor/v17-single-session` and CURSOR-V17-SINGLE heartbeat untouched |
| Context | Coordination ASSIGNED_WAITING_FOR_WORKER (GPT-6 Sol) for V1.7; Project mandates two-host MVP |
| Options Considered | (1) hijack V1.7 branch, (2) wait for V1.7 acceptance, (3) parallel lane |
| Why | Continue authorized work without overwriting another owner’s scope |
| Date Recorded | 2026-09-25 |
| Status | accepted |
| Related Files | `STATE.md`, `SOURCE_BASELINE.json` |
