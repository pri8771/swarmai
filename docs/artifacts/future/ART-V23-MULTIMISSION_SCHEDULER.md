# ART-V23-MULTIMISSION-OPS — fair multi-mission scheduling contract

Status: drafting
Target: V2.3
Owner: ChatGPT lead
Depends on: V2.0 integrated candidate, ART-V15 durable workers, ART-V12 broker

## Goal

Run many authorized missions concurrently without one project/mission recursively consuming all workers/provider quota/tool capacity. Scheduling changes share and order only; it must never widen authorization, data scope, provider eligibility, tool permissions or spending authority.

## Scheduling hierarchy

1. admission policy decides whether a mission may enter runnable state;
2. project scheduler chooses project share;
3. mission scheduler chooses mission/task within project;
4. worker/broker/tool admission chooses concrete resources;
5. acceptance fencing decides whether a returned result/effect may become durable accepted state.

Authorization/data never cross projects merely because scheduler metadata is shared.

## Durable scheduling state

ProjectQueueState:
- project_id
- priority_class
- weight
- active_mission_count
- runnable_task_count
- reserved_worker_slots
- provider reservation summary
- deadline_pressure
- last_served_at
- deficit_credit
- max_concurrent_tasks
- max_concurrent_model_calls
- policy_version
- scheduler_epoch
- version

MissionQueueState:
- project_id
- mission_id
- lifecycle: admitted | runnable | waiting | blocked | draining | cancelled | completed
- priority
- deadline_at / slack_ms if declared
- runnable_task_count
- active_attempt_count
- last_served_at
- cancellation_generation
- graph_revision
- version

Task scheduling state remains in the canonical durable task/attempt store. Do not introduce a second task-status authority merely for scheduling.

## Fairness policy

Use weighted deficit/fair-queue semantics rather than strict priority.

Hard priority is reserved for explicit operator/system safety classes.

At each scheduling round:
1. add `base_quantum * project.weight` to each admitted project with runnable work;
2. compute bounded urgency/aging bonus without changing the project's configured weight;
3. choose an eligible project with positive credit and the highest deterministic score;
4. choose one eligible mission/task inside that project;
5. charge the project's deficit by an estimated normalized service cost when dispatch succeeds;
6. reconcile estimated cost with observed service class after completion without rewarding failed/denied admissions.

Normalized service cost is a scheduler abstraction, not money. It may include worker-slot class, expected model-request class, tool-side-effect class and declared long-running CPU class. Provider token/request budgets remain enforced independently by the broker.

### Required invariants

- every admitted project with continuously runnable eligible work eventually receives service;
- weight affects long-run share, never project authorization;
- deadline pressure is bounded and cannot create permanent starvation;
- task spawning inherits the parent project/mission entitlement and cannot mint extra scheduling credit;
- blocked/waiting tasks consume no runnable share;
- a project cannot increase share by fragmenting one task into many tiny tasks;
- cancelled/draining work cannot re-enter eligibility without a new authorized state transition;
- retries/repair attempts are charged to the same project and do not receive fresh fairness entitlement;
- provider/tool/worker reservations remain separately enforced and cannot be bypassed by scheduler score.

DBOS partition concurrency may enforce per-project concurrency/flow control if DBOS is retained, but SwarmAI remains responsible for which mission/task is eligible and fair to enqueue.

## Mission/task choice

Within a selected project, candidates must satisfy:
- dependencies ready;
- mission/task cancellation generation valid;
- task source/graph revision current;
- task priority;
- deadline/slack when declared;
- aging to prevent starvation;
- required capability/trust/locality available;
- no duplicate accepted attempt/effect;
- privacy/data-locality constraints compatible with the proposed worker/route/tool;
- required approvals already present where applicable.

Tie-breaking must be deterministic from persisted fields plus a recorded scheduler policy version; do not depend on process-local iteration order.

## Atomic resource reservation boundary

Scheduler does not assume capacity because a worker exists. Task enters `dispatched` only after all required reservations are acquired or a durable reservation-intent protocol guarantees fail-closed behavior.

Required reservation classes may include:
- worker slot/lease;
- provider request/token/concurrency reservation;
- tool/effect admission and approval binding;
- artifact/workspace capacity;
- site/epoch authority for consequential effects.

Cross-system reservations may not be truly atomic. If so, use a durable `DispatchIntent` with:
- dispatch_intent_id
- project_id / mission_id / task_id / attempt_id
- scheduler_epoch / policy_version
- selected worker class/worker_id if allocated
- provider reservation IDs
- tool/effect reservation IDs
- created_at / expires_at
- state: preparing | ready | dispatched | compensating | released | completed
- version / idempotency digest

Inference/tool execution must not begin until the intent is `ready`. Partial failure triggers idempotent compensation/release. A crash during preparation is reconciled by expiry/recovery before the task can be claimed again. Unknown provider/effect outcome stays unknown and fenced; it is not silently retried as fresh work.

## Backpressure

Per-project and global controls:
- max admitted/runnable queue depth;
- max active missions/tasks;
- bounded graph growth and child-task fanout;
- provider request/token envelopes;
- worker-class capacity;
- tool side-effect concurrency;
- artifact/workspace storage pressure;
- per-site process/concurrency limits.

Overload response is queued, blocked or rejected according to versioned policy, not silent unbounded memory growth. Backpressure decisions must be explainable and observable.

## Restart and recovery semantics

Persist enough scheduler state to restart without resetting fairness:
- deficit credit;
- last served timestamp;
- project/mission concurrency counters derivable or reconciled from durable leases/reservations;
- scheduler epoch and policy version;
- DispatchIntent state;
- cancellation/drain state.

On scheduler restart:
1. increment/claim scheduler epoch using a fencing rule;
2. reconcile active leases/reservations/intents before new dispatch;
3. expire or recover stale preparation intents;
4. recompute derived counters from durable authoritative stores;
5. preserve fair-share credit subject to a bounded cap so long downtime does not create an unbounded burst;
6. resume only work whose project/mission/task generation is still valid.

Two active scheduler epochs must never both authorize new consequential dispatch. Standby/read-only observers may exist, but dispatch authority is fenced.

## Cancellation and drain

Mission cancellation removes not-started tasks from eligibility and fences active attempts by cancellation generation.
Project pause prevents new dispatch but may allow already-running safe read/compute work to drain according to policy.
Worker/site drain uses V1.5 worker protocol and V1.8 site authority. Consequential effects require current site epoch and approval/effect binding even during drain.

## Explainability artifact

Every actual dispatch decision produces a `SchedulingDecisionReceipt` suitable for audit without private prompt/output content:
- receipt_id
- scheduler_epoch / policy_version
- timestamp
- project_id / mission_id / task_id / attempt_id
- eligible_project_count / eligible_task_count
- selected project weight / deficit-before / bounded urgency-age bonus
- estimated service class / charged cost
- selected worker capability class
- provider/tool reservation references (opaque IDs only)
- decision: dispatched | queued | blocked | rejected
- reason codes
- dependency/cancellation/source revision
- reservation/dispatch intent ID
- resulting deficit-after

Receipts must not contain credentials, private browser state or raw customer/model content.

## Anti-gaming and pathological cases

Required negative cases:
- one project spawns thousands of children to try to gain share;
- repeated retry/repair loops attempt to reset priority/credit;
- a high-priority project continuously arrives while a lower-weight project remains runnable;
- incompatible worker at queue head must not block a later eligible task;
- partial provider reservation succeeds but worker reservation fails;
- scheduler crashes after reservations but before dispatch;
- result returns after project cancellation or scheduler/site epoch change;
- project weight changes while tasks are in flight;
- provider quota is exhausted while scheduler still has project credit;
- one project has only blocked work while another is runnable;
- duplicate scheduler processes race to dispatch the same task.

All cases must fail closed on authority/effect duplication and preserve eventual service for eligible work.

## Acceptance design

V2.3 acceptance should include sustained deterministic and live-local tests with at least two projects and multiple missions:
- projects with equal constant runnable demand converge to roughly equal service under equal weights;
- configured unequal weights produce corresponding larger long-run service share without starving the lower-weight project;
- use a preregistered tolerance (initial proposal: within ±15% of configured normalized share after >=200 successful scheduling decisions under controlled equal-cost synthetic load); if task costs differ, evaluate normalized service units rather than raw task count;
- no eligible project experiences starvation beyond the preregistered bounded aging/deadline policy under controlled load;
- recursive spawn cannot increase the parent's normalized entitlement;
- deadline pressure changes order only within its bounded cap;
- shared provider quota never double allocates and scheduler credit cannot override broker denial;
- project data/knowledge/artifacts remain isolated;
- cancellation frees/reconciles resources and stale results are fenced;
- scheduler state/fairness survives a real process restart;
- competing scheduler epochs prove a single dispatch authority;
- explain receipts account for every dispatch/blocked decision in the acceptance run.

The ±15%/200-decision figures are a proposed deterministic-test default, not a universal product SLA; freeze them or replace them with a reviewed metric before counted V2.3 evidence.

## Implementation packets

- V23A-001 SP2: durable `ProjectQueueState`/`MissionQueueState`, policy version and decision receipt contracts.
- V23A-002a SP2: weighted-deficit project selector + deterministic tie-breaking.
- V23A-002b SP2: mission/task eligibility/aging/deadline selection.
- V23A-002c SP3: durable DispatchIntent reservation/compensation integration.
- V23A-003a SP2: backpressure/anti-gaming/fair-share tests.
- V23A-003b SP2: restart/scheduler-epoch reconciliation and race tests.
- V23A-004 SP2: explain/observability API backed by decision receipts.

Keep implementation behind V2.0/V1.5 durable-store interfaces so this future work does not create a competing queue or persistence authority.
