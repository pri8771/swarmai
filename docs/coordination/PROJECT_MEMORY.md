# SwarmAI compact project memory

Curated 2026-09-21 after `LEAD-20260921-025`. `ARTIFACT_REGISTRY.json` is canonical; this is a compact derived orientation, not proof by itself.

## Authority and team

Owner authorizes source implementation through V3.0. Major milestones: V1.7, V2.3, V3.0. Immediate target: V2.0 implementation/artifact-complete candidate. Main merge, public release/deployment and additional spend remain separately gated.

Active implementation team:
- ChatGPT: lead/architect/independent reviewer/artifact owner/assignment scheduler.
- Cursor A / HOST-MAC-DEV / `cursor/v2-runtime-lane`: runtime/control plane/distributed/recovery + `cursor/v2-integration` owner.
- Cursor B / HOST-WIN-DEV / `cursor/v2-product-lane`: evaluation/knowledge/tools/product/beta.
- verification lane dormant reserve.

Artifacts are primary; packets advance artifact state. Cursor gets routine SP1-SP3 work. Lead reviews independently and advances architecture/recovery/security/evaluation/future contracts in parallel.

## Current source truth

Main: `b9141fa3150f853586dede0334a47b344571bc16`.
A runtime: `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, Actions `35558067148` **red offline Ruff**; console green.
B product: `6b0e1277051ae90fe1d56825d3e771b042380755`, Actions `35558073323` **red offline Ruff**; console green.
Reviewed integration baseline remains `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.

The A/B failures are from newly added shared coordination source, not newly reviewed product logic. A job `106205483700` reports 32 Ruff findings: predominantly E501 in `scripts/coordination/autonomous_worker.py` plus F841 unused `last_sent` in `scripts/coordination/heartbeat.py`. Later offline checks were skipped. Do not call current A/B tips green.

## Heartbeat and autonomous-worker truth

`HEARTBEAT_PROTOCOL.md` controls. Only `trigger=scheduler` counts; need 3 consecutive scheduler receipts 10-25 minutes apart for both workers before worker publication cadence can graduate to hourly. ChatGPT lead itself remains hourly.

At LEAD-025:
- A produced a fresh scheduler heartbeat at `2026-09-21T03:47:19Z`. Prior 02:31 receipt is too far away to be consecutive, so current streak restarts **1/3**.
- B produced its first scheduler heartbeat after reinstall at `2026-09-21T03:43:40Z`: **1/3**.
- Both are fresh, not stale. No graduation.
- Coordination heartbeats are not `ART-V10-WORKER-HEARTBEAT` authenticated Cursor-agent evidence.

Repo-driven autonomous-runner source/installers now exist on both A/B branches, but **neither host has proven an autonomous repo-assigned packet self-launch + attributable source push**. `ART-OPS-AUTONOMOUS-WORKERS` remains drafting.

Because the shared autonomous source makes both active branch tips red, the lead created `OPS-AUTO-001-R / SP1`. A assignment is now `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, repair-only. B assignment is `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, disabled until the shared repair is independently reviewed/propagated. Previous generation items were not observed as autonomously started and must not replay.

## Retained reviewed work

- V2A-003b-R2/SP1 accepted packet; parent `ART-V15-LEASE-FENCING` stays drafting pending V2A-003c result acceptance.
- V2A-H6A-R/SP1 accepted packet; parent V2 foundation hardening remains drafting.
- V2A-003X/SP2 accepted architecture spike: partial DBOS reuse for worker execution only after Swarm authority fencing; durable authority remains PostgreSQL-owned.
- V14-REAL-001 is a real failed mission, not a pass: actual brokered qwen3.5:4b at $0 but empty material diff; review rejected correctly. Repair packet V14-REAL-001-R remains next after autonomy runner repair.
- Current-tip local G12 proof accepted: actual Ollama inventory, two brokered local models, route-disable alternate, quota settlement/deny, $0. No remote claim.
- Remote G12 admission remains 0 routes: OpenRouter/Groq/Gemini metadata auth does not prove exact account free-tier/zero-charge eligibility.
- G13 screening has 72 provisional n=5 cells; zero qualified cells. Task/version pool and reviewer design must be frozen before counted held-out qualification.

No new bounded implementation packet reached lead review in LEAD-025, so `WORKER_PERFORMANCE.json` is intentionally unchanged.

## Immediate queues

A:
1. `OPS-AUTO-001-R` SP1 — clean autonomous runner/heartbeat source + focused fail-closed regressions + exact-tip green CI.
2. after lead review/new assignment generation: `V14-REAL-001-R` SP2.
3. then `V2A-003c` SP2 result-acceptance fencing.
4. after lead review: reviewed-slice integration receipt, then durable worker service/client.

B:
- keep scheduler heartbeat running while autonomous product assignment is held behind shared source repair;
- after repair propagation/new generation: `V2B-000` SP1 -> `V2B-001` SP2 -> `V2B-002` SP3;
- counted W-131B only after lead freezes B1; reviewer held-out only after B2 design freeze.

## Gate truth

V1.0 still blocked on separate authenticated Cursor-agent evidence. V1.1 required artifacts are verified. V1.2 broker/local admission are verified but dual-remote overlap blocked at 0 admitted remotes. V1.3 zero qualified cells. V1.4 first real E2E failed usefully; live adaptive proof and LIVE-142 have not started. V1.5 result acceptance remains. V1.6/V1.7 are queued behind B critical G13 work. V2.0 integration/hardening remain drafting; reliability wall-clock has not started.

Lead advanced `ART-V23-OPS-PLATFORM` with weighted-deficit multimission scheduling, durable SchedulerDecisionReceipt, anti-spawn-amplification/restart/drain/fleet/portability semantics and a preregistered V2.3 acceptance protocol. It remains architecture-only drafting.

Zero-spend, fail-closed, no operational mocks, no known-answer substitution, no admission bypass and no fabricated worker/provider/cost/time/acceptance evidence remain mandatory.
