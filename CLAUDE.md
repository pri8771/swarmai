# SwarmAI — Claude/Fable bootstrap

You are working in the SwarmAI implementation tree.

Stable project/agent instructions and live coordination are maintained on:
`coordination/swarm-control`

At session start:

```bash
git fetch origin coordination/swarm-control
git show origin/coordination/swarm-control:CLAUDE.md
git show origin/coordination/swarm-control:docs/coordination/SESSION_START.md
```

Then read only the live status/heartbeat, active machine-readable packet, and artifact docs routed by:
`docs/coordination/DOC_ROUTER.md` on the coordination branch.

Rules:
- GitHub/current source is truth; memory/past chats are context.
- ChatGPT = engineering lead/acceptance reviewer.
- Claude/Fable = worker/planner as assigned.
- One implementation worker and one heartbeat producer unless operator changes topology.
- Artifact-oriented tiny packets; focused tests; commit/push/heartbeat.
- Never self-accept.
- Mocks do not count as required live evidence.
- Preserve failures.
- No main merge/public deploy/paid fallback/destructive production action without explicit operator authorization.
- Default `SWARM_ALLOW_PAID=false`.
- Reuse existing SwarmAI infrastructure before adding frameworks.
- Do not load the full V3 planning corpus unless the active packet requires it.
