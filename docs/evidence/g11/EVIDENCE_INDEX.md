# G11 / RUN-111 evidence index

**Tip binding:** `3b0011f0605573ab77318981691f588ac72f912f`  
**Lead accepted:** no  
**Spend:** $0 claimed in listed artifacts

| Artifact | Claim | Not claimed |
|----------|-------|-------------|
| `run-111/durable-identity-proof.json` | API/CLI share MissionStore IDs | Console browser E2E as sole proof |
| `run-111/three-missions.json` | 3 unfamiliar objectives across extract+triage; cancel | Full worker execution success |
| `run-111/accept-controls.json` | unsupported + wrong-output reject + independent accept | All families through console |
| `run-111/restart-reopen.json` | Service restart reopens durable IDs | Process-kill mid-task recovery |
| `run-111/local-ollama-mission.json` | Local mission attempt at $0 (may be failed honestly) | Fake success |
| `run-111/private-console.json` | Loopback console start notes | Public URL |
| `g11/default-path-not-parser.json` | Default inspect does not auto-select parser dogfood (re-verified on tip) | Full unfamiliar-task execution |

**Post–LEAD-009:** normal `swarm mission run` no longer hard-wires parser dogfood (`parser_dogfood_fixture` default false). Selfdev / `--fixture-parser-dogfood` remain explicit fixture paths.

**Residual for accept:** three unfamiliar tasks fully executed across two families via console+API+CLI on same IDs after G10 lead accept; no secondary demo executor.
