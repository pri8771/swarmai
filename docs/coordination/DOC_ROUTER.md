# SwarmAI documentation router

Use this file to avoid loading the entire planning corpus.

## Always-small/current
- Session bootstrap: `SESSION_START.md`
- Canonical artifact states: `ARTIFACT_REGISTRY.json`
- Active V1.7 queue: `V17_RECOVERY_PACKET_QUEUE.json`
- Worker status: `status/CURSOR-V17-SINGLE.md`
- Heartbeat: `heartbeats/CURSOR-V17-SINGLE.json`

## V1.3 / qualification packets
Read only when packet artifact is ART-V13-*:
- `EVAL_131_QUALIFICATION_PROTOCOL.md`
- `G13_SEALED_REFERENCE_BINDING_PROTOCOL.md`
- relevant ART-V13 entries in registry
- current G13 evidence/donor source named by packet

## V1.4 / real/adaptive packets
For ART-V14-REAL-E2E:
- `REAL_V14_E2E_PROTOCOL.md`
- latest lead review in `reviews/`
For LIVE-142:
- `LIVE_142_CAMPAIGN_PROTOCOL.md`
For adaptive/role artifacts:
- relevant registry entry and current evidence only

## V1.5 / durable workers
For ART-V15-*:
- future/current V1.5 artifact contract named in registry
- donor commit refs in `V17_RECOVERY_PLAN_ARTIFACT_FIRST.md`
- relevant worker/lease/result source/tests
Do not read legacy A/B coordination docs.

## V1.6 / knowledge
For ART-V16-*:
- `docs/artifacts/future/ART-V16-*.md`
- relevant memory/knowledge source/tests
Key invariant: permission filter BEFORE ranking/context assembly.

## V1.7 / actions/tools/session
For ART-V17-*:
- `docs/artifacts/future/ART-V17-*.md`
- relevant ToolGateway/contracts/adapters/session source/tests
Key invariant: durable approval/effect boundary; process-local idempotency is insufficient.

## V1.8–V2.3
After V1.7 handoff:
- packet DAG: `V17_TO_V23_PACKET_QUEUE.json`
- architecture only when needed: `V17_TO_V23_CEMENTED_EXECUTION_PLAN.md`
- live gates: `V17_TO_V23_LIVE_CHECKPOINTS.md`

## V3.0
Only when V3 work is dependency-ready:
- execution DAG: `FUTURE_EXECUTION_GRAPH_V18_TO_V30.json`
- prep index: `FUTURE_PREP_INDEX_20260921.md`
Then open only the specific V30 artifact contract + schema/test/evidence files referenced by that packet.

## Architecture/reference lookups
Open only on demand:
- `FUTURE_SCHEMA_CONTRACTS_V18_TO_V30_20260921.md`
- `FUTURE_TRANSACTION_ALGORITHMS_V18_TO_V30_20260921.md`
- `FUTURE_TEST_EVIDENCE_MATRIX_V18_TO_V30_20260921.md`
- `FUTURE_ACCEPTANCE_CASE_IDS_20260921.md`
- `FUTURE_OPEN_DECISIONS_FREEZE_POINTS_20260921.md`
- `FUTURE_INFRA_REUSE_DECISIONS_20260921.md`

## Rule
If a large doc is unchanged and the active packet does not depend on it, do not reread it.
