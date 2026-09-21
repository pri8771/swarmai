# SwarmAI artifact-derived execution queue — after LEAD-20260921-026

Canonical lifecycle: `ARTIFACT_REGISTRY.json`. This is a derived execution view. Immediate target remains a V2.0 implementation/artifact-complete candidate; acceptance/live windows/main merge/public release/additional spend remain separately gated.

## Current source and liveness

- A / `cursor/v2-runtime-lane`: `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, Actions `35558067148` red offline Ruff from shared autonomous-runner source; console green.
- B / `cursor/v2-product-lane`: `6b0e1277051ae90fe1d56825d3e771b042380755`, prior exact-tip CI red from the same shared source; console green.
- Reviewed integration remains `9ce727842446b98cfa55c28c7e70808f57f17d7b` / code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.
- A scheduler heartbeats `03:47:19Z` -> `04:02:22Z`: valid pair, **2/3**, but A is stale at the >35m bootstrap threshold.
- B scheduler heartbeats `03:43:40Z` -> `03:59:17Z` -> `04:14:17Z` -> `04:29:17Z` -> `04:44:18Z`: **5 consecutive valid**; B individually satisfies cadence proof and is fresh.
- No global hourly graduation until A also satisfies the requirement. ChatGPT lead remains hourly.
- No new A/B implementation commit or autonomous repo-assigned self-launch/push was verified this run.

## External worker-pc — G13 task-pool stream

Infrastructure: `pri8771/remote-workers` only; SwarmAI remains project authority.

Attempt `swarmai-v13-task-pool-freeze-01` / `ART-V13-TASK-POOL` / `V2B-001` did not execute to a reviewable result:
- dispatch commit `7e17163e7fc85455a8eb0180d3cb2173711dc978`;
- Actions run `35559390335` = `cancelled`;
- no `results/swarmai-v13-task-pool-freeze-01.json`;
- no `worker/swarmai-v13-task-pool-freeze-01` branch.

No artifact credit is granted. At review time worker-pc's dispatch lane was occupied by unrelated run `35560103791`, observed `in_progress`. Capacity is 1, so **do not submit a competing retry**. When worker-pc becomes idle, submit a new unique branch-mode task for the same V2B-001 intent. Lead must review branch/diff/tests/result before any task-pool freeze. Counted G13 qualification remains prohibited until independent freeze.

## Session A — assignment generation 2

### A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Assignment: `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled.

Repair exact-tip autonomous-runner/heartbeat Ruff failures while preserving fail-closed one-packet/generation, clean-worktree, branch, no-remote-change, no-force-push and no-self-accept semantics. Add focused regressions. Push exact-tip green evidence. Parent autonomous-worker artifact still requires host self-launch proof after source repair.

### A1 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2 — after A0 lead review/new generation
Repair generic model-response -> isolated-worktree materialization without target-specific logic/known answers; add unrelated valid-patch and malformed/no-op regressions; preregister/run a new actual local brokered mission on a different bounded subsystem. Preserve the first failed evidence.

### A2 — V2A-003c / ART-V15-LEASE-FENCING / SP2 — next safe generation after A1
Durable result acceptance: current worker/project/generation, lease/attempt/task/revision/source/cancellation authority, stale/cancelled/superseded denial, duplicate idempotence and exactly-one winner under race.

### A3 — reviewed-slice integration receipt / SP1
After A2 lead review, integrate only independently reviewed V15/H6A slices into `cursor/v2-integration`; run integrated CI and bind receipt to exact SHAs.

### A4 — V2A-004 / ART-V15-WORKER-PROTOCOL / SP3
After result acceptance: durable registration/heartbeat/claim/result/drain service/client, restart-safe tests, then actual Mac+Windows multi-host evidence.

### A-G12 — remote overlap blocked
0 admitted remote routes. Do not canary unknown-cost routes. Exact account free-tier/model zero-price/quota/health/bounded-canary eligibility must be independently established first.

## Session B — assignment generation 2 held

Assignment `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, remains `enabled=false`. Keep scheduler heartbeat active. Do not execute product packets autonomously on the known-red shared runner source.

After A0 is independently reviewed and the shared fix is propagated, publish a **new enabled generation**. To avoid duplicate ownership with worker-pc, the intended local order is:

### B0 — V2B-000 / ART-V20-INTEGRATED-CANDIDATE / SP1
Sync only reviewed integration baseline, preserve branch-local host/session files, run Windows Python+console baseline, push exact evidence.

### B1-remote — V2B-001 / ART-V13-TASK-POOL / SP2
Reserved for a fresh worker-pc retry once remote capacity is idle. Freeze calibration/held-out IDs/hashes, required family x S/M/L/XL coverage and exact classifier/scorer/prompt/tool/model-config identities. Hidden answers stay worker-invisible. No counted qualification.

### B2-local — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair and freeze. Local B may proceed after B0 while external B1 is running, provided file ownership remains independent. No held-out qualification before lead freeze.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Only after lead accepts/freeze-binds B1. Preserve all outcomes and total workflow overhead; no post-result threshold changes.

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

No bounded implementation packet reached lead review in LEAD-026; `WORKER_PERFORMANCE.json` remains unchanged.

## Honest blocked acceptance artifacts

- `ART-OPS-HEARTBEAT`: A 2/3 and stale; B 5 consecutive and individually complete; global still drafting.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- `ART-V10-WORKER-HEARTBEAT`: authenticated Cursor-agent receipts absent.
- `ART-V12-REMOTE-OVERLAP`: 0 admitted remotes.
- `ART-V13-TASK-POOL`: drafting; first worker-pc attempt cancelled before result/branch.
- `ART-V13-QUALIFIED-MATRIX`: zero qualified cells.
- `ART-V14-REAL-E2E`: first real attempt failed; repair/rerun waits behind A0.
- `ART-V14-ROLE-MANIFEST` / live adaptive proof: blocked on G12/G13.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock cannot be backfilled.
- V2.0 reliability observation: not started; 168-hour clock remains real.

## Lead lane

`ART-V20-RELIABILITY-PROTOCOL` advanced at `170d0b8c72a89e698cdc15cbeb86901c0cecab1b` with campaign identity/reset classes, immutable checkpoints, monitoring-gap classification, and no-splicing/no-backfill rules for one compatible 168-hour campaign. It remains drafting protocol work; no campaign time is claimed.

Continue V2 security/recovery/integration acceptance and V2.3/V3 architecture while routine SP1-SP3 implementation remains with A/B/worker-pc. Do not take over `OPS-AUTO-001-R` unless worker attempts fail to converge.
