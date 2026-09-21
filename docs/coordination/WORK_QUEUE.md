# SwarmAI artifact-derived execution queue — after LEAD-20260921-025

Canonical lifecycle: `ARTIFACT_REGISTRY.json`. This is a derived execution view. Immediate target remains a V2.0 implementation/artifact-complete candidate; acceptance/live windows/main merge/public release/additional spend remain separately gated.

## Current source and liveness

- A / `cursor/v2-runtime-lane`: `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, Actions `35558067148` **red offline Ruff**, console green.
- B / `cursor/v2-product-lane`: `6b0e1277051ae90fe1d56825d3e771b042380755`, Actions `35558073323` **red offline Ruff**, console green.
- Reviewed integration remains `9ce727842446b98cfa55c28c7e70808f57f17d7b` / code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.
- A scheduler heartbeat: `03:47:19Z`, fresh, current streak **1/3** because the old 02:31 receipt is outside the 10-25m consecutive window.
- B scheduler heartbeat: `03:43:40Z`, fresh, current streak **1/3**.
- No worker cadence graduation. ChatGPT lead remains hourly.
- No new CURSOR message file since LEAD-024 and no verified autonomous repo-assigned self-launch/push from either host.

The new autonomous-runner source is the immediate shared blocker: Ruff reports 32 findings on A, primarily E501 in `scripts/coordination/autonomous_worker.py` plus F841 in `scripts/coordination/heartbeat.py`; B contains the same shared source. Later offline checks are skipped on both tips.

## Session A — current assignment generation 2

### A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Packet: `docs/coordination/packets/OPS-AUTO-001-R.md`.
Assignment: `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled.

Repair the exact-tip coordination-script Ruff failures while preserving fail-closed one-packet/generation semantics. Add/extend deterministic runner tests for no replay, started-but-not-complete generation fencing, dirty/wrong branch, host/session/branch mismatch and no-remote-change handling. Push exact-tip green evidence. This packet cannot by itself verify the parent autonomous-worker artifact.

### A1 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2 — queued after A0 lead review
Repair generic model response -> isolated worktree materialization, unrelated deterministic regression, then a new preregistered actual local brokered mission on a different subsystem. Preserve the first failed mission.

### A2 — V2A-003c / ART-V15-LEASE-FENCING / SP2 — after A1 in the next safe generation
Durable result acceptance: current worker/project/generation, lease/attempt/task/revision/source/cancellation authority, stale/cancelled/superseded denial, duplicate idempotence and exactly-one winner under race.

### A3 — reviewed-slice integration receipt / SP1
After A2 lead review, integrate only reviewed slices into `cursor/v2-integration`, with exact cherry-pick/receipt and integrated CI.

### A4 — V2A-004 durable worker service/client / SP3
After A2 lead review: durable registration/heartbeat/claim/result/drain, restart-safe tests, then real two-host evidence.

### A-G12 — remote overlap blocked
0 admitted remote routes. Do not canary unknown-cost routes. Exact account free tier / exact model zero price / quota / health / bounded canary eligibility must be independently established first.

## Session B — current assignment generation 2 held

Assignment: `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, `enabled=false` because the current product-lane tip is knowingly red from the shared runner source. Keep the heartbeat scheduler active. The next queue is preserved and will be re-enabled with a new generation after A0 repair is reviewed/propagated.

### B0 — V2B-000 / ART-V20-INTEGRATED-CANDIDATE / SP1
Sync only the reviewed integration baseline, preserve branch-local host/session files, run Windows Python+console baseline and push exact evidence.

### B1 — V2B-001 / ART-V13-TASK-POOL / SP2
Freeze calibration/held-out IDs and hashes across required family x S/M/L/XL plus source/license, size classifier, scorer/grader, prompt, tool and exact model-config versions. Hidden answers stay worker-invisible. No counted held-out qualification before lead freeze.

### B2 — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair and freeze. No qualification claim and no held-out contamination.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Only after B1 lead freeze. Use frozen held-out IDs/versions, retain all failures and total workflow overhead; no post-result threshold changes.

### B4 — reviewer held-out qualification
Only after B2 lead freeze. Required before G14 role manifest.

### B5 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned provenance/tombstones/non-leak tests; hand central migration delta to A.

### B6 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope / ApprovalGrant / ActionReceipt exact project/operation/destination/payload binding, expiry/revocation and explicit test fixtures only.

## Retained independent review decisions

- V2A-003b-R2 / SP1: accepted packet; parent V15 lease fencing still drafting pending V2A-003c.
- V2A-H6A-R / SP1: accepted packet; parent V20 hardening still drafting.
- V2A-003X / SP2: accepted spike, partial DBOS reuse recommendation only.
- V14-REAL-001 / SP2: changes required; genuine brokered local mission failed on empty material diff and was correctly rejected.
- A5-LOCAL-G12-CURRENT-TIP / SP2: accepted live-local proof only; no remote claim.

No new bounded implementation packet reached lead review in LEAD-025; `WORKER_PERFORMANCE.json` remains unchanged.

## Honest blocked acceptance artifacts

- `ART-OPS-HEARTBEAT`: A 1/3, B 1/3; drafting.
- `ART-OPS-AUTONOMOUS-WORKERS`: no repo-assigned self-launch/push from either host; drafting.
- `ART-V10-WORKER-HEARTBEAT`: authenticated Cursor-agent receipts absent.
- `ART-V12-REMOTE-OVERLAP`: 0 admitted remotes.
- `ART-V13-QUALIFIED-MATRIX`: task/version pool not frozen; zero qualified cells.
- `ART-V14-REAL-E2E`: first real attempt failed; repair/rerun waiting after A0.
- `ART-V14-ROLE-MANIFEST` / live adaptive proof: blocked on G12/G13.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock cannot be backfilled.
- V2.0 reliability observation: not started; wall-clock remains real.

## Lead lane

`ART-V23-OPS-PLATFORM` was materially advanced in LEAD-025 with a weighted-deficit project/mission fairness model, SchedulerDecisionReceipt, anti-spawn-amplification/restart/drain/fleet/portability rules and a preregistered ten-part V2.3 acceptance protocol. It remains drafting architecture, isolated from V2.0 source.

Continue V2 security/recovery/integration acceptance plus V3 architecture while Cursor handles routine SP1-SP3 implementation. Do not take over OPS-AUTO-001-R unless repeated worker attempts fail to converge.
