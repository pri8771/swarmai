# Execution handoff after planning closure

Use only after the closure revision has independent review and the active implementation worker is assigned the matching dependency-ready packet. Do not open all roadmap documents at startup.

```text
Continue pri8771/swarmai as the sole implementation worker named by canonical
coordination/swarm-control. Fetch and read CLAUDE.md, SESSION_START, your status,
heartbeat, current queue and relevant registry artifact. Inspect live source.

Use the current micro-packet queue. V1.7: V17_RECOVERY_PACKET_QUEUE.json + its
spec. V1.8–V2.3: V17_TO_V23_PACKET_QUEUE.json + the generated catalog card.
V3: FUTURE_EXECUTION_GRAPH_V18_TO_V30.json v30_packets + its catalog card.
Coarse phase aliases are not executable assignments.

Take one dependency-ready packet with satisfied entry gates. Read only that
packet, named interfaces and owned source. Implement bounded behavior, focused
negative tests, real evidence required by its gate; preserve failed attempts.
If actual source requires a different file/interface, make a narrow amendment
or split, not a broad new architecture plan. Do not self-waive a gate.

Commit/push source on the authorized implementation branch; retain exact
source/config/protocol identities, command results/skips and external blockers.
Update only your own permitted heartbeat/status through the canonical workflow.
Continue independent work when a human/elapsed gate blocks a claim.

No alternate scheduler, authority DB, permission engine, provider bypass,
static/in-memory operational fence or direct worker acceptance. No secrets,
paid fallback, public release, main merge or self-approval. Real-world proof is
required for working claims; fixtures and plan-validator tests are not that proof.

After each packet return ID/artifact, pushed SHA, owned files, tests/evidence,
claim dimensions, blockers and next packet. Independent review controls
verified/accepted. Keep campaign candidate deployments immutable while later
source advances. Finish at the assigned packet/version boundary and preserve
handoff, never invent missing evidence to advance a version.
```

Final architecture closure prompt is `FABLE_51_PLANNING_PROMPT.md`. It assigns planning only and does not dispatch this worker prompt.
