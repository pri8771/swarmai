# Linear reconciliation queue

**Date Recorded:** 2026-09-25  
**Updated:** 2026-09-25T21:10Z (FAST_TRACK L1–L6 eng_landed; tip `dd7726eb`; CandidateManifest rebound)  
**Status:** blocked — Linear MCP unavailable (`needsAuth`)  
**Action:** update existing SwarmAI project/issues in place; do **not** create a duplicate project when access returns.  
**Versions:** V1.7–V2.0 remain **unaccepted** in repo tracking regardless of Linear status.  
**Repo tip SoT:** `origin/dev` @ `dd7726eb8c22986ef72847994c8e435a81a869b6`

## Access problem

- Linear MCP namespace status: `needsAuth`
- `mcp_auth` not invoked this pass (queue-only policy while needsAuth)
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
| V1.7 complete the mission | Integrated lifecycle + protected verify + model-backed mission | Eng present — **not accepted** | V1.7 | 8 |
| V1.8 durable goals | Persistent Goal entity + pause/resume/cancel/restart/dedupe + protected tests | Eng complete — **not accepted** | V1.8 | 5 |
| V1.9 autonomous pursuit | Bounded pursuit loop + evaluated lessons | Eng complete — **not accepted** | V1.9 | 8 |
| V2.0 integrated product | UI/SDK goal pursuit + acceptance campaign | Eng present — **not accepted** | V2.0 | 13 |
| V2.0 acceptance campaign freeze (Lane F) | Freeze §10 scenarios/pass criteria; harness + matrices; no version accept; no invented LiveGrant | Done (eng freeze/harness) — versions still not accepted | V2.0, acceptance | 5 |
| **PORT-01 portable defects** | Configurable freeze hostname; connector executes assigned work; harness auth vs impl | **Done** (PR #55 merged; Mac verify PASS) | portable, PORT-01, P1, gate:product | 5 |
| **PORT-02 generic roles** | Server/worker/combined roles; enrollment contracts; support matrix; generic connector | **Done (eng)** (PR #57); matrix cells stay experimental — not `supported` | portable, PORT-02, P2, gate:product | 8 |
| **PORT-03 portable install** | Fresh-install example; runbooks; R730/Mac/CF as reference only | **Done (eng)** (PR #56); particular-deploy evidence external | portable, PORT-03, P3, gate:product | 5 |
| **PORT-04 portability tests** | Multi-config probes + two-container protocol proof | **Done (eng)** (PR #54); Mac Docker proof green | portable, PORT-04, P4, gate:product | 5 |
| **PORT-05 portable tracking** | Plan / packet graph / support matrix / this Linear queue | **Done (eng)** tip-sync @ `dd7726eb` (V20-E01); continuous | portable, PORT-05, P5 | 2 |
| **FAST_TRACK L1–L6** | Durable storage, pursuit, workers, memory, verify, UI/SDK | **Eng landed** on tip (#61/#63/#62/#64/#65/#60) — not version-accepted | fast-track, L1-L6, gate:product | 13 |
| **V2.0 eng depth E03–E06** | PG write-through, ledger durability, native model/tool loop, coordinator | Todo / eng gap | V2.0, gate:product | 13 |
| Live qualification grant | Approve route+budget before live provider dispatch | Blocked — **live gate**, not product eng stop | TH-07, live, gate:live | 2 |
| Live adapter dispatch (impl) | Optional dispatcher / qualification runner after approved grant | Todo / eng gap — label `blocked_missing_implementation` | portable, gate:product | 5 |
| R730 access gate | Verify SSH/OS/Docker/VM before host config | Blocked — **deployment gate** | infra, gate:deployment | 1 |
| Cloudflare tunnel gate | Origin cert + authenticated routes for swarm.splitsignal.ai | Blocked — **deployment gate** | infra, gate:deployment | 2 |

## Gate labels (apply when creating/updating)

| Label | Meaning |
|---|---|
| `gate:product` | Product correctness — eng must close |
| `gate:platform` | Supported-platform qualification |
| `gate:deployment` | Particular deployment (R730/CF) — does not block generic eng |
| `gate:live` | Live inference / LiveGrant |
| `gate:review` | Independent review |
| `gate:operator` | Operator acceptance |

## Repo SoT while blocked

- `docs/swarm-mvp/STATE.md`
- `docs/swarm-mvp/PACKET_QUEUE.json`
- `docs/swarm-mvp/EXECUTION_MAP.md`
- `docs/swarm-mvp/PORTABLE_SUPPORT_MATRIX.md`
- `docs/evidence/v20/support_matrix.json`
- Project Context: `docs/v2-portable-product-plan.md` (+ prior `docs/v2-goal-pursuit-plan.md`)
- Post-merge verify: Project Context `internal/v2-portable-post-merge-verify-handoff.md`

## Do not

- Create a second Linear project named SwarmAI
- Invent issue keys
- Mark live qualification or operator acceptance complete without independent review
- Mark V1.7–V2.0 accepted from eng green alone
- Treat missing R730/CF/LiveGrant as blocking portable eng (PORT-01–04 already landed)
- Claim Linux container / enrollment cells `supported` without qualification + review
