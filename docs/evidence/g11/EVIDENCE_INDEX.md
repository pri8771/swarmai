# G11 / RUN-111 evidence index

**Tip binding:** (see latest commit on `cursor/v1.4-live-integration-11e2`)  
**Lead accepted:** no (do not invent)  
**Spend:** $0 claimed in listed artifacts

| Artifact | Claim | Not claimed |
|----------|-------|-------------|
| `run-111/durable-identity-proof.json` | API/CLI share MissionStore IDs | Console browser E2E as sole proof |
| `run-111/three-missions.json` | 3 unfamiliar objectives across extract+triage; cancel | Full worker execution success (superseded by multisurface) |
| `run-111/accept-controls.json` | unsupported + wrong-output reject + independent accept | All families through console UI click-path |
| `run-111/restart-reopen.json` | Service restart reopens durable IDs | Process-kill mid-task recovery |
| `run-111/local-ollama-mission.json` | Local mission attempt at $0 (may be failed honestly) | Fake success |
| `run-111/private-console.json` | Loopback console start notes | Public URL |
| `g11/default-path-not-parser.json` | Default inspect does not auto-select parser dogfood | — |
| `g11/multisurface-three-tasks.json` | **Residual closed:** 3 unfamiliar extract+triage tasks; console-shaped create + API execute + CLI execute/report on same durable IDs; real Ollama; honest pass; $0 | G10 lead accept; browser Playwright E2E; paid providers |

**Post–LEAD-009:** normal `swarm mission run` no longer hard-wires parser dogfood (`parser_dogfood_fixture` default false). Selfdev / `--fixture-parser-dogfood` remain explicit fixture paths.

**Post–LEAD-010 residual:** three unfamiliar tasks fully executed across extract+triage via console create shape + API + CLI on same IDs — evidenced in `multisurface-three-tasks.json` (3/3 completed, $0, `invented_success: false`). G10 lead accept still **not** invented.
