# SwarmAI artifact-derived execution queue — after LEAD-20260921-035

Canonical lifecycle is `ARTIFACT_REGISTRY.json`. Immediate target remains a V2.0 implementation/artifact-complete candidate; main merge, public release, additional spend, and elapsed-time acceptance gates remain separately gated.

## Current source and liveness

- A / `cursor/v2-runtime-lane`: `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`; no newer implementation commit. Exact-tip CI remains red from the shared autonomous-runner source.
- B / `cursor/v2-product-lane`: `6b0e1277051ae90fe1d56825d3e771b042380755`; no newer implementation commit. Exact-tip CI remains red from the same shared source.
- Reviewed integration: `cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b`, reviewed code lineage `ee5a06612aa2e4409fa8bbfd1969225c16887615`.
- Heartbeat bootstrap is now complete. A's counted graduation chain is `13:21:56Z -> 13:36:58Z -> 13:52:01Z`; B's counted graduation chain is `13:14:17Z -> 13:29:18Z -> 13:44:19Z`. All counted receipts have `trigger=scheduler` and every adjacent gap is within 10-25 minutes.
- `HEARTBEAT_STATE.json` is graduated to `mode=hourly` with `worker_effective_cadence_minutes=60` at `2026-09-21T13:56:51Z`. OS schedulers may continue waking every 15 minutes; clients must self-throttle publication to the effective cadence.
- `ART-OPS-HEARTBEAT` remains drafting until post-graduation behavior is observed; bootstrap graduation alone is not being overclaimed as lifecycle acceptance.
- No repo-assigned autonomous self-launch plus attributable source push is verified from either A or B. Heartbeat liveness is not autonomous implementation evidence.

## Heartbeat stress test — owner reset 2026-09-21

The prior 15m bootstrap was verified and is preserved as historical evidence. The owner intentionally started a new reliability exercise:

1. **Phase 1:** A and B publish scheduler heartbeats at effective 5-minute cadence. Each needs 3 consecutive counted scheduler receipts, with adjacent gaps 3–8 minutes.
2. **Phase 2:** after both Phase-1 streaks are lead-verified, set effective cadence to 15 minutes for **24 real hours**. Preserve every miss; do not backfill.
3. **After soak:** only after the full 24-hour window is verified may effective cadence return to hourly.

OS scheduler installers now wake every 5 minutes; the heartbeat client self-throttles according to `HEARTBEAT_STATE.json`.
ChatGPT lead automation remains hourly and validates the worker histories retrospectively.

## External worker-pc — G13 task-pool critical path

`pri8771/remote-workers` is execution infrastructure only; SwarmAI remains project authority.

Retry 04 remains the last reviewable source result:
- task `swarmai-v13-task-pool-freeze-04`
- branch `worker/swarmai-v13-task-pool-freeze-04`
- commit `6467552f86e40964e5bd26d85e3b3a74d03aa059`
- parent `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- SwarmAI CI `35587202715`: Ruff/mypy/packaging/Alembic/console pass, ordinary offline pytest fails.
- lead disposition: changes required; `ART-V13-TASK-POOL` remains drafting; W-131B counted qualification prohibited.

Retry 05 is closed as transport failure/non-evidence:
- task `swarmai-v13-task-pool-freeze-05`
- remote-workers run `35596577823`, job `106322668369`
- sanitized result exists with `status=failed`, `failure_class=worker branch push failed`, `branch=null`, `commit=null`
- expected branch `worker/swarmai-v13-task-pool-freeze-05` does not exist.
Because no source branch/commit exists, retry 05 cannot satisfy independent review or artifact evidence.

Fresh retry 06 is now executing the same bounded R3 repair:
- task `swarmai-v13-task-pool-freeze-06`
- dispatch commit `bc14ddf4430039e7474b9f63cf6219b1243b4c11`
- remote-workers run `35608406904`, job `106361127740`
- base `worker/swarmai-v13-task-pool-freeze-04@6467552f86e40964e5bd26d85e3b3a74d03aa059`
- expected branch `worker/swarmai-v13-task-pool-freeze-06`
- at lead review cutoff, `Execute submitted tasks` is in progress and no retry-06 result/branch is yet reviewable.

R3 acceptance remains: exact-tip offline pytest green without weakened assertions; truthful provenance; >=15 genuinely independent semantic archetypes/groups per required family/size cell; mechanical rejection of semantic/template siblings; worker-visible input-only held-out records; contamination rejection preserved; no fabricated sealed-reference digest; `counted_qualification_ready=false` until a real lead-controlled sealed bundle is bound; no W-131B counted qualification before lead freeze.

Remote capacity is 1. Retry 06 currently owns worker-pc; any other submitted task must wait rather than overlap execution.

## Session A — assignment generation 2

### A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Assignment `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, remains enabled with only `OPS-AUTO-001-R`. Repair exact-tip autonomous-runner/heartbeat Ruff failures while preserving one-packet/generation, clean-worktree, branch/no-force-push/no-self-accept/fail-closed semantics. Add focused regressions and push exact-tip green evidence.

A heartbeat scheduler is healthy and has completed bootstrap, but there is still no autonomous-start/blocker receipt or attributable generation-2 implementation push. Do not replay generation 1.

### A1 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2 — only after A0 lead review/new generation
Repair generic model-response -> isolated-worktree materialization without target-specific logic or known answers; preserve the first genuine failed mission and run a newly preregistered real local brokered mission after repair.

### A2 — V2A-003c / ART-V15-LEASE-FENCING / SP2
Durable result acceptance: current worker/project/generation, current unexpired lease bound to attempt/task, source/revision/cancellation authority match, stale/cancelled/superseded denial, duplicate idempotence, exactly one accepted result under race.

### A3 — reviewed-slice integration receipt / SP1
After A2 lead review, integrate only independently reviewed slices into `cursor/v2-integration`; run integrated CI and bind receipt to exact SHAs.

### A4 — V2A-004 / ART-V15-WORKER-PROTOCOL / SP3
After result acceptance: durable registration/heartbeat/claim/result/drain service/client, restart-safe tests, then real multi-host evidence.

### A-G12 — remote overlap blocked
0 admitted remote routes. Do not canary unknown-cost routes; exact account free-tier/model zero-price/quota/health/bounded-canary eligibility must be independently established first.

## Session B — generation 2 remains held

Assignment `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, remains disabled until A0 is independently reviewed/propagated. Do not replay generation 1 and do not duplicate external G13 ownership.

### B0 — V2B-000 / ART-V20-INTEGRATED-CANDIDATE / SP1
After safe re-enable: sync only reviewed integration baseline, preserve host/session files, run Windows Python+console baseline, push exact evidence.

### B1-external — ART-V13-TASK-POOL / SP2
Retry 06 is executing through `worker-pc`; local B must not duplicate it. No counted qualification before independent lead freeze plus real sealed-reference binding.

### B2-local — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair/freeze after B0 when autonomy is safely re-enabled and file ownership is independent. No held-out qualification claim.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Only after lead accepts/freeze-binds the repaired task pool and a real sealed reference bundle is bound. Preserve every attempt and total overhead; no post-result threshold changes.

### B4 — reviewer held-out qualification
Only after B2 design freeze; required before G14 role manifest.

### B5 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned provenance/tombstones/non-leak tests; B owns domain/repository and hands central migration delta to A.

### B6 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope / ApprovalGrant / ActionReceipt exact project/operation/destination/payload binding, expiry/revocation and explicit test fixtures only.

## Retained independent review decisions

- V2A-003b-R2 / SP1: accepted packet; parent V15 lease fencing still drafting pending V2A-003c.
- V2A-H6A-R / SP1: accepted packet; parent V20 hardening still drafting.
- V2A-003X / SP2: accepted spike; partial DBOS reuse only.
- V14-REAL-001 / SP2: changes required; genuine brokered local mission failed on empty material diff and is preserved as failure.
- A5-LOCAL-G12-CURRENT-TIP / SP2: accepted live-local proof only; no remote claim.
- EXT-WORKER-PC-V2B-001-02 / SP2: changes required.
- retry 03: cancelled/non-evidence.
- retry 04: changes required at `6467552f86e40964e5bd26d85e3b3a74d03aa059`.
- retry 05: failed worker branch push; sanitized result but no branch/commit; non-evidence.

`WORKER_PERFORMANCE.json` remains unchanged because retry 05 produced no reviewable source and retry 06 has not completed. Heartbeat receipts are coordination evidence, not implementation-performance evidence.

## Honest blocked acceptance artifacts

- `ART-OPS-HEARTBEAT`: bootstrap 3/3 requirement met and effective cadence graduated to hourly; post-graduation hourly self-throttle evidence still pending before lifecycle promotion.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- `ART-V10-WORKER-HEARTBEAT`: authenticated Cursor-agent receipts absent.
- `ART-V12-REMOTE-OVERLAP`: 0 admitted remotes.
- `ART-V13-TASK-POOL`: drafting; retry 04 changes-required, retry 05 non-evidence, retry 06 in progress.
- `ART-V13-QUALIFIED-MATRIX`: zero qualified cells.
- `ART-V14-REAL-E2E`: first real attempt failed; repair waits behind A0.
- G14 role/live-adaptive proof: blocked on G12/G13.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock cannot be backfilled.
- V2.0 reliability observation: not started; 168-hour clock remains real.
