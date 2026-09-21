# SwarmAI single-session execution contract — current -> V1.7

Status: ACTIVE OWNER DIRECTIVE
Date: 2026-09-21
Implementation branch: `cursor/v17-single-session`
Coordination branch: `coordination/swarm-control`

This document supersedes the previous multi-lane execution topology for CURRENT IMPLEMENTATION WORK through V1.7.

Historical A/B/worker-pc records remain evidence. They are not active implementation lanes.

## Operating model

Exactly ONE Cursor implementation session is active.

- Active implementation session: `CURSOR-V17-SINGLE`
- Active implementation branch: `cursor/v17-single-session`
- Heartbeat producers allowed: exactly ONE, owned by this Cursor session
- Parallel implementation lanes: NONE
- worker-pc/Claude: no new execution assignments under this directive
- ChatGPT role during this run: downstream planning/architecture/review help, not a competing implementation lane
- Operator remains final authority

The session may inspect old branches and reuse/cherry-pick reviewed code, but old branches must not wake or continue autonomous execution.

## Goal

Move SwarmAI from current repository truth to a V1.7 IMPLEMENTATION-COMPLETE / REVIEWABLE candidate with real evidence.

Do not claim "accepted V1.7" unless every required artifact is actually accepted under `ARTIFACT_REGISTRY.json`. Time-bound, provider-account, OS-specific, or independent-review gates may remain honestly blocked even after implementation is complete.

## Canonical truth

Before making status claims, read from `coordination/swarm-control`:

1. `docs/coordination/ARTIFACT_REGISTRY.json`
2. `docs/coordination/STATE.json`
3. `docs/coordination/WORK_QUEUE.md`
4. `docs/coordination/VERSION_ARTIFACT_MATRIX.md`
5. `docs/coordination/SINGLE_SESSION_HEARTBEAT.md`
6. this file
7. latest relevant lead reviews/messages

Repository evidence outranks old prompts/chat.

## Hard boundaries

Do not:
- merge to `main`;
- publish/release/deploy publicly;
- spend money or enable paid fallback;
- force-push;
- bypass provider eligibility, quota, MFA, login, approvals, or policy;
- fabricate live/provider/worker/timing evidence;
- treat mocks as live evidence;
- self-accept artifacts;
- silently turn UNKNOWN/BLOCKED into success;
- silently broaden permissions, project scope, provider scope, or tool authority.

Keep `SWARM_ALLOW_PAID=false`.

## Startup

1. Fetch all refs.
2. Confirm current branch is `cursor/v17-single-session`.
3. Confirm branch ancestry begins from the reviewed integration baseline.
4. Inspect donor branches:
   - `cursor/v2-runtime-lane`
   - `cursor/v2-product-lane`
   - `cursor/v2-integration`
5. Inventory differences. Do not blindly merge entire donor branches.
6. Reuse only changes that are understood, dependency-correct, and supported by current evidence.
7. Install/repair EXACTLY ONE heartbeat producer per `SINGLE_SESSION_HEARTBEAT.md`.
8. Disable/stop any legacy A/B heartbeat or autonomous-runner process found on the same machine.
9. Publish session-start heartbeat.
10. Run baseline tests/lint/type checks available in the environment and record truthful results.
11. Begin the critical path below.

## Execution rule

Work sequentially on one branch, but exploit independence INSIDE the session when safe (for example, prepare tests/docs while another local command runs). Do not create another autonomous implementation session.

For each packet:
- inspect existing implementation first;
- implement the smallest correct generic change;
- add deterministic tests;
- run relevant tests/lint/type checks;
- preserve failure evidence;
- commit with packet/artifact IDs;
- push;
- update heartbeat/status;
- continue to the next dependency-ready packet.

Do not stop merely because one artifact awaits independent acceptance. Continue with dependency-independent work while marking the gate accurately.

# Phase A — reconcile current critical gates

## A0 — V1.0 worker heartbeat normalization

The old two-lane heartbeat stress test is superseded for current execution.

Implement/use the single-session heartbeat contract. Historical heartbeat evidence remains history only.

Do not reinterpret heartbeat as implementation acceptance.

## A1 — V1.3 qualification closure

Current registry is authoritative. Reconcile any mismatch between STATE/WORK_QUEUE and registry before making claims.

Required work:
1. Verify the G13 task-pool candidate on the actual current execution environment.
2. If Windows-specific verification is required by the frozen artifact and this session is not running Windows, record that exact blocker; do not impersonate Windows.
3. Preserve frozen input IDs/digests and no-answer leakage.
4. Complete reviewer calibration/scorer implementation using calibration data only.
5. Keep counted held-out answers sealed from the implementing/reviewer model path.
6. Prepare real sealed-reference binding/evidence without exposing answers to workers.
7. Run counted qualification only when its frozen prerequisites are legitimately satisfied.
8. Produce overhead/report evidence from real runs.

Exit for implementation-complete:
- task pool implementation and verifier are stable;
- reviewer qualification implementation is complete;
- counted qualification machinery is complete;
- any unsatisfied environment/independent-review gate is explicit.

## A2 — V1.4 real E2E generic materialization repair

Repair the known generic failure:
- model output contract/parser mismatch;
- raw-source vs fenced-code assumptions;
- a write attempt with empty material git diff must never count as successful implementation.

Required:
1. Add generic source extraction/materialization behavior.
2. Use actual git material diff as the final "work changed" authority.
3. Add unrelated temporary-repository regressions.
4. Run a new preregistered real local brokered mission against a different subsystem.
5. Require actual repository/tool reads and actual brokered model inference.
6. Preserve failed attempts.
7. No known-answer substitution or canned implementation text.

Exit:
- at least one real mission produces a material diff and passes its required deterministic checks, OR an honest external blocker is documented with implementation otherwise ready.

## A3 — V1.2 remote-overlap path

Keep local fallback working.

Remote admission must remain fail-closed. API key presence or public pricing metadata is not enough.

Implement all machinery required for:
- exact provider/model identity;
- account-specific eligibility record;
- quota/reservation/settlement;
- concurrent/overlapping governed calls;
- route disable -> allowed alternate;
- zero-paid-fallback.

If two real zero-charge routes cannot be proven from the available environment/account, leave live overlap BLOCKED and continue dependency-independent implementation.

# Phase B — V1.5 durable distributed workers

## B1 — durable result acceptance fence

Implement the remaining result-acceptance path after claim/renew/expiry:
- project/task/source revision binding;
- worker/enrollment/generation binding;
- lease binding;
- cancellation generation;
- attempt identity;
- reservation/settlement state;
- deterministic review checks;
- stale/duplicate result rejection;
- exactly-one accepted result/effect semantics.

Race tests must include stale worker, expired lease, reassignment, duplicate result, cancelled task, wrong generation, and conflicting attempts.

## B2 — worker service/client

Implement the transport-independent worker protocol from the existing V1.5 artifacts:
- enrollment;
- capability/trust advertisement;
- dispatch/lease;
- renewal;
- cancellation/drain;
- result/evidence submission;
- restart/reconnect;
- quarantine/fail-closed behavior.

PostgreSQL remains authoritative.

DBOS, if used, is partial workflow durability only; it must not replace Swarm authority, permissions, result fencing, or schema ownership.

## B3 — multi-host/recovery evidence harness

Build the harness and documentation required to prove:
- host enrollment;
- dispatch;
- worker kill;
- lease expiry/reassignment;
- stale-result rejection;
- drain;
- restart/recovery.

If only one physical host is available to this Cursor session, finish the implementation/harness and mark live multi-host evidence pending rather than fabricating it.

# Phase C — V1.6 scoped reusable knowledge

Use:
- `ART-V16-KNOWLEDGE_CONTRACT.md`
- `ART-V16-PROVENANCE_SCHEMA.md`
- accepted durable schema constraints

## C1 — knowledge repository

Implement versioned:
- KnowledgeItem;
- KnowledgeLink;
- Tombstone;
- project/tenant scope;
- provenance/source/content digests;
- acceptance state;
- confidence/expiry;
- permissions/retrieval labels;
- contradiction/supersession links.

Model output defaults to observation/hypothesis, never accepted_fact.

## C2 — permission-first retrieval

Order is mandatory:
1. resolve actor/project authorization;
2. filter permitted item IDs/versions;
3. remove deleted/stale/superseded according to query mode;
4. rank ONLY permitted candidates;
5. assemble bounded context;
6. emit retrieval receipt with selected IDs/versions/provenance/token cost.

Never rank a cross-project global corpus and filter afterward.

## C3 — lifecycle

Implement:
- versioned edits;
- contradiction sets;
- explicit supersession;
- deletion/tombstones;
- invalidation of retrieval index, dependent summaries, caches, export materializations, and future prompt assembly.

## C4 — legacy memory adapter

Adapt existing MemoryStore conservatively.
No silent conversion of prior generated memory into accepted facts.

## C5 — context-budget evidence

Create a fixed mission set and measure:
- selected relevant facts;
- context tokens loaded;
- context tokens avoided versus whole-history;
- stale/irrelevant retrieval;
- task quality;
- cross-project isolation negatives.

# Phase D — V1.7 unified tools/browser/permissions

Use:
- `ART-V17-TOOL_PERMISSION_CONTRACT.md`
- `ART-V17-APPROVAL_BINDING.md`
- accepted durable-effect schema

## D1 — shared consequential-action contracts

Implement:
- ActionEnvelope;
- ApprovalGrant;
- ActionReceipt;
- migrations/persistence;
- exact payload/destination/operation binding;
- effect/idempotency key;
- lease/cancellation generation;
- policy version.

## D2 — ToolGateway integration

Required order:
1. normalize;
2. authorize project/resource;
3. evaluate policy/risk;
4. require exact approval if needed;
5. reserve effect/idempotency;
6. execute adapter;
7. capture pre/post evidence;
8. reconcile;
9. expose only authorized artifacts.

Unknown external outcome enters reconciliation. Never blind-retry a consequential effect.

## D3 — adapter framework + manifest

Version adapters and declare:
- read/write data classes;
- scopes;
- secrets required;
- network/filesystem boundaries;
- risk/side-effect behavior;
- sandbox/host requirements.

Implement at least:
- one local/sandbox adapter;
- one API/MCP-style adapter;
- one browser/session-aware adapter or a complete browser/session path if external login blocks live execution.

## D4 — session recovery

Implement:
- safe browser/session alias only;
- signed-out/expired detection;
- preserve intended destination;
- request only essential human auth;
- return to exact approved destination/action;
- login success must NOT imply submission/execution.

## D5 — permission/effect negative suite

Cover:
- wrong project/identity;
- altered payload after approval;
- changed destination;
- expired/revoked approval;
- unsafe redirect;
- denied network/filesystem scope;
- cancellation;
- stale lease/generation;
- duplicate retry;
- unknown external outcome;
- session recovery without duplicate side effect.

# Completion definition for this Cursor run

The branch is V1.7 IMPLEMENTATION-COMPLETE / REVIEWABLE when:

1. all source paths required through V1.7 are implemented;
2. deterministic unit/integration/negative tests exist and pass where runnable;
3. lint/type checks pass where configured;
4. real E2E/provider/multi-host evidence is produced where genuinely available;
5. unavailable external gates are explicitly BLOCKED/WAITING with exact reason;
6. no mock operational result is counted as live evidence;
7. artifact evidence pointers are updated without self-promoting to accepted;
8. branch is pushed cleanly;
9. final report maps every V1.0-repair through V1.7 required artifact to:
   - implemented;
   - evidence produced;
   - reviewable;
   - blocked;
   - or external/time-bound acceptance pending.

Do not continue into V1.8+ implementation in this session unless the operator explicitly changes scope.

Use `V16_TO_V30_FORWARD_PLAN_20260921.md` and `V16_TO_V30_TASK_BACKLOG_20260921.md` as future planning only.
