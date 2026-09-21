# ART-V23-OPS-PLATFORM — V2.3 operational platform architecture

Status: drafting
Target milestone: V2.3
Owner: ChatGPT lead

## Purpose

Bridge the V2.0 single-mission product to V3 persistent objectives without prematurely giving the system self-directed authority.

V2.3 should make many concurrent user-authorized missions manageable, observable, portable and extensible. It must build on the V2.0 durable authority model rather than introduce a second scheduler, second quota ledger or hidden cross-project execution path.

## Non-negotiable invariants

1. **Authority is monotonic:** V2.3 scheduling can further restrict execution but cannot grant permissions, project scope, provider eligibility, tool authority or spending that the underlying mission did not already have.
2. **Reservations are shared truth:** provider, worker and tool-effect capacity is reserved through the same durable admission primitives used by V2.0. A mission cannot bypass fairness by recursively creating children or changing lanes.
3. **Project isolation precedes ranking:** project/data/tool permissions are checked before work enters a shared scheduling pool. Fairness never means sharing private context.
4. **Unknown is not capacity:** unknown quota/cost/worker health does not become schedulable merely to prevent starvation.
5. **Cancellation/drain fences future work:** cancelled missions, drained workers and stale site epochs cannot receive or accept new work.
6. **Every scheduler decision is explainable:** durable decision receipts identify inputs, policy version, competing eligible work and the reason one item was admitted/deferred.
7. **V3 authority is absent:** schedules/events in V2.3 may operate only on already-authorized missions or explicit operator-created recurring contracts. Persistent autonomous objectives remain V3.

## ART-V23-MULTIMISSION-OPS

### Mission scheduling record

Each schedulable mission exposes a normalized immutable-at-decision snapshot:

- `mission_id`, `project_id`, `mission_revision`;
- `priority_class` (`urgent`, `interactive`, `normal`, `background`) plus operator-set numeric weight;
- optional deadline / earliest-start / maximum parallelism;
- current runnable task count and dependency depth;
- requested provider/tool/worker resource classes;
- remaining mission request/token/tool-effect envelopes;
- cancellation generation and site epoch;
- enqueue timestamp and accumulated eligible wait time.

Priority is configuration, not an excuse for starvation. The scheduler persists the policy version and effective weight used for every decision.

### Fairness model

Default policy: **weighted deficit round robin at project level, then mission level**, with hard resource admission after selection.

Rationale:
- deterministic enough to replay/debug;
- supports different operator priorities without pure priority-queue starvation;
- does not require predicting exact model-token cost before admission;
- works with heterogeneous resources by maintaining a deficit/account per resource class.

Rules:

1. Eligible projects accrue deficit while they have runnable work.
2. A project selected for service spends deficit based on normalized resource units, not wall-clock duration.
3. Within a project, missions use the same mechanism with their own bounded weights.
4. `urgent` may borrow bounded future deficit but cannot exceed configured global/project concurrency or quota reservations.
5. Background work gets an aging floor so continuously eligible work eventually receives service when required resources are available.
6. Child tasks inherit the parent mission/project accounting domain; spawning agents never creates new fairness credit.
7. Tasks blocked on a specific unavailable provider/tool do not consume fairness credit while ineligible.
8. A failed admission does not silently reroute across privacy/cost/tool boundaries; it records `deferred_resource_unavailable` and returns to eligible evaluation only when evidence changes.

### SchedulerDecisionReceipt

Persist an append-only receipt for every admission/defer/cancel/drain scheduling decision:

```text
receipt_id
policy_version
observed_at
site_epoch
candidate_set_hash
selected_project_id | null
selected_mission_id | null
selected_task_id | null
decision = admit | defer | cancel | drain
reason_code
resource_class
reservation_id | null
project_deficit_before/after
mission_deficit_before/after
priority_weight
wait_age_ms
source_revision
cancellation_generation
```

Receipts contain identifiers/metrics only, not prompt/customer payloads.

### Required negative behaviors

- 100 recursively spawned tasks do not create 100x project weight.
- one urgent project cannot exceed its provider/project concurrency cap.
- one project with a blocked remote route cannot consume another project's reserved local slots.
- cancellation between selection and reservation prevents dispatch.
- stale site epoch/worker generation prevents execution even if scheduler selected the task.
- duplicate scheduler ticks do not duplicate reservation/effect acceptance.
- a scheduler restart reconstructs deficits and pending state from durable records without resetting every project to zero unfairly.

## ART-V23-CAPABILITY-PACKS

Versioned capability packs bundle:
- task handlers;
- tool adapters;
- evaluator/scorer;
- prompts/procedures;
- permissions requested (never granted implicitly);
- compatibility constraints;
- tests;
- publisher/signature/digest;
- migration hooks with explicit supported from/to versions.

Installing a pack does not automatically grant permissions, create credentials, expose tools to every project or mark models/routes qualified.

Lifecycle: `installed -> enabled_for_project -> draining -> disabled -> uninstalled`. Disable/drain must fence new work while allowing policy-approved in-flight read-only work to finish or cancel safely.

## ART-V23-PORTABILITY

Export/import bundle includes:
- project config without secrets;
- artifact manifests and accepted-evidence refs;
- accepted knowledge/provenance + tombstones;
- mission history and immutable decision/effect receipts;
- capability manifests;
- schema/version compatibility manifest;
- cryptographic content hashes.

Never export secret values, browser/session state, live approvals, active leases/reservations, provider tokens or site authority credentials.

Import semantics:
- imported approvals are historical only and cannot authorize new effects;
- active leases/reservations import as expired historical records;
- site epoch is regenerated for the destination;
- unknown/newer schema versions fail closed with an actionable compatibility report;
- ID collisions require deterministic namespace remap recorded in an import receipt.

## ART-V23-OBSERVABILITY

One operational view for:
- missions/tasks and dependency state;
- scheduler/fairness queues and wait age;
- workers/site epochs/leases;
- providers/reservations/known vs unknown quota;
- tool approvals/effect receipts;
- artifact graph/acceptance state;
- knowledge retrieval/provenance;
- costs/unknown costs;
- errors/retries/recovery actions.

Trace IDs connect:
`operator action -> mission -> scheduler decision -> task/attempt -> inference/tool attempts -> artifacts -> independent acceptance`.

Observability is read-only with respect to authority. A dashboard control that mutates state must go through the same authenticated action/approval boundary as API/CLI operations.

## ART-V23-FLEET-POLICY

### Worker trust classes

- `observe_only`: no task execution; telemetry/status only.
- `sandbox_compute`: deterministic/local compute inside restricted workspace.
- `model_worker`: may execute admitted inference/task work but no browser/tool side effects by default.
- `tool_worker`: may receive specifically approved tool capabilities.
- `integration_worker`: trusted for bounded code/worktree integration only under explicit repository/project scope.

Trust class is a ceiling. Project policy may further reduce it. Worker self-report cannot raise its trust class.

### Placement inputs

- site/node labels and health;
- project affinity;
- data residency/locality labels;
- worker trust class and capabilities;
- current lease/concurrency load;
- required tool/provider reachability;
- maintenance/drain status;
- source revision/site epoch compatibility.

Placement output is still subject to durable lease and resource admission; a placement decision alone cannot execute work.

### Drain semantics

`active -> draining -> drained -> offline`.

On drain:
- no new leases;
- existing leases either finish before deadline or are cancelled/requeued using V1.5 fencing;
- effect-producing work that cannot be safely replayed must resolve through durable result/effect receipts before migration;
- the operator can see remaining leases and the exact reason a node is not yet drained.

## Acceptance protocol for V2.3 operational platform

A future V2.3 candidate is not accepted until all of the following are independently evidenced on one pinned integrated SHA/config:

1. **Fairness:** at least three projects with unequal weights share constrained provider and worker resources for a preregistered workload; measured service shares match policy within a preregistered tolerance and no eligible project starves.
2. **Anti-amplification:** a mission that dynamically expands by >=50 logical tasks cannot increase project-level scheduler share merely by expansion.
3. **Isolation:** two-project negative tests cover provider reservation, knowledge retrieval, tool approval/effect and worker placement boundaries.
4. **Restart:** scheduler/control-plane process restart preserves pending work, fairness accounting, reservations and cancellation fencing.
5. **Drain:** a worker/site enters draining while leases are active; new work stops and existing work finishes/requeues without duplicate accepted result/effect.
6. **Capability pack:** install, enable for one project, deny unauthorized project use, drain/disable, and verify no implicit permission/model qualification change.
7. **Portability:** export/import one project into a clean environment with no secrets/live authority; history/provenance/artifacts remain verifiable and imported approvals/leases cannot execute.
8. **Traceability:** one accepted result can be traced from operator request through scheduler decision, task attempts, inference/tool receipts and artifact acceptance using durable IDs.
9. **Failure truth:** inject provider unavailability and worker loss; dashboard/API report explicit blocked/recovery state rather than mock success.
10. **Zero-spend operator profile:** no paid fallback or unknown-cost route is admitted under the operator's configured policy.

All workloads, tolerances and negative expectations must be frozen before counted execution. Simulated scheduler tests are necessary but do not replace the multi-process/private live evidence required by the acceptance protocol.

## Decomposition direction

Keep implementation packets SP1-SP3 and wait until V2.0 interfaces are sufficiently stable before assigning them:
- V23A-001 / SP2 — scheduler decision schema + durable project/mission deficit records;
- V23A-002 / SP3 — weighted deficit scheduler behind existing admission boundary;
- V23A-003 / SP2 — restart/anti-amplification regressions;
- V23B-001 / SP2 — capability-pack manifest/validator + project enablement contract;
- V23B-002 / SP2 — export/import bundle schema and secret/authority stripping;
- V23B-003 / SP2 — trace/read model for scheduler/effect/artifact graph;
- V23A-004 / SP2 — fleet trust/placement/drain policy implementation;
- V23X-001 / SP2 — frozen multimission fairness benchmark manifest.

Do not implement persistent objectives here; that is V3. Do not assign these packets until they are non-conflicting with the active V2.0 critical path and the lead has registered/frozen the relevant V2.3 artifact contracts.
