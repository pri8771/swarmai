# SwarmAI artifact-derived execution queue — after LEAD-20260921-031

Canonical lifecycle is `ARTIFACT_REGISTRY.json`. Immediate target remains a V2.0 implementation/artifact-complete candidate; acceptance/live windows/main merge/public release/additional spend remain separately gated.

## Current source and liveness

- A / `cursor/v2-runtime-lane`: `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`; exact-tip CI `35558067148` remains red in the offline job from the shared autonomous-runner source.
- B / `cursor/v2-product-lane`: `6b0e1277051ae90fe1d56825d3e771b042380755`; exact-tip CI `35558073323` remains red from the same shared source.
- Reviewed integration: `cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b`, reviewed code lineage `ee5a06612aa2e4409fa8bbfd1969225c16887615`.
- A scheduler: `03:47:19Z -> 04:02:22Z` = **2/3**, stale; no later scheduler receipt observed.
- B scheduler: current valid chain is `07:29:17Z -> 07:44:17Z -> 07:59:17Z -> 08:14:27Z -> 08:29:18Z -> 08:44:17Z -> 08:59:27Z -> 09:14:18Z -> 09:29:17Z -> 09:44:17Z` = **10 consecutive valid scheduler receipts**. B individually satisfies bootstrap cadence, but global cadence remains 15 minutes because A does not.
- No new A/B implementation commit or repo-assigned autonomous self-launch/push is verified.

## External worker-pc — G13 task-pool critical path

`pri8771/remote-workers` is execution infrastructure only; SwarmAI remains project authority.

- Attempt 01 `swarmai-v13-task-pool-freeze-01`: cancelled before result/branch; non-evidence.
- Attempt 02: `worker/swarmai-v13-task-pool-freeze-02@bbe41b7770123fef4eb03c4f03f95fc18eefc692`; independently reviewed **changes required** because worker-visible hidden references exist, held-out depth is 5/cell rather than >=15, seed-isomorphic variants remain, and no Python/pytest/Ruff/mypy/CI actually ran.
- Attempt 03: `swarmai-v13-task-pool-freeze-03`, remote-workers commit `cbdaaab46142e2165084a15157f1aabd8180483d`, run `35566726945`, job `106229937621`; cancelled with no result JSON and no worker branch. This is not implementation evidence.
- Lead narrowed the retry contract in `docs/coordination/packets/EXT-WORKER-PC-V2B-001-R2.md` at coordination commit `d67ed2bc07f7239220cdf7e4c8aca32f2ccbd0c8`.
- Attempt 04 is actively executing as `swarmai-v13-task-pool-freeze-04`, remote-workers commit `f3eeb62f836ece720f80e5e79a0a8a461c8e39cc`, workflow run `35580580156`, job `106272271934`. At this review the job remained in `Execute submitted tasks`; result JSON was absent and `worker/swarmai-v13-task-pool-freeze-04` did not yet exist.

`ART-V13-TASK-POOL` remains **drafting**. Counted qualification remains prohibited until the lead independently freezes a compliant v2 task pool.

## Session A — assignment generation 2

### A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Assignment `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled. Repair exact-tip autonomous-runner/heartbeat Ruff failures while preserving one-packet/generation, clean-worktree, branch/no-force-push/no-self-accept/fail-closed semantics. Add focused regressions and push exact-tip green evidence.

A is stale and has not started this generation. Restore the local Mac heartbeat/autonomous LaunchAgents before expecting autonomous execution.

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
Attempt 04 is the active external repair. Local B must not duplicate it. No counted qualification before independent lead freeze.

### B2-local — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair/freeze after B0 when autonomy is safely re-enabled and file ownership is independent. No held-out qualification claim.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Only after lead accepts/freeze-binds the repaired task pool. Preserve every attempt and total overhead; no post-result threshold changes.

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
- EXT-WORKER-PC-V2B-001-02 / SP2: changes required; real scoped branch but hidden-reference/depth/independence/executed-test gates fail.
- EXT-WORKER-PC-V2B-001-R1 / retry 03: cancelled without result/branch; no performance score or artifact transition.

`WORKER_PERFORMANCE.json` remains unchanged because no new bounded implementation packet reached independent source/evidence review.

## Honest blocked acceptance artifacts

- `ART-OPS-HEARTBEAT`: A 2/3 stale; B individually complete at 10 consecutive valid receipts; no global hourly graduation.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- `ART-V10-WORKER-HEARTBEAT`: authenticated Cursor-agent receipts absent.
- `ART-V12-REMOTE-OVERLAP`: 0 admitted remotes.
- `ART-V13-TASK-POOL`: drafting; retry 02 changes-required, retry 03 cancelled, retry 04 actively executing/unreviewed.
- `ART-V13-QUALIFIED-MATRIX`: zero qualified cells.
- `ART-V14-REAL-E2E`: first real attempt failed; repair waits behind A0.
- G14 role/live-adaptive proof: blocked on G12/G13.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock cannot be backfilled.
- V2.0 reliability observation: not started; 168-hour clock remains real.

## Lead lane

`ART-V13-TASK_POOL_REPAIR_CONTRACT.md` plus bounded retry packet `EXT-WORKER-PC-V2B-001-R2.md` define the current G13 repair boundary. `ART-V20-SECURITY-REVIEW` and `ART-V20-RELIABILITY-PROTOCOL` remain drafting. `ART-V20-PERFORMANCE-BASELINE` was advanced in `docs/artifacts/future/ART-V20-PERFORMANCE_BASELINE.md` at `ddfc8f969ab66684697fa822279da441a197421e` with frozen campaign identity, measurement discipline, resource accounting, fail-closed pathology rules and reproducible evidence requirements. No benchmark execution or performance acceptance is claimed.
