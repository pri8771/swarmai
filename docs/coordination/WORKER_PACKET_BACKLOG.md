# SwarmAI worker packet backlog — current

Updated: 2026-09-21T07:51:25Z after `LEAD-20260921-029`. Canonical artifact lifecycle remains in `ARTIFACT_REGISTRY.json`; this backlog contains bounded execution packets only.

## Shared local execution blocker

A and B still contain the shared repo-driven autonomous-runner source that leaves both active exact-tip offline CI paths red:
- A `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, run `35558067148`.
- B `6b0e1277051ae90fe1d56825d3e771b042380755`, run `35558073323`.

No newer A/B implementation commit is present. No repo-assigned autonomous implementation self-launch + push has been verified on either host.

### READY A-AUTO — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Assignment: `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled.

Fix coordination-script Ruff failures without weakening one-packet/generation, dirty-worktree, branch, no-remote-change, no-force-push or no-self-accept safety. Add focused regressions and return exact-tip CI. Intended parent artifact transition remains `drafting -> drafting` with source blocker removed; host proof is still required later.

B's autonomous assignment remains `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, disabled until this shared repair is independently reviewed and safely propagated. Do not replay generation 1.

## Heartbeat bootstrap

Only `trigger=scheduler` counts. Coordination liveness is separate from autonomous-worker proof and ART-V10 Cursor-agent evidence.

- A: `03:47:19Z -> 04:02:22Z` = **2/3**, stale.
- B: `07:29:17Z -> 07:44:17Z` = **2/3**, fresh; the `06:29:17Z -> 07:29:17Z` 60-minute gap broke the prior chain.
- Keep global worker publication cadence at 15 minutes until both hosts have current 3/3 qualifying chains. ChatGPT lead remains hourly.

## External worker-pc / G13 task-pool

Attempt 01 `swarmai-v13-task-pool-freeze-01` is closed as non-evidence: cancelled, no result JSON, no worker branch.

### Retry 02 — independently reviewed: changes required

- branch `worker/swarmai-v13-task-pool-freeze-02`
- commit `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- exact parent reviewed integration `9ce727842446b98cfa55c28c7e70808f57f17d7b`

Useful output exists, but lead review found worker-visible hidden answer/grader/reference fields, only 5 held-out cases per required cell, seed-isomorphic variants, and no executed Python/pytest/Ruff/mypy/CI evidence. `ART-V13-TASK-POOL` remains drafting; counted qualification is prohibited.

### Retry 03 — ACTIVE REPAIR

Lead repair contract: `docs/artifacts/current/ART-V13-TASK_POOL_REPAIR_CONTRACT.md`.

- task `swarmai-v13-task-pool-freeze-03`
- packet `EXT-WORKER-PC-V2B-001-R1`
- base `worker/swarmai-v13-task-pool-freeze-02`
- expected branch `worker/swarmai-v13-task-pool-freeze-03`
- remote-workers commit `cbdaaab46142e2165084a15157f1aabd8180483d`
- run `35566726945`, job `106229937621`
- status at `2026-09-21T07:51:25Z`: `Execute submitted tasks` still in progress; result JSON absent; expected SwarmAI branch absent.

Repair must produce a new v2 freeze with input-only worker-visible held-out cases, sealed grader-reference identity, >=15 independent held-out inputs for each coding/planning/reasoning/extraction × S/M/L/XL cell, contamination/independence checks, pinned identities and actually executed verification evidence. Preserve v1 as incomplete evidence; do not run counted qualification.

Local B must not duplicate this task while retry 03 is active.

## Retained lead review dispositions

- **V2A-003b-R2 / ART-V15-LEASE-FENCING / SP1 — accepted packet.** Parent remains drafting pending result acceptance.
- **V2A-H6A-R / ART-V20-FOUNDATION-HARDENING / SP1 — accepted packet.** Parent remains drafting.
- **V2A-003X / ART-V15-DBOS-REUSE / SP2 — accepted spike.** Partial DBOS reuse only.
- **V14-REAL-001 / ART-V14-REAL-E2E / SP2 — changes required.** Genuine brokered local mission failed because model output created no material diff; preserved as failure.
- **A5-LOCAL-G12-CURRENT-TIP / SP2 — accepted live-local evidence.** Actual local two-model broker/fallback/quota proof; no remote claim.
- **EXT-WORKER-PC-V2B-001-02 / ART-V13-TASK-POOL / SP2 — changes required.** Real/scoped output but not qualification-ready.

`WORKER_PERFORMANCE.json` is unchanged because no new bounded packet reached independent review.

## Session A — runtime/control-plane/integration

### READY A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1
Repair source + focused fail-closed runner tests + exact-tip green CI.

### QUEUED-AFTER-REVIEW A1 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2
After A0 lead review and a new assignment generation, repair generic materialization and rerun a newly preregistered actual local brokered mission. Preserve failed V14-REAL-001 evidence.

### QUEUED A2 — V2A-003c / ART-V15-LEASE-FENCING / SP2
Implement durable result acceptance with current worker/project/generation, current unexpired lease, source/revision/cancellation authority checks, stale/cancelled/superseded denial, idempotent duplicates and exactly one accepted result under race.

### BLOCKED-ON-A2 A3 — reviewed-slice integration receipt / SP1
Integrate only independently reviewed V15/H6A slices into `cursor/v2-integration`; no bulk runtime merge.

### BLOCKED-ON-A2 A4 — V2A-004 / ART-V15-WORKER-PROTOCOL / SP3
Durable registration/heartbeat/claim/result/drain service/client with restart-safe tests, then prepare actual Mac+Windows multi-host evidence.

### BLOCKED-EXTERNAL A-G12 — ART-V12-REMOTE-OVERLAP
0 admitted remotes. No remote inference until exact account free tier/model zero price/quota/health and bounded-canary eligibility are independently established.

## Session B — evaluation/knowledge/tools/product/beta

Autonomous product execution remains held until A0 is reviewed/propagated. Keep heartbeat scheduler active. After the shared repair, lead issues a new enabled generation.

### LOCAL B0 — V2B-000 / ART-V20-INTEGRATED-CANDIDATE / SP1
Sync only reviewed `cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b`, preserve host/session files, run Windows Python+console baseline, return exact evidence.

### EXTERNAL B1 — ART-V13-TASK-POOL / SP2 — REPAIR ACTIVE
Retry 03 is executing on worker-pc. Local B must not duplicate. No counted qualification before lead freeze.

### LOCAL B2 — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair/freeze after B0 and safe autonomy re-enable. No held-out qualification claim.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Starts only after repaired B1 is independently frozen. Preserve all outcomes and full workflow overhead; no post-result threshold changes.

### B4 — reviewer held-out qualification
Starts only after B2 design freeze. Required before G14 role manifest.

### B5 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned provenance/tombstones/non-leak tests; B owns domain/repository and hands central migration delta to A.

### B6 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope / ApprovalGrant / ActionReceipt with mandatory project identity and exact operation/destination/payload digest, expiry/revocation and explicit test fixtures only.

## Acceptance blockers — do not relabel

- `ART-OPS-HEARTBEAT`: A 2/3 stale; B 2/3 fresh; global drafting.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- authenticated Cursor-agent worker receipts absent.
- remote overlap = 0 admitted routes.
- `ART-V13-TASK-POOL`: retry 02 changes-required; repair 03 active; not frozen.
- G13 reviewer not frozen; zero qualified cells.
- V14 real E2E first attempt failed; repair/rerun queued after autonomous source repair.
- G14 live adaptation blocked on G12/G13.
- LIVE-142 not started.
- V2.0 reliability wall-clock not started.

## Lead-owned parallel work

`ART-V13-TASK_POOL_REPAIR_CONTRACT.md` remains the G13 critical-path acceptance contract. `ART-V20-SECURITY-REVIEW` advanced in coordination commit `c1cd213d33fcda8916ce3f0c0f65972f6a849d57` with candidate-bound negative/evidence mapping, evaluation hidden-reference isolation and install/support secret-handling requirements. `ART-V20-RELIABILITY-PROTOCOL` remains drafting; no elapsed campaign time is claimed.
