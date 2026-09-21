# SwarmAI session start router

This is the compact entry point for every Claude/Fable/agent session.

## 1. Current execution truth

Repository: `pri8771/swarmai`

Canonical coordination branch:
`coordination/swarm-control`

Current implementation branch:
`cursor/v17-single-session`

Current implementation worker/session:
`CURSOR-V17-SINGLE`

Current topology:
- ONE implementation session
- ONE heartbeat producer
- ChatGPT lead/reviewer
- operator final authority

Current target:
Reach a V1.7 implementation-complete, live-checkpointed candidate first. Then follow the already-prepared V1.8 -> V2.3 -> V3.0 DAGs.

## 2. Always read these small live files

Current status:
`docs/coordination/status/CURSOR-V17-SINGLE.md`

Heartbeat:
`docs/coordination/heartbeats/CURSOR-V17-SINGLE.json`

Current V1.7 queue:
`docs/coordination/V17_RECOVERY_PACKET_QUEUE.json`

Canonical artifact truth:
`docs/coordination/ARTIFACT_REGISTRY.json`

The heartbeat/status is freshest for worker liveness/current packet.
The artifact registry is authoritative for artifact state.
If they conflict, do not guess: report the discrepancy.

## 3. Current recovery contract

Detailed current plan:
`docs/coordination/V17_RECOVERY_PLAN_ARTIFACT_FIRST.md`

Live checkpoint protocol:
`docs/coordination/V17_LIVE_CHECKPOINT_PROTOCOL.md`

Latest serious code audit:
`docs/coordination/V17_CODE_AUDIT_20260921_1432.md`

Read these only when the current packet needs them; do not reread all three every turn.

## 4. Active packet routing

From `V17_RECOVERY_PACKET_QUEUE.json`:
1. find the current/incomplete dependency-ready packet;
2. read its artifact ID;
3. use `docs/coordination/DOC_ROUTER.md` to locate only relevant contracts/evidence;
4. inspect live source before coding.

Packet execution rule:
one small packet -> focused tests -> commit -> push -> heartbeat -> next ready packet.

## 5. Future routing

After the V1.7 authorized handoff:
- V1.8–V2.3: `docs/coordination/V17_TO_V23_PACKET_QUEUE.json`
- V1.8–V2.3 architecture: `docs/coordination/V17_TO_V23_CEMENTED_EXECUTION_PLAN.md`
- V3 preparation/execution DAG: `docs/coordination/FUTURE_EXECUTION_GRAPH_V18_TO_V30.json`
- future prep index: `docs/coordination/FUTURE_PREP_INDEX_20260921.md`

Do NOT open all future planning files at startup.

## 6. Current known blockers / caveats

Always verify live before repeating:
- GitHub Actions billing/startup has been a USER_ACTION blocker.
- External provider credentials/entitlements may block remote evidence.
- Some physical multi-host/Windows/wall-clock evidence may remain externally gated.
- Blocked external evidence must not idle dependency-independent implementation.

## 7. Memory/context

Check relevant past conversation/memory when available to recover product intent and prior decisions.
Never use memory as proof of current implementation or acceptance.

## 8. End-of-packet update

Every packet handoff should be concise:
- packet/artifact
- source SHA
- files changed
- tests/evidence
- blockers
- next packet
- no acceptance claim unless independently reviewed
