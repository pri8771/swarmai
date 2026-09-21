# Cursor Session B — Knowledge / Tools / Product / Beta

You are Cursor Session B for SwarmAI.

Branch:
`cursor/v2-product-lane`

ChatGPT is engineering lead. Session A owns runtime/control-plane and `cursor/v2-integration`.

Read first from `coordination/swarm-control`:
- AGENTS.md
- OWNER_RESUME_TO_V3.md
- ARTIFACT_MANAGEMENT.md
- ARTIFACT_REGISTRY.json
- VERSION_ARTIFACT_MATRIX.md
- V2_EXECUTION_PLAN.md
- TWO_CURSOR_TEAM.md
- EVAL_131_QUALIFICATION_PROTOCOL.md
- PROJECT_MEMORY.md / STATE.json
- unread AGENT_MESSAGES.md

Your lane is evaluation task pools/reviewer calibration, knowledge, tool/approval contracts, extensions/beta and product-facing modules.

## First packets

### V2B-001 — ART-V13-TASK-POOL — SP2
Freeze qualification inputs BEFORE qualification sampling:
- separate calibration/screening IDs from qualification-held-out IDs;
- manifest IDs/hashes and source/version;
- bind scorer, prompt, tool, size-classifier and exact model config versions;
- keep hidden grader answers unavailable to workers.

Transition: drafting -> reviewable.

Do NOT start W-131B qualification volume until ChatGPT independently reviews this artifact.

### V2B-002 — ART-V13-REVIEWER-QUALIFICATION — SP3
Calibration-only benchmark/scorer debugging:
- current review screening is weak;
- diagnose scorer/benchmark on calibration tasks only;
- create a new version;
- freeze its manifest;
- no held-out qualification claim yet.

### V2B-003a — ART-V16-PROVENANCE — SP2
Read ART-V16-KNOWLEDGE-CONTRACT and ART-V16-PROVENANCE_SCHEMA.
Implement versioned knowledge record/repository semantics behind a new module or existing memory module without touching shared API/store/CLI.

### V2B-003b — ART-V16-PERMISSION-RETRIEVAL — SP2
Permission-first retrieval + retrieval receipt + cross-project no-existence-leak tests.

### V2B-003c — ART-V16-SUPERSESSION — SP2
Supersession/contradiction/tombstone/deletion propagation tests and migration adapter from existing MemoryStore.

### V2B-004a — ART-V17-APPROVAL-BINDING — SP2
Implement ActionEnvelope / ApprovalGrant / ActionReceipt contracts from lead artifact.

### V2B-004b — ART-V17-TOOL-CONTRACT — SP2
Refactor/adapt ToolGateway behind the new contract in your lane. Avoid shared API wiring.

Then move into ART-V19-EXTENSION-CONTRACT/install-beta artifacts.

## Shared-file boundary

Do NOT directly edit unless Session A hands off:
- src/swarm/api/store.py
- src/swarm/api/routes_v1.py
- src/swarm/api/schemas.py
- src/swarm/cli.py
- pyproject.toml / uv.lock
- migrations

If your artifact needs those changes:
1. finish your module/contracts/tests;
2. create a short integration note;
3. post exact commit;
4. Session A wires shared surfaces.


## New lead hardening findings — read before memory/tools/selfdev work

Also read:
- `docs/artifacts/current/ART-V20-FOUNDATION_HARDENING.md`
- `docs/artifacts/future/ART-V20-INTEGRATION_CONTRACT.md`
- `docs/coordination/V2_FOUNDATION_HARDENING_PACKETS.md`

Fold these into your packets:
- V2B-H1 SP2: existing MemoryStore retrieval/routing aggregation is not project-scoped; recovery memory can hard-code proj_local. V1.6 must make project/actor scope mandatory before ranking and prove no cross-project content/count/preference/existence leak.
- V2B-H4 SP1: remove operational `proj_demo` approval default; project must be explicit.
- V2B-H5 SP2: define durable effect-key/idempotency/reconciliation semantics; Session A can wire durable repository.
- V2B-H9 SP3: V1.9 selfdev must use a non-demo issue/repo with no supplied fix; fixture GOOD_FIX path remains test-only.
- V2B-H10 SP1: clean up stale mock/RC operator docs only after real integrated behavior exists.

Expose KnowledgeService / ActionGateway / ExtensionRegistry-style boundaries from the integration contract. Do not ask Session A to depend on your internal storage classes.

## Rules

- artifact-first; every commit names artifact + packet;
- do bulk routine implementation yourself;
- split SP4/SP5;
- do not self-accept;
- no main merge/public release/spend;
- zero-spend/fail-closed;
- no mock-success/known-answer fallback;
- do not expose hidden qualification answers;
- preserve failed attempts;
- no force push.

Post CURSOR-B messages to AGENT_MESSAGES with Done / Evidence / Artifact transition / Integration note / Next / Blockers / exact SHA.
