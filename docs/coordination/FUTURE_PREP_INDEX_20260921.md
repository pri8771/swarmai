# SwarmAI future-prep index — V1.8 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY
Current implementation session remains scoped through V1.7.

Purpose: remove future worker ambiguity without changing current execution, acceptance state, release authority, spend authority, or main-merge authority.

## Prepared planning set

1. `MASTER_PLAN_V17_TO_V30_20260921.md`
   - end-to-end product sequence from the V1.7 core-platform milestone through V3.0.

2. `DEPENDENCY_GRAPH_V17_TO_V30_20260921.md`
   - hard/soft dependencies, critical path, and what can be prepared in parallel.

3. `FUTURE_CODE_MAP_V18_TO_V30_20260921.md`
   - maps each future artifact to existing SwarmAI modules so workers extend the product rather than invent parallel subsystems.

4. `FUTURE_PACKET_CATALOG_V18_TO_V30_20260921.md`
   - bounded worker packets with inputs, owned surfaces, work, tests, and exit criteria.

5. `FUTURE_SCHEMA_CONTRACTS_V18_TO_V30_20260921.md`
   - implementation-neutral durable schemas/interfaces for site authority, extensions, scheduling, objectives, learning, and audit.

6. `FUTURE_TEST_EVIDENCE_MATRIX_V18_TO_V30_20260921.md`
   - deterministic, integration, live/private, wall-clock, and independent-review evidence requirements.

7. `FUTURE_RISK_REGISTER_V18_TO_V30_20260921.md`
   - architectural failure modes and pre-decided fail-closed responses.

Existing canonical artifact contracts remain authoritative:
- `ARTIFACT_REGISTRY.json`
- `docs/artifacts/future/ART-V18-*.md`
- `docs/artifacts/future/ART-V19-*.md`
- `docs/artifacts/future/ART-V20-*.md`
- `docs/artifacts/future/ART-V23-*.md`
- `docs/artifacts/future/ART-V30-*.md`

## Important

These documents are prep, not implementation authorization.

Before executing a future packet, a worker must:
1. reread the canonical registry;
2. inspect current source;
3. reconcile any contract changes made since this prep set;
4. use current source/evidence rather than assuming the 2026-09-21 code map is still exact.

## Additional prepared accelerators

- `FUTURE_INFRA_REUSE_DECISIONS_20260921.md` — prevents unnecessary infrastructure/framework expansion.
- `FUTURE_MIGRATION_SEQUENCE_V18_TO_V30_20260921.md` — pre-orders durable schema work.
- `FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md` — implementation-complete vs accepted checklists.
- `FUTURE_OPERATOR_JOURNEYS_V18_TO_V30_20260921.md` — end-to-end acceptance journeys.
- `FUTURE_ACCEPTANCE_CASE_IDS_20260921.md` — stable negative/live case identifiers.
- `FUTURE_EVIDENCE_TEMPLATES_20260921.md` — candidate/recovery/scheduler/objective/learning evidence skeletons.
- `FUTURE_WORKER_START_PROMPTS_V18_TO_V30_20260921.md` — prepared future worker bootstraps.
- `FUTURE_TRACEABILITY_MATRIX_V18_TO_V30_20260921.md` — artifact -> packet -> code -> case -> evidence mapping.
