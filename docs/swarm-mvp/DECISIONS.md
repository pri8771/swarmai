# SwarmAI MVP decisions

## DEC-TH-004 — Synthetic harness before live qualification; no auto routing

| Field | Value |
|---|---|
| Decision ID | DEC-TH-004 |
| Topic | Evaluation / qualification gate |
| Decision Maker | Implementation worker per architecture §8 |
| Decision | Prepare and run the graded synthetic harness independently of live route/budget grants. Live dispatch stays blocked until an approved `LiveGrant`. Fixture/oracle results never auto-change production routing; ProfileStore updates from synthetic runs are ephemeral and `simulated=True`. |
| Context | TH-07; starter.jsonl 128 cases; R730/DNS/CF and provider grants unavailable |
| Options Considered | (1) wait for live grants before harness, (2) prepare harness + block live, (3) promote provisional routes from oracle scores |
| Why | Architecture §8: prepare harness independently; no universal best model; no auto production routing from few examples |
| Date Recorded | 2026-09-25 |
| Actual Start Date | 2026-09-25 |
| Actual End Date | 2026-09-25 |
| Status | accepted |
| Consequences | TH-07 Mac eng complete; live qualification remains blocked pending grant + dispatch wiring |
| Related Files | `src/swarm/evals/synthetic_harness.py`, `docs/evidence/two-host/TH-07/` |
| Related Prompt | TH-07 authorized continuation |
| Related Jira/Linear | pending — see `LINEAR_RECONCILIATION.md` |

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

## DEC-TH-003 — Runtime adapters require mediated qualification

| Field | Value |
|---|---|
| Decision ID | DEC-TH-003 |
| Topic | Optional OpenCode / Hermes runtimes |
| Decision Maker | Implementation worker per architecture mandate |
| Decision | Framework configuration alone does **not** enforce SwarmAI contracts. OpenCode/Hermes stay non-admissible until capability-by-capability SwarmAI kernel mediation is proven. Missing/unqualified capabilities are marked unavailable. Native remains default. |
| Context | TH-06 optional adapters; OpenCode binary present on Mac; Hermes not installed |
| Options Considered | (1) claim qualified from vendor config, (2) honest discovery + unavailable caps, (3) block all optional runtimes including native |
| Why | Architecture §6 and P16 stop conditions forbid false badges and contract weakening |
| Date Recorded | 2026-09-25 |
| Actual Start Date | 2026-09-25 |
| Actual End Date | 2026-09-25 |
| Status | accepted |
| Consequences | `GET /v1/runtimes` admits only `native` today; OpenCode=`discovered_unqualified`; Hermes=`unavailable` |
| Related Files | `src/swarm/runtime/adapters/`, `docs/evidence/two-host/TH-06/` |
| Related Prompt | TH-06 authorized continuation |
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

## DEC-V23-001: Owner pre-approvals for V2.3 (2026-09-26)

The owner approved these grants in chat on 2026-09-26. The full scope and
wording are recorded in `docs/plans/v2.3/OWNER_PREFLIGHT.md` on
`cursor/v23-plan-460c`.

- SW-PREAPPROVAL-A3: APPROVED 2026-09-26 (owner, chat) (SplitSignal live smoke; at most 2 chat calls, `max_tokens` 16, free route, $0, gated on SP4/SP5, joint live-call maximum 7)
- SW-PREAPPROVAL-A5: APPROVED 2026-09-26 (owner, chat) (multi-process/private-infrastructure evidence run; no provider/model calls, no deploy)
