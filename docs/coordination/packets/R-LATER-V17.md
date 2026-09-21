# Remaining V1.7 execution contracts

These are executable specifications after their JSON dependencies/gates and reviewed adoption. Common commands and evidence format are in `README.md`; no blanket future planning pass is needed.

## R02b — genuine preregistered mission

Artifact ART-V14-REAL-E2E. Depends R02a; result requires independent semantic review. Own `scripts/` existing real-mission entrypoint invocation and `docs/evidence/v14-real-e2e/<new-run-id>/`; no product patch authored by the harness. Read REAL_V14_E2E_PROTOCOL and lead review of 007 first.

Before starting: freeze candidate, goal, bounded unaudited subsystem, real brokered local route, budget/retry limits, verifier and no-known-answer declaration. Do not re-use the already audited tool/knowledge/lease defects as a discovery test. At most two new attempts. Each creates an isolated diff through SwarmAI, shows a real pre-patch failing regression or objective defect proof, passes the post-patch targeted check and receives independent review. An honest no-defect/failed run stays a failed run and may require a bounded runtime repair. Never pick a prewritten answer and call it discovery.

Negatives: no-op/typing-only patch, unrelated review, collection failure masquerading as red test, unrelated passing suite and changed acceptance after output. Evidence includes mission ID, route/usage, before/after diff and test artifacts. Exit: new evidence review_pending; CP1 passes only after the separate lead decision. No invented zero usage.

## R17b — leased runtime aggregate

Completion requires R17b-1 and R17b-2. The current `MissionRuntime` creates a file-backed MissionStore and MissionController; a new DurableWorkerService constructor alone cannot put DB leases on that path. Do not keep parallel writable mission authorities.

### R17b-1 — durable mission/attempt mapping

Artifact ART-V15-WORKER-PROTOCOL. SP2. Depends R17a/R28b. Own `src/swarm/db/repositories.py`, new `src/swarm/mission/durable_bridge.py`, `src/swarm/mission/store.py`; tests `tests/integration/db/test_mission_durable_bridge.py`.

Map existing mission/project/task/graph-revision/attempt IDs into current MissionRow/TaskRow/TaskAttemptRow through existing repositories. Persist immutable source/input/config/acceptance digests and cancellation generation. Use stable command IDs and transactional outbox; replay of identical admission returns the same IDs, changed payload with same ID conflicts. File MissionStore becomes a derived export/cache in leased mode; never writes authoritative status independently. Import legacy development records explicitly as historical, not fresh authority. Keep DB-backed source of truth across reopen.

Negatives: crash after commit before file export, duplicate admission, changed graph/input, wrong project, cache edited to fake success. Clean/restart on real Postgres yields one graph and original IDs. No migration guessed: inspect current columns; any actual schema gap must be a named bounded migration before this packet exits. Evidence contains source/schema and two-process readback; no live qualification claim.

### R17b-2 — claim/run/submit/accept loop

SP2. Depends R17b-1. Own `src/swarm/mission/runtime.py`, `src/swarm/controller/mission.py`, `src/swarm/mission/durable_bridge.py`; tests `tests/mission/test_leased_runtime.py` with real DB cases.

Operational mode is explicitly leased, requiring configured DB and authenticated principal. Controller schedules eligible existing tasks; WorkerClient claims from DurableWorkerService, performs bounded work under returned immutable lease, renews until finish, submits result, and an independently authorized controller accepts it through existing acceptance fences. WorkerClient.control_plane_accept must not become worker authority. Controller.reconcile_leases invokes existing expiry/reassignment service and does not schedule from file cache. Connect LeaseFenceProvider to later R28d effects. Until R28d is complete, use no-effect test tasks for integration evidence; do not claim ungatewayed worker writes operationally complete. Database-less mode is labeled simulation and cannot perform operational effects.

Negatives: expiry before/during task, cancellation between renew and submit, changed input revision, duplicate result, worker attempting acceptance and process restart. One result accepted by control-plane identity, stale result retained and rejected. No second scheduler/thread timer authority.

## R17c — separate worker and API aggregate

Completion requires R17c-1/R17c-2. Both use the same authoritative rows and services from R17b.

### R17c-1 — authenticated transport and worker read model

SP2. Depends R17b. Own `src/swarm/workers/transport.py`, `src/swarm/api/routes_v1.py`, `src/swarm/api/store.py`; tests `tests/workers/test_worker_http_transport.py` and API authorization tests.

Wire existing enrollment/heartbeat/claim/renew/submit/drain DTOs through authenticated HTTP transport. Bind principal/project and enrolled worker generation on the server; request fields cannot impersonate another worker. Worker credentials allow claims/submission only, never accept_result or approval creation. ProductStore reads worker state from DurableWorkerService; legacy WorkerRegistryService remains explicitly simulation-only. Local control-plane calls use the same service and independent acceptance identity. Preserve protocol errors and immutable request IDs; no provider credential reaches worker.

Negatives: forged project/worker/generation, revoked worker, duplicate submit, worker calling acceptance/admin API, stale transport reconnect and server restart. Real service transport tests retain rejection receipts; no in-memory operational authority fallback.

### R17c-2 — separate-process CLI

SP2. Depends R17c-1. Own `src/swarm/cli.py`, new `src/swarm/workers/runner.py`, `scripts/r17_cp3_separate_process_recovery.py`; tests `tests/workers/test_runner.py` plus real CP3 run.

`swarm worker run --project <id>` uses scoped worker enrollment credential and WorkerClient. Claim, renew, execute approved task, submit; control plane accepts independently. Inference requests go to control-plane broker, never provider SDK credentials on worker. Termination stops renewal and lets durable expiry/reassignment handle recovery; no local task database/scheduler.

Kill worker during a real bounded mission; launch replacement process, prove stale submit rejection and one accepted result. Also concurrent duplicate accept, cancellation and reconnect. Capture real process IDs/UTC times; second process on same host is not physical multi-host evidence. Exit CP3 complete for local process recovery; R18 physical gate remains.

## R25b — CP4 scoped knowledge in real missions

Artifact ART-V16-CONTEXT-BUDGET-EVIDENCE. Depends R25a. Own new `scripts/r25_cp4_knowledge_missions.py` and its focused harness checks. Real Postgres, real zero-paid brokered local inference, fixed A/B mission set and scorer/route manifest.

A1 produces observation; separately authenticated operator with knowledge.accept grants accepted_fact (worker cannot). A2 reuses permitted item/version, with exact prompt and retrieval receipt refs. B's identical query cannot see A content or infer it through IDs/counts when A's hidden corpus changes from 1 to 50 items. Compare semantic actor-visible fields, excluding declared run IDs/timestamps. Supersession then tombstone remove old content and invalidate dependent summaries. Knowledge text is untrusted data, never a system directive.

Token comparison uses same permitted full-history baseline and identical token estimator/tokenizer version, excluding cross-project content. Require a nontrivial frozen workload with relevant context and strict reduction; empty baseline is invalid, not a free pass. Correctness scorer must prove retained useful information; if quality is UNKNOWN, explicitly block the quality claim rather than silently calling the whole artifact complete. Negative controls include prompt injection, stale cached summary and direct cross-project lookup. Preserve every failed run; CP4 reviewable only when its own required properties are demonstrated.

## R34a — integrated operational mission

Artifact V1.7-integrated-audit. Depends R33b/R25a/R17c/R27d. Own new `scripts/r34_cp6_integrated_mission.py` and focused harness tests. One real zero-paid mission from API/CLI must contain broker reservation/settlement, DB lease claim/accept, knowledge retrieval and action receipts. Harness fails on any missing family or disconnected mission/task IDs. Use actual enforced sandbox for code tasks.

Cancel after admission but before a new effect: prove new admission denied and stale result rejected; already-issued remote effect may require reconciliation, never promise it was undone. Kill/restart control process: same durable graph/operation identities resume without duplicate effects. Evidence must show operational service calls, not manually assembled receipt lists. CP5-REALWORLD may be pending separately; do not substitute these local runs for it.

## R34b — CP6 exact candidate claim matrix

Artifact V1.7-integrated-audit. Depends all entries in JSON, including R17c/R27d. Own `docs/evidence/v17-checkpoints/CP6/<run-id>/`; no source refactor. Freeze pushed source/schema/lock/config and protocol identities, complete configured check commands/exits/skips, CP0–CP5 refs plus real-world result, every V1.0–V1.7 registry artifact and its evidence disposition.

Compute dimensions independently: implementation, wired, live_local, real_world, independently reviewed, external_pending, wall_clock_pending. Implementation-complete requires every core wiring/source row; live-checkpointed only for actual passed required checkpoints. Working requires R33c-2 plus relevant real-world policy. Accepted requires canonical governance and lower-version acceptance; no blanket label is allowed merely because a harness ran. Missing CP2, task quality, CI, provider, physical host or elapsed gate remains explicit.

Negatives: mix candidate SHAs, hidden required skips, missing subsystem receipt, failed real-world run relabeled fixture pass, stale lead decision or self-review. Exit: internally consistent reviewable CP6 package and exact next independent packet/gate, whether or not all claims can be made.
