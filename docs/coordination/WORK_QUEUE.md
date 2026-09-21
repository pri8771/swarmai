# SwarmAI artifact-derived execution queue — after LEAD-20260921-033

Canonical lifecycle is `ARTIFACT_REGISTRY.json`. Immediate target remains a V2.0 implementation/artifact-complete candidate; acceptance/live windows/main merge/public release/additional spend remain separately gated.

## Current source and liveness

- A / `cursor/v2-runtime-lane`: `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`; exact-tip CI `35558067148` remains red in the offline job from the shared autonomous-runner source.
- B / `cursor/v2-product-lane`: `6b0e1277051ae90fe1d56825d3e771b042380755`; exact-tip CI `35558073323` remains red from the same shared source.
- Reviewed integration: `cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b`, reviewed code lineage `ee5a06612aa2e4409fa8bbfd1969225c16887615`.
- A scheduler: a fresh scheduler receipt resumed at `11:55:14Z` after the long outage. The old 2/3 chain is broken, so the current chain is **1/3**; A is no longer stale.
- B scheduler: `11:14:17Z -> 11:29:17Z -> 11:44:27Z` = **3/3** with valid 10–25 minute gaps; B individually satisfies bootstrap cadence.
- Global worker cadence remains 15 minutes because both lanes must be 3/3 simultaneously. No repo-assigned autonomous self-launch/push is verified on A or B.

## External worker-pc — G13 task-pool critical path

`pri8771/remote-workers` is execution infrastructure only; SwarmAI remains project authority.

Retry 04 remains independently reviewed changes-required:
- task `swarmai-v13-task-pool-freeze-04`
- worker branch `worker/swarmai-v13-task-pool-freeze-04`
- commit `6467552f86e40964e5bd26d85e3b3a74d03aa059`
- parent `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- remote-workers run `35580580156`, job `106272271934`
- remote task execution succeeded and branch push occurred, but sanitized result publication failed; result JSON is absent
- exact-tip SwarmAI CI `35587202715`: Ruff/mypy/packaging/Alembic pass, console passes, **offline pytest fails**.

Lead disposition remains **changes required**. `ART-V13-TASK-POOL` remains drafting and counted W-131B qualification remains prohibited.

Main repair findings remain:
1. exact-tip offline pytest must be green;
2. v2 evidence provenance must report the actual pushed commit instead of saying the branch is uncommitted;
3. the current `5 task variants x 3 structural loads` construction is not mechanically sufficient to prove 15 independent observations per cell because ordinary scenario/domain substitutions and incremental clause changes can evade the current template normalizer;
4. no lead-controlled sealed-reference bundle/content digest is bound, so counted readiness must remain false.

Lead review: `docs/coordination/reviews/ART-V13-TASK-POOL-RETRY04-LEAD-REVIEW.md`.
Repair contract: `docs/coordination/packets/EXT-WORKER-PC-V2B-001-R3.md`, requiring a green exact-tip suite and >=15 distinct semantic independence groups/archetypes per required cell, with direct negatives for scenario-name/seed-isomorphic siblings.

`worker-pc` capacity became free after unrelated run `35590523591` completed. The lead dispatched retry 05:
- task `swarmai-v13-task-pool-freeze-05`
- remote-workers dispatch commit `d12ec01e9d741f4ac117c074190811a4d48d0e41`
- workflow run `35596577823`
- base `worker/swarmai-v13-task-pool-freeze-04@6467552f86e40964e5bd26d85e3b3a74d03aa059`
- expected worker branch `worker/swarmai-v13-task-pool-freeze-05`
- state at dispatch review: **queued**; no result/worker commit is claimed yet.

Lead-owned sealed-reference preregistration: `docs/coordination/G13_SEALED_REFERENCE_BINDING_PROTOCOL.md`. It does not create or claim a hidden bundle; a real non-worker-readable bundle and binding receipt remain prerequisites.

## Session A — assignment generation 2

### A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Assignment `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled. Repair exact-tip autonomous-runner/heartbeat Ruff failures while preserving one-packet/generation, clean-worktree, branch/no-force-push/no-self-accept/fail-closed semantics. Add focused regressions and push exact-tip green evidence.

A's scheduler has resumed but no autonomous-start or implementation push is observed yet. Keep generation 2 unchanged; do not replay older packets.

### A1 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2 — only after A0 lead review/new generation
Repair generic model-response -> isolated-worktree materialization without target-specific logic/known answers; preserve the first genuine failed mission and run a newly preregistered real local brokered mission after the repair.

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
Retry 05 is dispatched through `worker-pc`; local B must not duplicate it. No counted qualification before independent lead freeze plus sealed-reference binding.

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
- EXT-WORKER-PC-V2B-001-R1: cancelled without result/branch; non-evidence.
- EXT-WORKER-PC-V2B-001-R2 / retry 04: changes required at `6467552f86e40964e5bd26d85e3b3a74d03aa059`.

`WORKER_PERFORMANCE.json` summary counts remain unchanged this run because no new bounded implementation packet reached independent lead review. Dispatching retry 05 is not review evidence.

## Honest blocked acceptance artifacts

- `ART-OPS-HEARTBEAT`: A current chain 1/3 after scheduler recovery; B current chain 3/3; no global hourly graduation.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- `ART-V10-WORKER-HEARTBEAT`: authenticated Cursor-agent receipts absent.
- `ART-V12-REMOTE-OVERLAP`: 0 admitted remotes.
- `ART-V13-TASK-POOL`: drafting; retry 04 changes-required; retry 05 dispatched/queued for R3 repair.
- `ART-V13-QUALIFIED-MATRIX`: zero qualified cells.
- `ART-V14-REAL-E2E`: first real attempt failed; repair waits behind A0.
- G14 role/live-adaptive proof: blocked on G12/G13.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock cannot be backfilled.
- V2.0 reliability observation: not started; 168-hour clock remains real.
