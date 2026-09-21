# SwarmAI live progress

Updated: 2026-09-21T21:53:02Z

## Current operating model

| Role | Identity | Scope |
|---|---|---|
| Implementation | `CURSOR-V17-SINGLE` | Current truth -> V1.7 implementation-complete/reviewable candidate |
| Heartbeat | `CURSOR-V17-SINGLE` | Exactly one 5-minute scheduled producer |
| Operator | owner | Final authority |
| ChatGPT | planning / coordination / independent review | No competing implementation lane |

Implementation branch: `cursor/v17-single-session` @ `f2b8d5f7dfd65530e73c63438c229b9fa428f922`.
Legacy A/B assignment JSONs remain generation 7, disabled, with empty queues. Repository owner directive continues to supersede older two-lane reset text.

## Heartbeat

- Protocol: `SINGLE_SESSION_HEARTBEAT.md`; epoch `single-v17-20260921-01`; producer registered.
- Latest counted scheduler heartbeat observed: `2026-09-21T21:52:25Z` at branch SHA `f2b8d5f7dfd65530e73c63438c229b9fa428f922`.
- Status: `working`; current packet `R27`; current artifact `ART-V17-APPROVAL-BINDING`.
- Session remains fresh under the 12-minute stale threshold.
- Heartbeat is liveness/progress only and does not accept artifacts.

## Current review decisions

### ART-V14-REAL-E2E

`v14-real-007` remains **CHANGES REQUIRED**. The run proved real brokered local inference, material isolated-worktree output and no auto-apply, but did not demonstrate a defensible pre-patch correctness/reliability/security defect or a target regression proving repair. `ART-V14-REAL-E2E` stays `drafting`. Next attempt must be newly preregistered on a different bounded subsystem and prove an actual failing invariant/check before repair.

### V1.5 durable worker path

Useful local evidence remains retained without self-acceptance:

- R15 result-acceptance fence: `d3e1cd4035067abf30ce07093e7b0663f7f13ba9`; focused result-acceptance suite reports 10 passed.
- R16 durable worker protocol: `b683ed7a3ab755181fb0ffc69833c7b34638dab7`, bound by `f322672c24db3aae513c1b3301b005d4673419b6`; 18 focused tests reported.
- R17 recovery CP3: `cea12c622a44196b57bb8abe76b0ed83da1d97b6`, bound by `f5503d7d409096b773e8f86c7fe5cebba2c99800`; separate OS processes sharing Postgres demonstrated victim kill, expiry/reassignment, one accepted survivor result, and stale-result rejection.
- R18 records the actual second-physical-host blocker at `37fd070cf466127a194acd3e406fc8954a37868b`.

Canonical lifecycle is unchanged: `ART-V15-LEASE-FENCING` and `ART-V15-WORKER-PROTOCOL` remain `drafting`; `ART-V15-MULTIHOST-EVIDENCE` remains blocked.

### V1.6 / V1.7 implementation evidence

No new implementation commit landed since the previous lead run. Current retained tip is still `f2b8d5f7dfd65530e73c63438c229b9fa428f922`, with R19-R27 evidence already recorded. Next dependency-independent packet named by the session is R28 ToolGateway migration/verification.

## G13

- Canonical `ART-V13-TASK-POOL` remains `reviewable`, not verified/frozen.
- Actual HOST-WIN-DEV executable verification remains unsatisfied; Darwin/macOS verification cannot impersonate it.
- Real sealed-reference content digest remains unbound; counted qualification remains prohibited and qualified cells remain zero.
- worker-pc task `swarmai-v13-task-pool-v3-audit-01` remains read-only static support only; no new worker-pc dispatch under the current single-session owner directive.

## CI / blockers

- Exact-tip GitHub Actions run `35648897892` remains marked failure without usable runner execution evidence. Treat it as external Actions availability/billing non-evidence, not a source/test pass or failure.
- Human action: restore GitHub Actions availability only within the existing/no-additional-spend entitlement. Do not authorize new charges or raise a paid spending limit without separate approval.
- `ART-V14-REAL-E2E` remains drafting / changes required.
- G13 Windows executable verification + sealed-reference binding remain unresolved.
- G12 remote overlap remains at 0 admitted routes pending exact zero-charge admission and bounded canaries.
- V1.5 actual multi-host evidence still needs a second physical host.

## Top next actions

1. Continue R28 ToolGateway migration/verification or other dependency-independent single-session work while external blockers remain; do not create parallel implementation lanes.
2. Run a newly preregistered V14 real mission only after selecting a bounded subsystem with an objectively demonstrable pre-patch defect/invariant failure and target regression.
3. Preserve G13 counted qualification prohibition until the canonical Windows-verification and sealed-reference gates are legitimately satisfied.

## Human action

Restore GitHub Actions billing/spending-limit availability under existing/no-additional-spend entitlement. No main merge, public release/deploy, force push, or additional spend is authorized.

Latest lead record: `docs/coordination/messages/LEAD-20260921-041.md` (`2ffd087209533b604bb58960be260a709313c7ee`).