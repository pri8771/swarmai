# SwarmAI worker packet backlog — current

Updated after `LEAD-20260921-035`. Canonical artifact lifecycle remains in `ARTIFACT_REGISTRY.json`; this file tracks bounded execution state only.

## Shared local execution blocker

A and B still contain the shared repo-driven autonomous-runner source that leaves both active exact-tip offline CI paths red:
- A `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, run `35558067148`.
- B `6b0e1277051ae90fe1d56825d3e771b042380755`, run `35558073323`.

No newer A/B implementation commit is present. No repo-assigned autonomous implementation self-launch + attributable source push has been verified on either host.

### READY A-AUTO — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Assignment `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled with only `OPS-AUTO-001-R`.

Fix coordination-script Ruff failures without weakening one-packet/generation, dirty-worktree, branch, no-remote-change, no-force-push or no-self-accept safety. Add focused regressions and return exact-tip green CI. Intended parent artifact transition remains `drafting -> drafting`; host self-launch proof is still required later.

Heartbeat bootstrap no longer blocks this packet: both A and B have met 3/3 and global effective cadence is now hourly. A still has no autonomous-start/blocker receipt or generation-2 implementation push. Keep generation 2 unchanged; B remains disabled until this shared repair is independently reviewed and propagated.

## Heartbeat state

Bootstrap proof is complete using only `trigger=scheduler` receipts:
- A: `13:21:56Z -> 13:36:58Z -> 13:52:01Z` = **3/3**.
- B: counted graduation chain `13:14:17Z -> 13:29:18Z -> 13:44:19Z` = **3/3**; B actually had four consecutive valid receipts in its current chain at review.
- `HEARTBEAT_STATE.json` graduated at `2026-09-21T13:56:51Z` to `mode=hourly`, `worker_effective_cadence_minutes=60`.
- OS schedulers may continue waking every 15 minutes; clients must self-throttle publications. Post-graduation hourly behavior still needs observation before any lifecycle promotion of `ART-OPS-HEARTBEAT`.

## External worker-pc / G13 task pool

### REVIEWED CHANGES-REQUIRED — EXT-WORKER-PC-V2B-001-R2 / ART-V13-TASK-POOL / SP2
Retry 04 remains the last source-bearing result:
- task `swarmai-v13-task-pool-freeze-04`
- branch `worker/swarmai-v13-task-pool-freeze-04`
- commit `6467552f86e40964e5bd26d85e3b3a74d03aa059`
- parent `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- SwarmAI exact-tip CI `35587202715`: Ruff/mypy/packaging/Alembic/console pass, ordinary offline pytest fails.

Disposition remains **changes required; ART-V13-TASK-POOL stays drafting; no W-131B**. Review: `docs/coordination/reviews/ART-V13-TASK-POOL-RETRY04-LEAD-REVIEW.md`.

### CLOSED NON-EVIDENCE — retry 05 / EXT-WORKER-PC-V2B-001-R3 transport attempt
- task `swarmai-v13-task-pool-freeze-05`
- remote-workers run/job `35596577823` / `106322668369`
- result: `status=failed`, `failure_class=worker branch push failed`, `branch=null`, `commit=null`
- expected branch `worker/swarmai-v13-task-pool-freeze-05` absent.

The executor ran, but source was not pushed. Self-report without a branch/commit is not reviewable implementation evidence and does not change artifact state or worker-performance counts.

### RUNNING — retry 06 / EXT-WORKER-PC-V2B-001-R3 / ART-V13-TASK-POOL / SP2
Contract: `docs/coordination/packets/EXT-WORKER-PC-V2B-001-R3.md`.
Base: `worker/swarmai-v13-task-pool-freeze-04@6467552f86e40964e5bd26d85e3b3a74d03aa059`.
Expected branch: `worker/swarmai-v13-task-pool-freeze-06`.
Remote-workers task: `swarmai-v13-task-pool-freeze-06`.
Dispatch commit: `bc14ddf4430039e7474b9f63cf6219b1243b4c11`.
Workflow run/job: `35608406904` / `106361127740`.
State at lead cutoff: `Execute submitted tasks` in progress; no retry-06 result/branch yet.

Required repair remains:
- fix exact-tip offline pytest without weakening assertions and keep Ruff/mypy/package/Alembic green;
- bind evidence provenance to the actual pushed branch/commit and commands;
- require >=15 genuinely independent semantic archetypes/groups per required family/size cell; scenario/domain/seed/cumulative-clause variants alone cannot count as independent;
- add direct negative tests for semantic/template siblings;
- preserve worker-visible input-only held-out records, opaque hidden-reference IDs and cross-partition contamination rejection;
- keep `counted_qualification_ready=false` until a real lead-controlled sealed bundle is bound;
- do not run counted W-131B; request lead review only.

Lead-owned sealed-reference contract remains `docs/coordination/G13_SEALED_REFERENCE_BINDING_PROTOCOL.md`; it does not itself claim that a sealed bundle exists.

Remote capacity is 1 and retry 06 currently owns `worker-pc`; other remote tasks must wait rather than overlap execution. Local B must not duplicate this packet.

## Session A — runtime/control-plane/integration

### READY A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1
Shared runner repair + fail-closed regressions + exact-tip green CI.

### QUEUED-AFTER-REVIEW A1 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2
After A0 lead review and a new assignment generation, repair generic materialization and rerun a newly preregistered actual local brokered mission. Preserve failed V14-REAL-001 evidence.

### QUEUED A2 — V2A-003c / ART-V15-LEASE-FENCING / SP2
Implement durable result acceptance with current worker/project/generation, current unexpired lease, source/revision/cancellation authority checks, stale/cancelled/superseded denial, idempotent duplicates and exactly one accepted result under race.

### BLOCKED-ON-A2 A3 — reviewed-slice integration receipt / SP1
Integrate only independently reviewed V15/H6A slices into `cursor/v2-integration`; no bulk runtime merge.

### BLOCKED-ON-A2 A4 — V2A-004 / ART-V15-WORKER-PROTOCOL / SP3
Durable registration/heartbeat/claim/result/drain service/client with restart-safe tests, then prepare actual Mac+Windows multi-host evidence.

### BLOCKED-EXTERNAL A-G12 — ART-V12-REMOTE-OVERLAP
0 admitted remotes. No remote inference until exact account free-tier/model zero-price/quota/health and bounded-canary eligibility are independently established.

## Session B — evaluation/knowledge/tools/product/beta

Autonomous product execution remains held until A0 is reviewed/propagated.

### LOCAL B0 — V2B-000 / ART-V20-INTEGRATED-CANDIDATE / SP1
After safe re-enable, sync only reviewed integration baseline, preserve host/session files, run Windows Python+console baseline, return exact evidence.

### EXTERNAL B1 — ART-V13-TASK-POOL / SP2
R3 is running as retry 06 through `worker-pc`. Local B must not duplicate. No counted qualification before lead freeze + real sealed-reference binding.

### LOCAL B2 — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair/freeze after B0 and safe autonomy re-enable. No held-out qualification claim.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Starts only after repaired B1 is independently frozen and sealed-reference binding is real. Preserve all outcomes and full workflow overhead; no post-result threshold changes.

### B4 — reviewer held-out qualification
Starts only after B2 design freeze. Required before G14 role manifest.

### B5 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned provenance/tombstones/non-leak tests; B owns domain/repository and hands central migration delta to A.

### B6 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope / ApprovalGrant / ActionReceipt with mandatory project identity and exact operation/destination/payload digest, expiry/revocation and explicit test fixtures only.

## Retained review dispositions

- V2A-003b-R2 / ART-V15-LEASE-FENCING / SP1 — accepted packet; parent remains drafting pending result acceptance.
- V2A-H6A-R / ART-V20-FOUNDATION-HARDENING / SP1 — accepted packet; parent remains drafting.
- V2A-003X / ART-V15-DBOS-REUSE / SP2 — accepted spike; partial DBOS reuse only.
- V14-REAL-001 / ART-V14-REAL-E2E / SP2 — changes required; genuine brokered local mission failed because model output created no material diff.
- A5-LOCAL-G12-CURRENT-TIP / SP2 — accepted live-local evidence only; no remote claim.
- EXT-WORKER-PC-V2B-001-02 / ART-V13-TASK-POOL / SP2 — changes required.
- retry 03 — cancelled/non-evidence.
- retry 04 — changes required at `6467552f86e40964e5bd26d85e3b3a74d03aa059`.
- retry 05 — failed worker branch push; non-evidence.

`WORKER_PERFORMANCE.json` remains unchanged because no new bounded implementation packet reached independent review. Heartbeats and transport failures are not implementation-performance evidence.

## Acceptance blockers — do not relabel

- `ART-OPS-HEARTBEAT`: bootstrap proof complete and cadence graduated; post-graduation hourly behavior still pending before lifecycle promotion.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- authenticated Cursor-agent worker receipts absent.
- G12 remote overlap = 0 admitted routes.
- `ART-V13-TASK-POOL`: retry 04 changes-required; retry 05 non-evidence; retry 06 running; not frozen.
- G13 reviewer not frozen; zero qualified cells.
- V14 real E2E first attempt failed; repair/rerun queued after autonomous source repair.
- G14 live adaptation blocked on G12/G13.
- LIVE-142 not started.
- V2.0 reliability wall-clock not started.
