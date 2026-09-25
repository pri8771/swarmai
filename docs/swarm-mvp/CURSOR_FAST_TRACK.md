# Cursor: fast parallel V2 product completion

## Latest user direction — takes precedence

The user explicitly requests faster execution, substantial parallel work, and skipping new test/mock datasets and other work that slows delivery. This file is the execution entrypoint and overrides conflicting sequence, dataset, benchmark and exhaustive campaign requirements in `V2_PRODUCT_COMPLETION_PLAN.md`. Retain that detailed plan as the architecture/interface reference and read the review for reproduced defects. Do not implement its entire qualification program before shipping useful code.

**Objective:** connect and finish the real portable V2 goal-pursuit product. Implement the substantive system, integrate into dev, and return a usable build with precise limitations. No new mock-provider infrastructure, dummy-task corpus, nine-task benchmark, exhaustive fault campaign or benchmark-driven learning engine in this round. Reuse existing checks selectively. Do not manufacture live/accepted status when verification was deferred.

## Begin immediately

1. Fetch current dev, preserve active worktrees, read applicable instructions and this review. Reconcile review source `4444a565` with newer changes. No general re-audit or new long planning cycle.
2. One coordinator owns shared contracts, schema/migration ordering, app composition, tracking and dev integration. Publish a compact interface/ownership note and immediately dispatch the six lanes below. Existing types and services are the defaults; avoid parallel replacements.
3. Start independently useful work in every lane. Agree only interfaces that block others; don't force all workers to wait for the complete storage layer. Workers return small coherent commits/PRs as slices become usable. Coordinator integrates continuously in dependency order.

## Six lanes

| Lane | Owned work | Primary source boundaries | Integration dependencies |
|---|---|---|---|
| A — durable authority | Operational PostgreSQL repositories; persisted pursuit history/progress/schedules/dedupe/reservations; migrations and safe legacy import; no writable fallback when DB is unavailable | `db/`, `migrations/`, persistence adapters | Coordinator approves schemas; expose repository contracts first |
| B — real pursuit and execution | Remove successful RecordingExecutor from operational composition; real mission dispatch; bounded native model/tool loop; real clock/coordinator scheduling; recovery and stop conditions | `pursuit/`, `mission/`, `controller/`, native adapter | A contracts; E receipts; use one existing broker/tool authority |
| C — workers and permission enforcement | All-required capability/scope matching; verified enrollment; runtime eligibility; scoped workspace/artifact input; drain/revoke/rotate/reconnect; cancellation while work is executing | `workers/`, `workspace/`, worker lifecycle services | A durability; coordinator wires shared API models/routes |
| D — agent continuity | Human-configurable agents; actual scoped peer help/messages/delegation; layered memory retrieval; X/Y KT1/KT2 succession with logical identity and fenced sessions; persist lesson provenance/adoption, reuse existing evaluator only | `memory/`, `knowledge/`, `runtime/session*`, collaboration/handoff code | A persistence; C effect fences; B runtime integration; coordinate `mission/collab.py` ownership explicitly |
| E — truthful acceptance and accounting | Fix failed/self-claimed criterion achievement; protected verifier/artifact receipts; actual route/usage/budget accounting; real LiveGrant dispatch/preflight wiring | verification/acceptance, artifacts, cost/broker integration | A transactions; B result contract; no new synthetic campaign or fabricated receipts |
| F — usable product and deployment | UI/SDK/CLI parity for goals, agents, progress, artifacts, pause/resume/cancel and worker control; package console + server + coordinator + outbound worker; fresh volume permissions, readiness, install/restore docs | `apps/console/`, `sdk/`, `deploy/`, Dockerfile, install docs | Contract-first with A–E; coordinator alone merges shared `api/store.py`, route/schema and CLI edits |

Map lane tasks to PC packets from the detailed plan, but record current fast-track priority in the existing packet queue. PC-08's new benchmark corpus, PC-11's exhaustive new campaign and related dataset work are deferred by user instruction. Do not close those deferred qualification requirements as passed.

## Implementation priorities and rules

- First integration slice closes review R20-01 through R20-05: false operational success, failed-result achievement, executor authorization/path escape, lost pursuit state/zero clock, and false enrollment qualification. These are implementation defects, not credential blockers.
- Next connect goal → persisted cycle → admitted mission → real worker → permitted model/tool effects → immutable artifact → protected verifier → durable criterion progress → next autonomous cycle. Remove shadow demos from this path.
- API/store, routes, shared contracts, migrations and tracking have one integration owner. Workers propose bounded patches for shared files; no concurrent wholesale rewrites. A fresh branch/worktree per lane; branch PRs target dev. Never main.
- Use generic identities/configuration. No personal R730/Mac/domain/account/path assumptions. One coordinator with outbound workers; no peer consensus or distributed writable memory.
- Native runtime must work first. Preserve optional OpenCode/Hermes integration boundaries and show honest availability. Do not spend this round implementing another agent framework or inference router.
- Personality, peer advice, memory or model output cannot grant permissions. All effects remain kernel-mediated. Runtime cancellation, resource caps, grant checks and accurate state are essential implementation work.
- Context thresholds are configurable; use the detailed plan's conservative defaults if no approved values exist. Trainee shadows read-only, KT2 transfers continuity, generation fencing prevents two active writers.
- Persist scoped lessons with sources and reversible adoption. Defer elaborate benchmark-driven learning, model ranking and weight training.
- Do not stop because Linear, a personal host, public ingress or live inference is unavailable. Finish all independently implementable product work and identify only the specific dependent operation as blocked.

## Minimal verification, no new test-data project

Use existing targeted regressions for the code changed, type/lint/build checks required by the repository, and a brief operational smoke check with an authorized local workspace. Inspect actual persisted state/artifacts and reopen after restart. Do not add mock infrastructure or benchmark datasets. Do not repeatedly run broad suites when targeted checks already resolve the remaining risk; do not bypass required repository/CI gates.

The existing review probe script may be used to confirm the reproduced defects are gone; it is an observation tool, not a benchmark project. Do not add tests that only mirror new implementation. Keep any essential new regression narrow and use existing fixture support rather than constructing a new corpus. If no applicable live grant exists, finish the live path and its preflight but do not make model calls solely to satisfy a demonstration.

Describe unrun checks as unrun. "Implemented", "smoke-checked", "independently verified", "live-qualified" and "accepted" remain distinct. No version acceptance is implied by this speed-first round. No spending, public deployment, account creation or main merge is newly authorized.

## Tracking and delivery

Update canonical repository status and real Linear issues where the exact existing project/team is resolved. If Cursor's Linear auth or project resolution fails, record exact queued updates in LINEAR_RECONCILIATION and keep moving; never create a duplicate project or claim sync happened.

Integrate small PRs continuously, resolve conflicts, verify the integrated candidate, push dev under the existing integration authorization and read back its remote SHA. Keep an accurate checkpoint when context/worker limits require continuation; do not stop after only dispatching workers or writing plans. Report working user journeys, exact commit/PRs, minimum checks actually run, deferred verification and genuine blockers.

## Concise launch prompt

Read `docs/swarm-mvp/CURSOR_FAST_TRACK.md` from the supplied planning PR, then execute it against current dev. You are the integration owner: dispatch all six bounded lanes, agree shared interfaces immediately, and integrate continuously. Finish the real portable V2 goal-pursuit product—durability, native execution, worker permissions/cancellation, memory and X/Y succession, protected verification/accounting, and UI/SDK/Docker delivery. Follow the detailed plan for contracts, with FAST_TRACK taking precedence. Skip new mock datasets, benchmarks and broad test campaigns; retain brief critical checks and required CI. Update repo tracking and the verified existing Linear project, push work, and continue until independent engineering is finished. No main merge, paid inference or public deployment; report actual capabilities and remaining gates honestly.
