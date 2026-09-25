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
| TH-01 server compose | Containerized API+Postgres durable path | In Progress | TH-01, deploy | 3 |
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
