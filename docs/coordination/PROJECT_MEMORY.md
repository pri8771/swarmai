# SwarmAI compact project memory

Curated 2026-09-21 after `LEAD-20260921-026`. `ARTIFACT_REGISTRY.json` is canonical; this is a compact derived orientation, not proof by itself.

## Authority and team

Owner authorizes source implementation through V3.0. Major milestones: V1.7, V2.3, V3.0. Immediate target: V2.0 implementation/artifact-complete candidate. Main merge, public release/deployment and additional spend remain separately gated.

Active implementation team:
- ChatGPT: lead/architect/independent reviewer/artifact owner/assignment scheduler.
- Cursor A / HOST-MAC-DEV / `cursor/v2-runtime-lane`: runtime/control plane/distributed/recovery + `cursor/v2-integration` owner.
- Cursor B / HOST-WIN-DEV / `cursor/v2-product-lane`: evaluation/knowledge/tools/product/beta.
- verification lane dormant reserve.
- `pri8771/remote-workers` is external execution infrastructure only; it never owns SwarmAI roadmap/state/acceptance.

Artifacts are primary; packets advance artifact state. Cursor gets routine SP1-SP3 work. Lead reviews independently and advances architecture/recovery/security/evaluation/future contracts in parallel.

## Current source truth

Main: `b9141fa3150f853586dede0334a47b344571bc16`.
A runtime: `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, Actions `35558067148` red offline Ruff; console green.
B product: `6b0e1277051ae90fe1d56825d3e771b042380755`, prior exact-tip CI red from the same shared autonomous-runner source; console green.
Reviewed integration baseline remains `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.

No A/B source commit advanced in LEAD-026. The shared runner repair `OPS-AUTO-001-R` remains the immediate local implementation blocker; do not call either active lane tip green.

## Heartbeat and autonomous-worker truth

Only `trigger=scheduler` counts. Need 3 consecutive receipts 10-25 minutes apart for both workers before global worker publication cadence may graduate to hourly. ChatGPT lead remains hourly.

At LEAD-026:
- A scheduler receipts `03:47:19Z` and `04:02:22Z` form a valid pair: **2/3**, but the latest was >35 minutes old at review, so A is **stale**.
- B receipts `03:43:40Z`, `03:59:17Z`, `04:14:17Z`, `04:29:17Z`, `04:44:18Z` form **5 consecutive valid** intervals. B individually satisfies the requirement and is fresh.
- Global mode remains `bootstrap_15m` because A has not satisfied the requirement.
- Coordination heartbeat is not `ART-V10-WORKER-HEARTBEAT` authenticated Cursor-agent evidence.

Repo-driven autonomous-runner source/installers exist on both A/B branches, but neither host has proven a repo-assigned autonomous self-launch + attributable source push. `ART-OPS-AUTONOMOUS-WORKERS` remains drafting.

A assignment remains `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled with only `OPS-AUTO-001-R`. B assignment remains `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, disabled until that repair is independently reviewed/propagated. Do not replay prior generations.

## External worker-pc truth

`worker-pc` is online, capacity 1, with verified Claude branch execution infrastructure. The SwarmAI task `swarmai-v13-task-pool-freeze-01` did **not** produce a result: dispatch commit `7e17163e7fc85455a8eb0180d3cb2173711dc978`, Actions run `35559390335` ended `cancelled`, result JSON is absent and expected worker branch is absent. Therefore `ART-V13-TASK-POOL` remains drafting and counted qualification remains forbidden.

At LEAD-026 the remote-worker lane was occupied by unrelated run `35560103791` observed `in_progress`. Do not submit a competing retry. When `worker-pc` is idle, create a new unique task ID for the same V2B-001 intent, then independently review its branch/diff/tests/result before any artifact transition. While that external retry is active, local B should not duplicate V2B-001.

## Retained reviewed work

- V2A-003b-R2/SP1 accepted packet; parent `ART-V15-LEASE-FENCING` stays drafting pending V2A-003c result acceptance.
- V2A-H6A-R/SP1 accepted packet; parent V2 foundation hardening remains drafting.
- V2A-003X/SP2 accepted architecture spike: partial DBOS reuse for worker execution only after Swarm authority fencing; durable authority remains PostgreSQL-owned.
- V14-REAL-001 is a real failed mission, not a pass: actual brokered qwen3.5:4b at $0 but empty material diff; repair packet V14-REAL-001-R remains after runner repair.
- Current-tip local G12 proof accepted: actual Ollama inventory, two brokered local models, route-disable alternate, quota settlement/deny, $0. No remote claim.
- Remote G12 admission remains 0 routes: metadata/auth does not prove exact account free-tier/zero-charge eligibility.
- G13 screening has 72 provisional n=5 cells; zero qualified cells. Task/version pool and reviewer design must be frozen before counted held-out qualification.

No new bounded implementation packet reached independent review in LEAD-026, so `WORKER_PERFORMANCE.json` remains unchanged.

## Immediate queues

A:
1. `OPS-AUTO-001-R` SP1 — repair autonomous-runner/heartbeat source + focused fail-closed regressions + exact-tip green CI.
2. after lead review/new assignment generation: `V14-REAL-001-R` SP2.
3. then `V2A-003c` SP2 result-acceptance fencing.
4. after review: reviewed-slice integration receipt, then durable worker service/client.

B:
- keep scheduler heartbeat running while assignment remains held;
- after shared repair propagation/new generation: run `V2B-000` locally, then `V2B-002` locally while the external worker handles the retried `V2B-001` task-pool freeze;
- counted W-131B only after lead freezes ART-V13-TASK-POOL; reviewer held-out only after reviewer design freeze.

## Gate truth and lead lane

V1.0 still blocked on separate authenticated Cursor-agent evidence. V1.1 required artifacts are verified. V1.2 broker/local admission are verified but dual-remote overlap blocked at 0 admitted remotes. V1.3 zero qualified cells. V1.4 first real E2E failed usefully; live adaptive proof and LIVE-142 have not started. V1.5 result acceptance remains. V1.6/V1.7 are queued behind B critical-path work. V2.0 integration/hardening remain drafting; its 7-day reliability wall-clock campaign has not started.

Lead advanced `ART-V20-RELIABILITY-PROTOCOL` at `170d0b8c72a89e698cdc15cbeb86901c0cecab1b`: campaign identity, reset matrix, immutable checkpoints, monitoring-gap treatment and no-splicing/no-backfill rules now bind any future 168-hour campaign. This is protocol work only, not elapsed evidence.

Zero-spend, fail-closed, no operational mocks, no known-answer substitution, no admission bypass and no fabricated worker/provider/cost/time/acceptance evidence remain mandatory.
