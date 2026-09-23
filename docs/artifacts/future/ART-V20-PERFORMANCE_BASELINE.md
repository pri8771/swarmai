# ART-V20-PERFORMANCE-BASELINE — integrated performance/resource protocol

Status: drafting
Target: V2.0
Owner: ChatGPT lead

Purpose: establish real operating characteristics and detect pathological overhead. It is not a marketing benchmark and it does not substitute for live acceptance, reliability, security, or qualification evidence.

## 1. Benchmark identity and freeze

Every counted run belongs to one immutable benchmark campaign identity. Before the first counted sample, record and freeze:
- exact integrated candidate SHA and dirty-tree status;
- benchmark protocol version/digest;
- workload manifest version/digest;
- qualification/routing profile versions;
- database schema/Alembic head;
- host CPU/RAM/GPU class and power-mode assumptions;
- OS, Python/Node/runtime versions;
- DB/storage class and dataset size;
- local model identity/config/context/quantization where used;
- remote route identities and exact price/eligibility state where used;
- worker count/topology and host aliases;
- relevant feature flags and concurrency limits.

A source/config/schema/workload change that can materially affect results starts a new campaign identity. Never splice samples from incompatible identities.

Unknown values remain `unknown`; do not infer hardware, provider cost, token counts, or model availability.

## 2. Measurement discipline

For latency/throughput measurements:
- separate warm-up from counted samples;
- use monotonic elapsed time for process-local timings;
- preserve individual sample records, not only aggregates;
- record success/failure/retry/cancel outcomes for every counted attempt;
- report at minimum count, median, p95 and max when sample count is sufficient;
- do not report p95 from fewer than 20 counted observations; use raw values + median/max instead;
- include queue wait separately from execution/inference latency;
- measure end-to-end user-visible latency separately from internal stage latency;
- preserve failures instead of rerunning until a clean chart appears.

Default counted depth for repeatable deterministic/control-plane paths is >=30 successful-or-failed attempts per case after warm-up. Model-backed workloads may use smaller preregistered counts when cost/time is constrained, but the exact n must be frozen before results and reported without pretending statistical precision that the sample cannot support.

## 3. Resource accounting

Where observable without adding paid telemetry, capture:
- wall-clock duration;
- process/system CPU utilization;
- process and system resident memory, including peak RSS where available;
- GPU utilization/VRAM where applicable;
- DB size, connection count and query count where practical;
- artifact bytes written/read;
- worker processes/sessions and queue depth;
- in-flight model requests;
- model calls, input/output tokens and retries when reported by the route;
- remote usage/cost or explicit `unknown`;
- failure/retry/cancellation counts.

Instrumentation must not leak prompts, secrets, private identities, credentials, cookies, hidden benchmark answers, or raw sensitive payloads.

## 4. Workload classes

### P1 — control-plane baseline

Exercise supported create/list/get/cancel mission flows plus project/worker/approval and artifact/history reads.

Measure API latency, queueing, DB activity and memory. Include at least one denied/invalid request path so fail-closed behavior is measured rather than only happy-path throughput.

### P2 — single local mission

Run one supported S and one supported M mission using a currently qualified/admitted local route.

Measure:
- end-to-end latency;
- queue wait;
- inference latency;
- model calls/tokens;
- planning/review/tool overhead;
- DB/artifact writes;
- peak process memory/VRAM where observable.

The task input must not be a known-answer fixture used to make the runtime appear successful.

### P3 — concurrent missions

Run bounded concurrent supported missions at 2, 5 and 10 concurrency where the declared host support envelope permits.

Measure:
- completed throughput;
- queue wait distribution;
- per-mission slowdown versus P2;
- fairness/starvation indicators;
- error/retry/cancel rate;
- worker/broker saturation;
- memory growth and recovery after load drains.

This is not a claim that every installation supports ten concurrent reasoning jobs. If a host's declared capacity is below a level, record that level as unsupported rather than bypassing admission controls.

### P4 — distributed worker

When ART-V15 durable worker semantics and real multi-host evidence exist, use two actual workers/hosts.

Measure:
- registration/heartbeat overhead;
- dispatch/claim latency;
- lease-renewal overhead;
- result submission/acceptance latency;
- reassignment latency after one worker loss;
- stale-result rejection latency and duplicate-attempt count.

Never simulate the second host for counted distributed evidence.

### P5 — knowledge

Compare on the same preregistered task set:
- source reload/no reusable knowledge;
- permission-scoped reusable knowledge retrieval.

Measure retrieved tokens/bytes, context reduction, retrieval latency, end-to-end latency and task-quality outcome. Permission filtering occurs before ranking; a faster leaking path is a failure, not an optimization.

### P6 — tool/action

Use a read-only action and one explicitly approved idempotent local side effect.

Measure gateway/policy overhead, receipt persistence and duplicate-retry behavior. A duplicate accepted effect is an acceptance blocker regardless of latency.

### P7 — backup/restore

On a supported private deployment, record backup size/time plus actual restore/reconcile time, restored object counts, site/epoch reconciliation and any recovery-induced data loss window.

Do not use a synthetic success flag in place of a real restore.

## 5. Comparison rules

When comparing two configurations:
- use the same candidate/workload dataset unless the changed variable necessarily changes it;
- change one declared variable at a time where practical;
- preserve admission limits rather than disabling them for higher numbers;
- distinguish cold-start and steady-state results;
- state whether model outputs were semantically successful; failed model tasks are not throughput wins;
- report both absolute measurements and deltas;
- do not compare measurements from incompatible campaign identities as if they were controlled A/B results.

## 6. Required evidence bundle

A reviewable performance artifact must include:
1. campaign manifest with exact source/config/environment identities;
2. workload manifest and preregistered sample counts;
3. raw machine-readable sample records;
4. aggregation script/version or reproducible aggregation procedure;
5. summary table with success/failure counts and supported percentile semantics;
6. resource traces/snapshots where available;
7. anomaly/failure log, including reruns and invalidated samples;
8. explicit unsupported/not-measured fields;
9. lead review binding the evidence to the exact candidate SHA.

Charts are optional; raw records and reproducible summaries are mandatory.

## 7. Pathology / blocker rules

V2.0 needs a reproducible baseline and absence of pathological/unbounded behavior within its declared support envelope, not an arbitrary universal speed threshold.

A result blocks support/acceptance if it demonstrates any of the following without an accepted mitigation/retest:
- deadlock or livelock;
- unbounded queue, process, memory, artifact or DB growth inside declared bounds;
- severe persistent fairness starvation;
- duplicate accepted effects or duplicate accepted task results;
- stale/cancelled/superseded work accepted after its authority was revoked;
- admission/quota bypass under load;
- resource use that contradicts declared minimum requirements;
- sustained failure/retry loops that can consume unbounded local/remote inference;
- benchmark instrumentation that changes protected semantics or exposes hidden/sensitive data.

Performance regressions that are finite but material must be documented in the support matrix/release review even when they are not release blockers.

## 8. Acceptance semantics

`ART-V20-PERFORMANCE-BASELINE` can be independently verified only when a frozen V2 candidate has a reproducible evidence bundle covering every workload class applicable to the declared support matrix, with unsupported classes explicitly identified and no unresolved blocker-class pathology.

Verification of this artifact does **not** imply:
- the 168-hour reliability window elapsed;
- G12 remote overlap passed;
- G13 model qualification passed;
- LIVE-142 passed;
- security review passed;
- public release is authorized.

Publish hardware/context with every number. Never generalize one private host benchmark into a universal product maximum.