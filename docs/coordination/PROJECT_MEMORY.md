# SwarmAI compact project memory

Curated after `LEAD-20260921-030`. `ARTIFACT_REGISTRY.json` is canonical; this is a compact derived orientation, not proof by itself.

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
A runtime `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, Actions `35558067148` red offline Ruff on shared autonomous-runner source.
B product `6b0e1277051ae90fe1d56825d3e771b042380755`, Actions `35558073323` red from the same shared source.
Reviewed integration baseline `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.

No A/B implementation commit advanced in LEAD-030. `OPS-AUTO-001-R` remains the immediate local implementation blocker.

## Heartbeat / autonomy truth

Only `trigger=scheduler` counts. Need 3 consecutive receipts 10-25 minutes apart for both workers before global worker cadence can graduate to hourly; ChatGPT lead itself remains hourly.

Current verified scheduler state:
- A: `03:47:19Z -> 04:02:22Z`, **2/3 and stale**; no later receipt observed.
- B: `07:29:17Z -> 07:44:17Z -> 07:59:17Z -> 08:14:27Z -> 08:29:18Z -> 08:44:17Z`, **6 consecutive valid scheduler receipts** and individually complete.
- Global mode remains `bootstrap_15m` because A has not reached a current 3/3 chain.

Coordination heartbeat does not satisfy `ART-V10-WORKER-HEARTBEAT`. Neither host has proven a repo-assigned autonomous self-launch plus attributable source push, so `ART-OPS-AUTONOMOUS-WORKERS` remains drafting.

A assignment: `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled with only `OPS-AUTO-001-R`. B assignment: `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, disabled pending independent review/propagation of the shared runner repair. Never replay older generations.

## External worker-pc / G13 truth

Attempt 01 (`swarmai-v13-task-pool-freeze-01`) was cancelled with no result or worker branch.

Attempt 02 produced the last real scoped SwarmAI branch:
- `worker/swarmai-v13-task-pool-freeze-02`
- commit `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- exact parent reviewed integration `9ce727842446b98cfa55c28c7e70808f57f17d7b`.

Independent lead review found useful freeze/verifier work but changes required: worker-visible hidden answers/grader/reference material exists; only 5 held-out cases exist per required family/size cell while EVAL-131 requires at least 15 independent observations; seed-isomorphic variants remain; and the remote executor ran no Python/pytest/Ruff/mypy/CI. `ART-V13-TASK-POOL` remains drafting and counted qualification remains forbidden.

Attempt 03 (`swarmai-v13-task-pool-freeze-03`, run `35566726945`, job `106229937621`) was cancelled at `08:02:30Z` after the submitted-task step ran for roughly two hours. `results/swarmai-v13-task-pool-freeze-03.json` is absent and no `worker/swarmai-v13-task-pool-freeze-03` branch exists. Treat it as non-evidence; no worker-performance score was added.

Lead created a narrower retry packet `docs/coordination/packets/EXT-WORKER-PC-V2B-001-R2.md` at `d67ed2bc07f7239220cdf7e4c8aca32f2ccbd0c8`. After worker-pc capacity became free, retry 04 was dispatched:
- task `swarmai-v13-task-pool-freeze-04`
- packet `EXT-WORKER-PC-V2B-001-R2`
- base `worker/swarmai-v13-task-pool-freeze-02`
- remote-workers commit `f3eeb62f836ece720f80e5e79a0a8a461c8e39cc`
- workflow run `35580580156`, queued when first observed
- expected branch `worker/swarmai-v13-task-pool-freeze-04`.

Retry 04 must produce a freeze-v2 core: worker-visible input-only held-out data; sealed/opaque grader-reference identity; >=15 independent held-out inputs in all 16 coding/planning/reasoning/extraction × S/M/L/XL cells; contamination/isomorphism rejection; frozen identities; and actually executed focused verification. No counted qualification is part of the retry.

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
1. restore Mac heartbeat/autonomous LaunchAgents if they are not running;
2. `OPS-AUTO-001-R` SP1 — shared runner source + fail-closed regressions + exact-tip green CI;
3. after independent review/new generation: `V14-REAL-001-R` SP2;
4. then `V2A-003c` SP2 durable result-acceptance fencing;
5. then reviewed-slice integration receipt and durable worker service/client.

B:
- keep heartbeat scheduler running while product assignment is held;
- do not duplicate external task-pool retry 04;
- after shared runner repair/new generation: `V2B-000`, then `V2B-002` reviewer calibration/freeze where ownership is independent;
- W-131B counted qualification only after lead freezes `ART-V13-TASK-POOL`; reviewer held-out only after reviewer design freeze.

## Gate truth and lead lane

V1.0 still blocked on separate authenticated Cursor-agent evidence. V1.1 required artifacts are verified. V1.2 broker/local admission are verified but dual-remote overlap is blocked at 0 admitted remotes. V1.3 has zero qualified cells and task-pool retry 04 is unreviewed. V1.4 first real E2E failed usefully; live adaptive proof and LIVE-142 have not started. V1.5 result acceptance remains. V1.6/V1.7 are queued behind B critical-path work. V2.0 integration/hardening remain drafting; its 168-hour reliability campaign has not started.

Lead-owned G13 repair boundary is `ART-V13-TASK_POOL_REPAIR_CONTRACT.md` plus `EXT-WORKER-PC-V2B-001-R2.md`. `ART-V20-SECURITY-REVIEW` and `ART-V20-RELIABILITY-PROTOCOL` remain drafting; no security acceptance or elapsed reliability evidence is claimed.

Zero-spend, fail-closed, no operational mocks, no known-answer substitution, no admission bypass and no fabricated worker/provider/cost/time/acceptance evidence remain mandatory.
