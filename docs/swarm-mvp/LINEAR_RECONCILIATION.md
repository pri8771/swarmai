# Linear reconciliation queue

**Date Recorded:** 2026-09-25  
**Status:** blocked — Linear MCP unavailable  
**Action:** update existing SwarmAI project/issues in place; do **not** create a duplicate project when access returns.

## Access problem

- Linear MCP namespace status: `needsAuth`
- `mcp_auth` call: authentication timed out
- No Linear issue IDs mutated this session

## Intended updates (when auth works)

| Issue / epic (find existing) | Summary | Status to set | Labels | Story points |
|---|---|---|---|---|
| SwarmAI MVP / two-host epic | Adopt R730+Mac topology; supersede local-only deploy | In Progress | swarm-mvp, two-host | 8 |
| P00 baseline | Freeze source/ownership/docs on `cursor/two-host-mvp-b28d` | In Progress | P00 | 2 |
| TH-01 server compose | Containerized API+Postgres durable path | Done (Mac eng) | TH-01, deploy | 3 |
| TH-02 native mission | Native worker completes mission on authoritative loopback path | Done (Mac eng) | TH-02, worker | 5 |
| TH-03 Mac connector | Mac connector completes mac_local scoped task through server | Done (Mac eng) | TH-03, connector | 3 |
| TH-04 durable artifacts | Content-addressed artifacts reopen identical sha256 after API restart | Done (Mac eng) | TH-04, artifacts | 3 |
| TH-05 mission UI | Console live mode shows real missions/artifacts/workers on loopback | Done (Mac eng) | TH-05, console | 3 |
| TH-06 runtime adapters | Qualify OpenCode/Hermes honestly; mark unqualified caps unavailable | Done (Mac eng) | TH-06, runtime | 3 |
| TH-07 synthetic eval harness | Graded starter suite + sealed answers; live gate blocked pending grant; no auto routing | Done (Mac eng) / review-required | TH-07, evals | 5 |
| R1–R9 foundation repairs | Close review blockers with protected regressions on `dev` lane | In Progress (R7 eng closed on `cursor/foundation-ci-c8a3`; R9 Linear + connector remain) | foundation, R1-R9 | 8 |
| R7 CI / ephemeral Postgres | Lint, typing, offline suites, console, PG integration job green | Done (hosted CI green on PR #50) | foundation, R7, ci | 3 |
| V1.7 complete the mission | Integrated lifecycle + protected verify + model-backed mission | Planned | V1.7 | 8 |
| V1.8 durable goals | Persistent Goal entity + pause/resume/cancel | Planned | V1.8 | 5 |
| V1.9 autonomous pursuit | Bounded pursuit loop + evaluated lessons | Planned | V1.9 | 8 |
| V2.0 integrated product | UI/SDK goal pursuit + acceptance campaign | Planned | V2.0 | 13 |
| Live qualification grant | Approve route+budget before live provider dispatch | Blocked | TH-07, live | 2 |
| R730 access gate | Verify SSH/OS/Docker/VM before host config | Blocked | infra | 1 |
| Cloudflare tunnel gate | Origin cert + authenticated routes for swarm.splitsignal.ai | Blocked | infra | 2 |

## Repo SoT while blocked

- `docs/swarm-mvp/STATE.md`
- `docs/swarm-mvp/PACKET_QUEUE.json`
- Project Context: `docs/two-host-implementation-plan.md`

## Do not

- Create a second Linear project named SwarmAI
- Invent issue keys
- Mark live qualification or operator acceptance complete without independent review
