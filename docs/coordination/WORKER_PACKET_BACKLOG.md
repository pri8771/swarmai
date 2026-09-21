# SwarmAI worker packet backlog — current

Updated after `LEAD-20260921-033`. Canonical artifact lifecycle remains in `ARTIFACT_REGISTRY.json`; this file is bounded execution state only.

## Shared local execution blocker

A and B still contain the shared repo-driven autonomous-runner source that leaves both active exact-tip offline CI paths red:
- A `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, run `35558067148`.
- B `6b0e1277051ae90fe1d56825d3e771b042380755`, run `35558073323`.

No newer A/B implementation commit is present. No repo-assigned autonomous implementation self-launch + push has been verified on either host.

### READY A-AUTO — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Assignment `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled.

Fix coordination-script Ruff failures without weakening one-packet/generation, dirty-worktree, branch, no-remote-change, no-force-push or no-self-accept safety. Add focused regressions and return exact-tip CI. Intended parent artifact transition remains `drafting -> drafting` with the source blocker removed; host proof is still required later.

A's scheduler has resumed at `11:55:14Z`, but the long outage broke its old chain and no autonomous-start/push is present. Keep generation 2 unchanged. B's autonomous assignment remains disabled until this shared repair is independently reviewed and safely propagated. Do not replay generation 1.

## Heartbeat bootstrap

Only `trigger=scheduler` counts.

- A: fresh scheduler receipt at `11:55:14Z` after a multi-hour gap; old chain is broken, so current chain is **1/3** and A is fresh.
- B: `11:14:17Z -> 11:29:17Z -> 11:44:27Z` = **3/3**, with valid 10–25 minute gaps. B individually satisfies bootstrap cadence.
- Global cadence stays at 15 minutes until both have a current 3/3 qualifying chain. ChatGPT lead remains hourly.

## External worker-pc / G13 task pool

### REVIEWED CHANGES-REQUIRED — EXT-WORKER-PC-V2B-001-R2 / ART-V13-TASK-POOL / SP2

Retry 04 produced real source:
- task: `swarmai-v13-task-pool-freeze-04`
- branch: `worker/swarmai-v13-task-pool-freeze-04`
- commit: `6467552f86e40964e5bd26d85e3b3a74d03aa059`
- parent: `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- remote-workers run/job: `35580580156` / `106272271934`
- SwarmAI exact-tip CI: `35587202715`.

The remote task execution step succeeded and the branch was pushed, but sanitized result publication failed, so no result JSON exists. SwarmAI static/type/package/Alembic checks pass and console CI passes, but the offline pytest step fails.

Independent lead review additionally found that the current `5 task variants x 3 structural loads` construction does not mechanically establish 15 semantic-independent observations per cell: ordinary scenario/domain substitutions and incremental clause variants can evade the current normalizer. The evidence document also contains stale provenance saying the branch was never committed/pushed. Finally, the lead-controlled sealed reference bundle/content digest is not bound and counted readiness remains false.

Disposition: **changes required; ART-V13-TASK-POOL stays drafting; no W-131B**.
Review: `docs/coordination/reviews/ART-V13-TASK-POOL-RETRY04-LEAD-REVIEW.md`.

### DISPATCHED — EXT-WORKER-PC-V2B-001-R3 / ART-V13-TASK-POOL / SP2

Contract: `docs/coordination/packets/EXT-WORKER-PC-V2B-001-R3.md`.
Base: `worker/swarmai-v13-task-pool-freeze-04@6467552f86e40964e5bd26d85e3b3a74d03aa059`.
Expected branch: `worker/swarmai-v13-task-pool-freeze-05`.
Remote-workers task: `swarmai-v13-task-pool-freeze-05`.
Dispatch commit: `d12ec01e9d741f4ac117c074190811a4d48d0e41`.
Workflow run: `35596577823` (queued at lead review; no result/worker05 source claimed yet).

Required repair:
- reproduce/fix exact-tip offline pytest while preserving existing negative assertions and green Ruff/mypy/package/Alembic;
- rebind evidence provenance to actual commit/CI;
- require >=15 distinct semantic independence groups/archetypes per required family/size cell; scenario-noun, seed-ID or cumulative-clause variations alone cannot count as independent;
- add negative tests proving semantic/template siblings are rejected;
- preserve input-only worker-visible records and opaque hidden-reference IDs;
- keep `counted_qualification_ready=false` until lead-controlled sealed bundle binding exists;
- do not run counted W-131B; request lead review only.

Lead-owned sealed-reference contract: `docs/coordination/G13_SEALED_REFERENCE_BINDING_PROTOCOL.md`.

Local B must not duplicate the external task-pool packet.

## Session A — runtime/control-plane/integration

### READY A0 — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1
Shared runner source + fail-closed regressions + exact-tip green CI.

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

Autonomous product execution remains held until A0 is reviewed/propagated. Keep heartbeat scheduler active.

### LOCAL B0 — V2B-000 / ART-V20-INTEGRATED-CANDIDATE / SP1
After safe re-enable, sync only reviewed integration baseline, preserve host/session files, run Windows Python+console baseline, return exact evidence.

### EXTERNAL B1 — ART-V13-TASK-POOL / SP2
R3 is dispatched as retry 05 through `worker-pc`. Local B must not duplicate. No counted qualification before lead freeze + real sealed-reference binding.

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
- EXT-WORKER-PC-V2B-001-R1 / retry 03 — cancelled without result/branch; not scored as reviewed implementation.
- EXT-WORKER-PC-V2B-001-R2 / retry 04 — changes required at `6467552f86e40964e5bd26d85e3b3a74d03aa059`.

`WORKER_PERFORMANCE.json` summary counts remain unchanged because no new bounded implementation packet reached independent review. Retry 05 dispatch is work scheduling, not review evidence.

## Acceptance blockers — do not relabel

- `ART-OPS-HEARTBEAT`: A current 1/3 after scheduler recovery; B current 3/3; global drafting.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- authenticated Cursor-agent worker receipts absent.
- G12 remote overlap = 0 admitted routes.
- `ART-V13-TASK-POOL`: retry 04 changes-required; retry 05 dispatched/queued; not frozen.
- G13 reviewer not frozen; zero qualified cells.
- V14 real E2E first attempt failed; repair/rerun queued after autonomous source repair.
- G14 live adaptation blocked on G12/G13.
- LIVE-142 not started.
- V2.0 reliability wall-clock not started.
