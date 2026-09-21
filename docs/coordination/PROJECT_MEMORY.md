# SwarmAI compact project memory

Curated after `LEAD-20260921-034`. `ARTIFACT_REGISTRY.json` is canonical; this is a compact derived orientation, not proof by itself.

## Authority and team

Owner authorizes source implementation through V3.0. Major milestones: V1.7, V2.3, V3.0. Immediate target: V2.0 implementation/artifact-complete candidate. Main merge, public release/deployment and additional spend remain separately gated.

Active implementation team:
- ChatGPT: lead/architect/independent reviewer/artifact owner/assignment scheduler.
- Cursor A / HOST-MAC-DEV / `cursor/v2-runtime-lane`: runtime/control plane/distributed/recovery + `cursor/v2-integration` owner.
- Cursor B / HOST-WIN-DEV / `cursor/v2-product-lane`: evaluation/knowledge/tools/product/beta.
- verification lane dormant reserve.
- `pri8771/remote-workers` is execution infrastructure only; SwarmAI remains roadmap/state/acceptance authority.

Artifacts are primary; packets advance artifact state. Cursor gets routine SP1-SP3 work. Lead reviews independently and advances architecture/recovery/security/evaluation/future contracts in parallel.

## Current source truth

Main `b9141fa3150f853586dede0334a47b344571bc16`.
A runtime `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, Actions `35558067148` red offline on shared autonomous-runner source.
B product `6b0e1277051ae90fe1d56825d3e771b042380755`, Actions `35558073323` red from the same shared source.
Reviewed integration baseline `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.

No A/B implementation commit advanced in LEAD-034. `OPS-AUTO-001-R` remains the immediate local implementation blocker.

## Heartbeat / autonomy truth

Only `trigger=scheduler` counts. Need 3 consecutive receipts 10-25 minutes apart for both workers before global worker cadence can graduate to hourly; ChatGPT lead itself remains hourly.

Current verified scheduler state at the lead cutoff:
- A: `12:36:39Z -> 12:51:41Z`, **2/3**, valid 15m02s gap. The prior ~41-minute gap from `11:55:14Z` reset the chain. A is fresh.
- B: **1/3** at `12:29:17Z`; the prior `11:59:17Z -> 12:29:17Z` 30-minute gap reset the chain. B is fresh at cutoff.
- Global mode remains `bootstrap_15m`; no hourly graduation.

Coordination heartbeat does not satisfy `ART-V10-WORKER-HEARTBEAT`. Neither host has proven a repo-assigned autonomous self-launch plus attributable source push, so `ART-OPS-AUTONOMOUS-WORKERS` remains drafting.

A assignment: `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled with only `OPS-AUTO-001-R`. B assignment: `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, disabled pending independent review/propagation of the shared runner repair. Never replay older generations.

## External worker-pc / G13 truth

Attempts 01 and 03 were cancelled without result/branch. Attempt 02 at `worker/swarmai-v13-task-pool-freeze-02@bbe41b7770123fef4eb03c4f03f95fc18eefc692` was independently reviewed changes-required.

Attempt 04 produced real worker source:
- branch `worker/swarmai-v13-task-pool-freeze-04`
- commit `6467552f86e40964e5bd26d85e3b3a74d03aa059`
- parent `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- remote-workers run/job `35580580156` / `106272271934`.

Retry 04 remains changes-required: exact-tip SwarmAI offline pytest is red; evidence provenance is stale; the current corpus does not mechanically prove >=15 semantic-independent observations per cell; and no lead-controlled sealed reference bundle/content digest is bound. `ART-V13-TASK-POOL` remains drafting and counted W-131B remains prohibited.

Attempt 05 / R3 is now executing through `worker-pc`:
- task `swarmai-v13-task-pool-freeze-05`
- dispatch commit `d12ec01e9d741f4ac117c074190811a4d48d0e41`
- workflow run/job `35596577823` / `106322668369`
- base `worker/swarmai-v13-task-pool-freeze-04@6467552f86e40964e5bd26d85e3b3a74d03aa059`
- expected branch `worker/swarmai-v13-task-pool-freeze-05`.

At LEAD-034 cutoff, the workflow/job remains in progress in `Execute submitted tasks`; no result JSON and no expected worker branch exist yet. Capacity 1 is therefore occupied and no second remote task should be dispatched.

Lead review contract: `docs/coordination/packets/EXT-WORKER-PC-V2B-001-R3.md`. It requires green exact-tip verification, correct provenance, >=15 genuinely independent semantic groups per required family/size cell, negative sibling/contamination tests, input-only worker-visible records, opaque hidden-reference IDs, `counted_qualification_ready=false`, and no W-131B.

Lead-owned sealed-reference preregistration remains `docs/coordination/G13_SEALED_REFERENCE_BINDING_PROTOCOL.md`. It does not invent a hidden bundle; counted qualification remains blocked until an actual non-worker-readable reference bundle and immutable lead binding receipt exist.

## Retained reviewed work

- V2A-003b-R2/SP1 accepted packet; parent `ART-V15-LEASE-FENCING` still drafting pending V2A-003c result acceptance.
- V2A-H6A-R/SP1 accepted packet; parent V2 hardening remains drafting.
- V2A-003X/SP2 accepted architecture spike: partial DBOS reuse only; Swarm authority remains PostgreSQL-owned.
- V14-REAL-001 is a real failed mission, not a pass: actual brokered qwen3.5:4b at $0 but empty material diff; repair V14-REAL-001-R remains queued after runner repair.
- Current-tip local G12 proof accepted: actual Ollama inventory, two brokered local models, route-disable alternate, quota settlement/deny, $0. No remote claim.
- G12 remote admission remains 0 routes: metadata/auth does not prove exact-account free-tier/zero-charge eligibility.
- G13 screening has 72 provisional n=5 cells; zero qualified cells.

## Immediate queues

A:
1. `OPS-AUTO-001-R` SP1 — shared runner source + fail-closed regressions + exact-tip green CI;
2. after independent review/new generation: `V14-REAL-001-R` SP2;
3. then `V2A-003c` SP2 durable result-acceptance fencing;
4. then reviewed-slice integration receipt and durable worker service/client.

B:
- keep heartbeat scheduler running while product assignment is held;
- do not duplicate external task-pool repair;
- after shared runner repair/new generation: `V2B-000`, then `V2B-002` reviewer calibration/freeze where ownership is independent;
- W-131B counted qualification only after lead freezes `ART-V13-TASK-POOL` and binds a real sealed reference bundle; reviewer held-out only after reviewer design freeze.

## Lead parallel artifact lane

`docs/artifacts/future/ART-V20-INSTALL_UPGRADE_PROTOCOL.md` was strengthened at coordination commit `0c74cb9db6bcf26583b234c33566573c9f8f42e7` for `ART-V20-UPGRADE-ROLLBACK`. It now preregisters exact candidate/predecessor identity, immutable pre-upgrade manifests, consistent backup/quiesce boundaries, support-matrix-bound upgrade paths, code/downgrade/restore rollback classes, partial-migration/crash/stale-authority negatives, semantic integrity checks, measurements and immutable evidence requirements.

This is protocol progress only. No upgrade, rollback, restore, timing threshold, supported predecessor, or artifact lifecycle transition is claimed.

## Gate truth

V1.0 remains blocked on separate authenticated Cursor-agent evidence. V1.1 required artifacts are verified. V1.2 broker/local admission are verified but dual-remote overlap is blocked at 0 admitted remotes. V1.3 has zero qualified cells and task pool remains drafting while retry 05 runs. V1.4 first real E2E failed usefully; live adaptive proof and LIVE-142 have not started. V1.5 result acceptance remains. V1.6/V1.7 are queued behind B critical-path work. V2.0 integration/hardening remain drafting; its 168-hour reliability campaign has not started.

Zero-spend, fail-closed, no operational mocks, no known-answer substitution, no admission bypass and no fabricated worker/provider/cost/time/acceptance evidence remain mandatory.
