# SwarmAI artifact-derived execution queue — after LEAD-20260921-027

Canonical lifecycle: `ARTIFACT_REGISTRY.json`. This is a derived execution view. Immediate target remains a V2.0 implementation/artifact-complete candidate; acceptance/live windows/main merge/public release/additional spend remain separately gated.

## Current source and liveness

- A / `cursor/v2-runtime-lane`: `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, Actions `35558067148` red offline Ruff from shared autonomous-runner source; console path had been green.
- B / `cursor/v2-product-lane`: `6b0e1277051ae90fe1d56825d3e771b042380755`, prior exact-tip CI red from the same shared source.
- Reviewed integration remains `9ce727842446b98cfa55c28c7e70808f57f17d7b` / code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.
- A scheduler: `03:47:19Z -> 04:02:22Z` = **2/3**, now stale.
- B scheduler: valid sequence through `05:29:17Z` = **8 consecutive**, individually complete/fresh.
- Global worker publication cadence remains 15 minutes until A reaches 3/3; ChatGPT lead remains hourly.
- No new A/B implementation commit or repo-assigned autonomous self-launch/push is verified.

## External worker-pc — G13 task-pool critical path

Infrastructure is `pri8771/remote-workers` only; SwarmAI remains project authority.

### Attempt 01
`swarmai-v13-task-pool-freeze-01`: cancelled before result/worker branch. Non-evidence.

### Attempt 02 — reviewed, changes required
- worker branch: `worker/swarmai-v13-task-pool-freeze-02`
- commit: `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- parent: exact reviewed integration `9ce727842446b98cfa55c28c7e70808f57f17d7b`
- result JSON exists and source diff is scoped to evaluation/benchmark/evidence/tests.

Useful output: stable pool/record hashes, family/size mapping, identity pins, deterministic verifier/test source, explicit `qualification_claimed=false`.

Independent rejection reasons:
1. worker-visible `benchmarks/starter.jsonl` contains hidden answer/grader/reference material;
2. only 5 held-out cases per required family/size cell, below EVAL-131 minimum 15 independent observations for possible qualification;
3. seed-isomorphic held-out variants remain, so independence is not established;
4. Python/pytest/Ruff/mypy were denied in the remote executor and no workflow ran at `bbe41b...`.

`ART-V13-TASK-POOL` therefore remains **drafting**. No counted qualification.

### Attempt 03 — active repair
Lead created `docs/artifacts/current/ART-V13-TASK_POOL_REPAIR_CONTRACT.md` and dispatched:
- task: `swarmai-v13-task-pool-freeze-03`
- packet: `EXT-WORKER-PC-V2B-001-R1`
- base: `worker/swarmai-v13-task-pool-freeze-02`
- expected branch: `worker/swarmai-v13-task-pool-freeze-03`
- remote-workers dispatch: `cbdaaab46142e2165084a15157f1aabd8180483d`
- workflow: `35566726945`, `in_progress` at last check.

Repair requires a new v2 freeze with input-only worker-visible held-out tasks, sealed grader-reference identity, >=15 independent held-out inputs for each required coding/planning/reasoning/extraction × S/M/L/XL cell, hard contamination/independence checks, frozen identities and actually executed verification evidence. It still must not run counted qualification or self-accept.

## Session A — assignment generation 2

### A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Assignment `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, remains enabled. Repair exact-tip autonomous-runner/heartbeat Ruff failures while preserving fail-closed one-packet/generation, clean-worktree, branch/no-remote-change/no-force-push/no-self-accept semantics. Add focused regressions and push exact-tip green evidence. A is stale and has not produced this packet yet.

### A1 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2 — after A0 lead review/new generation
Repair generic model-response -> isolated-worktree materialization without target-specific logic/known answers; add unrelated valid-patch and malformed/no-op regressions; preregister/run a new actual local brokered mission on a different bounded subsystem. Preserve first failed evidence.

### A2 — V2A-003c / ART-V15-LEASE-FENCING / SP2
Durable result acceptance: current worker/project/generation; current lease bound to attempt/task and unexpired; task/attempt revision, source revision and cancellation generation match authority; stale/cancelled/superseded denial; duplicate idempotence; exactly one accepted result under race.

### A3 — reviewed-slice integration receipt / SP1
After A2 lead review, integrate only independently reviewed V15/H6A slices into `cursor/v2-integration`; run integrated CI and bind receipt to exact SHAs.

### A4 — V2A-004 / ART-V15-WORKER-PROTOCOL / SP3
After result acceptance: durable registration/heartbeat/claim/result/drain service/client, restart-safe tests, then actual Mac+Windows multi-host evidence.

### A-G12 — remote overlap blocked
0 admitted remote routes. Do not canary unknown-cost routes. Exact account free-tier/model zero-price/quota/health/bounded-canary eligibility must be independently established first.

## Session B — generation 2 remains held

Assignment `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, stays disabled until A0 is independently reviewed/propagated. B heartbeat remains healthy; product autonomy is intentionally separate from liveness.

After the shared repair, publish a new enabled generation. Do not replay generation 1 and do not duplicate external G13 ownership.

### B0 — V2B-000 / ART-V20-INTEGRATED-CANDIDATE / SP1
Sync only reviewed integration baseline, preserve branch-local host/session files, run Windows Python+console baseline, push exact evidence.

### B1-external — ART-V13-TASK-POOL repair / SP2
**Active as external repair 03.** Local B must not duplicate it. Counted qualification is prohibited until independent lead freeze.

### B2-local — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair and freeze. May proceed after B0 when local autonomy is safely re-enabled and ownership is independent of external task-pool files. No held-out qualification before lead freeze.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Only after lead accepts/freeze-binds the repaired task pool. Preserve every attempt and total overhead. No post-result threshold changes.

### B4 — reviewer held-out qualification
Only after B2 design freeze; required before G14 role manifest.

### B5 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned provenance/tombstones/non-leak tests; B owns domain/repository and hands central migration delta to A.

### B6 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope / ApprovalGrant / ActionReceipt exact project/operation/destination/payload binding, expiry/revocation and explicit test fixtures only.

## Retained independent review decisions

- V2A-003b-R2 / SP1: accepted packet; parent V15 lease fencing still drafting pending V2A-003c.
- V2A-H6A-R / SP1: accepted packet; parent V20 hardening still drafting.
- V2A-003X / SP2: accepted spike, partial DBOS reuse recommendation only.
- V14-REAL-001 / SP2: changes required; genuine brokered local mission failed on empty material diff and was correctly rejected.
- A5-LOCAL-G12-CURRENT-TIP / SP2: accepted live-local proof only; no remote claim.
- EXT-WORKER-PC-V2B-001-02 / SP2: changes required; real scoped branch, but hidden-reference/depth/independence/executed-test gates fail.

`WORKER_PERFORMANCE.json` records the remote SP2 review; SP2 first-review acceptance is now 5/12.

## Honest blocked acceptance artifacts

- `ART-OPS-HEARTBEAT`: A 2/3 stale; B 8 consecutive; global still drafting.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- `ART-V10-WORKER-HEARTBEAT`: authenticated Cursor-agent receipts absent.
- `ART-V12-REMOTE-OVERLAP`: 0 admitted remotes.
- `ART-V13-TASK-POOL`: drafting; retry 02 changes-required, repair 03 active.
- `ART-V13-QUALIFIED-MATRIX`: zero qualified cells.
- `ART-V14-REAL-E2E`: first real attempt failed; repair/rerun waits behind A0.
- G14 role/live adaptive proof: blocked on G12/G13.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock cannot be backfilled.
- V2.0 reliability observation: not started; 168-hour clock remains real.

## Lead lane

Primary lead artifact advanced this run: `ART-V13-TASK_POOL_REPAIR_CONTRACT.md`, which closes ambiguity around hidden-reference isolation, independent pool depth and freeze-v2 readiness before counted qualification.

`ART-V20-RELIABILITY-PROTOCOL` remains drafting with campaign identity/reset/checkpoint/gap/no-splicing semantics. No campaign time is claimed.

Continue V2 security/recovery/integration acceptance and V2.3/V3 architecture while routine SP1-SP3 implementation remains with A/B/worker-pc. Do not take over `OPS-AUTO-001-R` unless worker attempts fail to converge.
