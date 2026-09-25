# SwarmAI MVP / two-host state

**Owner:** Cursor Project implementation worker (`bc-39c5759a-8fb4-514e-a825-98363e5fb28d`)  
**Branch:** `cursor/two-host-mvp-b28d`  
**Worktree:** `/Users/pchordia/Downloads/swarm-ai-two-host-mvp`  
**Base:** `origin/main` @ `08b910f981eff2ab66873a71055090f2c60f2a91`  
**Updated:** 2026-09-25T15:05:00Z  
**Public hostname:** `swarm.splitsignal.ai` (operator correction — never `.com`)

## Packet status

| Packet | Status | Notes |
|---|---|---|
| P00 | done (engineering) | Docs + baseline frozen; independent review not claimed |
| TH-01 | in progress | Mac compose verify **passed**; R730 placement **blocked** |
| P01–P19 | planned | Product queue unchanged |
| TH-02–TH-07 | planned | Next: native worker mission on authoritative path |

## Checks this session

| Check | Result |
|---|---|
| Hostname correction `.ai` | applied across repo + Project plan doc |
| Mac Docker/Compose server stack | pass — live/ready, DB up, volume durable, port 18765 |
| R730 SSH | **blocked** — unresolved |
| `swarm.splitsignal.ai` DNS | **blocked** — no A/AAAA |
| Cloudflare tunnel cert | **blocked** |
| Linear MCP | **blocked** — needsAuth |
| Deployment unit tests | pass (8) |

## Running locally (Mac verify)

```sh
docker compose -f deploy/compose/server.yml ps
curl -fsS http://127.0.0.1:18765/health/ready
# stop: docker compose -f deploy/compose/server.yml down   # keep volumes unless -v
```

## Next action

1. Operator: R730 SSH + Docker/VM facts.  
2. Operator: DNS + Cloudflare Access for `swarm.splitsignal.ai`.  
3. Linear auth for in-place issue updates.  
4. Worker: TH-02 native mission through authoritative API/worker path (still free/fake inference).
