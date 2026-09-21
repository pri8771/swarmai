# ART-V20-PERFORMANCE-BASELINE — integrated performance/resource protocol

Status: drafting
Target: V2.0
Owner: ChatGPT lead

Purpose: establish real operating characteristics and detect pathological overhead. It is not a marketing benchmark.

## Freeze

Record:
- candidate SHA;
- host CPU/RAM/GPU class;
- OS/runtime;
- DB/storage;
- local model/config;
- remote route identities if used;
- worker count/topology;
- qualification/routing profile versions.

## Workload classes

### P1 — control-plane baseline
- create/list/get/cancel missions;
- project/worker/approval reads;
- artifact/history retrieval.

Measure API latency and DB queries where practical.

### P2 — single local mission
One supported S and M mission.

Measure:
- end-to-end latency;
- inference latency;
- model calls/tokens;
- planning/review overhead;
- DB/artifact writes;
- peak process memory.

### P3 — concurrent missions
Run bounded concurrent supported missions:
- 2;
- 5;
- 10 where host capacity permits.

Measure:
- throughput;
- queue wait;
- fairness;
- error/retry rate;
- worker/broker saturation.

This is not a claim that every installation supports ten concurrent reasoning jobs.

### P4 — distributed worker
Two workers/hosts when available:
- dispatch latency;
- heartbeat/claim overhead;
- result/acceptance latency;
- reassignment after one worker loss.

### P5 — knowledge
Compare:
- no reusable knowledge / source reload;
- permission-scoped knowledge retrieval.

Measure retrieved tokens, context reduction, retrieval latency and task quality.

### P6 — tool/action
Read-only and one approved idempotent local side effect.
Measure policy/gateway overhead and duplicate-retry behavior.

### P7 — backup/restore
Record backup size/time and actual restore/reconcile time.

## Required resource accounting

- wall-clock;
- CPU/RAM where observable;
- DB size/query counts where practical;
- artifact bytes;
- worker processes/sessions;
- in-flight model requests;
- model calls/tokens;
- remote usage/cost or explicit unknown.

## Gate semantics

V2.0 needs a reproducible baseline and absence of pathological/unbounded behavior, not an arbitrary universal speed threshold.

A result blocks candidate support if it shows:
- deadlock/livelock;
- unbounded queue/memory growth in declared bounds;
- severe fairness starvation;
- duplicate accepted effects/results;
- resource use that contradicts declared minimum requirements.

Publish hardware/context with all numbers. Never generalize one local host benchmark into a product maximum.
