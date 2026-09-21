# ART-V23-MULTIMISSION-OPS — fair multi-mission scheduling contract

Status: drafting
Target: V2.3
Owner: ChatGPT lead
Depends on: V2.0 integrated candidate, ART-V15 durable workers, ART-V12 broker

## Goal

Run many authorized missions concurrently without one project/mission recursively consuming all workers/provider quota/tool capacity.

## Scheduling hierarchy

1. admission policy decides whether a mission may enter runnable state;
2. project scheduler chooses project share;
3. mission scheduler chooses mission/task within project;
4. worker/broker/tool admission chooses concrete resources.

Authorization/data never cross projects merely because scheduler metadata is shared.

## Project scheduling metadata

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
- deficit/credit
- max_concurrent_tasks
- max_concurrent_model_calls
- policy_version

## Recommended fairness policy

Use weighted deficit/fair-queue semantics rather than strict priority.

Hard priority is reserved for explicit operator/system safety classes.

Properties:
- each admitted project with runnable work eventually receives service;
- weight changes share, not authorization;
- deadline urgency may increase scheduling score within bounded cap;
- recursive task spawning does not create new project entitlement;
- blocked/waiting tasks do not consume runnable share;
- provider/tool quotas remain separately enforced.

DBOS partition concurrency may enforce per-project concurrency/flow control if DBOS is retained, but SwarmAI remains responsible for which mission/task is eligible and fair to enqueue.

## Mission/task choice

Within project:
- dependencies ready;
- cancellation state valid;
- task priority;
- deadline/slack;
- aging to prevent starvation;
- required capability/trust/locality available;
- no duplicate accepted attempt/effect.

## Resource reservation

Scheduler does not assume capacity because a worker exists.

Task enters dispatched state only when needed reservations are atomically acquired:
- worker slot/lease;
- provider request/token bucket as needed;
- tool/effect gate where applicable;
- artifact/workspace capacity if constrained.

If partial reservation fails, release/reconcile acquired reservations before another task.

## Backpressure

Per-project and global:
- max runnable queue depth;
- max active missions/tasks;
- bounded graph growth;
- provider request/token envelopes;
- worker class capacity;
- tool side-effect concurrency.

Overload response is queued/blocked/rejected according to policy, not silent unbounded memory growth.

## Cancellation/drain

Mission cancellation removes not-started tasks from eligibility and fences active attempts.
Project pause prevents new dispatch but may allow safe read/compute tasks to drain according to policy.
Worker/site drain uses V1.5 protocol.

## Evidence

V2.3 acceptance should include:
- two projects with different weights both progress;
- high-weight gets larger share without starving low-weight;
- one project spawning many tasks cannot monopolize;
- deadline pressure changes order within bound;
- shared provider quota never double allocates;
- project data/knowledge/artifacts remain isolated;
- cancellation frees/reconciles resources;
- scheduler state survives restart.

## Implementation packets later

- V23A-001 SP2: ProjectQueueState + policy.
- V23A-002 SP3: fair scheduler/admission integration.
- V23A-003 SP2: backpressure/aging/deadline tests.
- V23A-004 SP2: observability/explain API.
