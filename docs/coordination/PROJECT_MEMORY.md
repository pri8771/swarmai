# SwarmAI compact project memory

Curated after `LEAD-20260921-032`. `ARTIFACT_REGISTRY.json` is canonical; this is a compact derived orientation, not proof by itself.

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

No A/B implementation commit advanced in LEAD-032. `OPS-AUTO-001-R` remains the immediate local implementation blocker.

## Heartbeat / autonomy truth

Only `trigger=scheduler` counts. Need 3 consecutive receipts 10-25 minutes apart for both workers before global worker cadence can graduate to hourly; ChatGPT lead itself remains hourly.

Current verified scheduler state:
- A: `03:47:19Z -> 04:02:22Z`, **2/3 and stale**; no later receipt observed.
- B: a prior long valid chain reached `10:14:17Z`, but the next scheduler receipt was `10:44:17Z`, a **30-minute gap**. Because that exceeds the 25-minute maximum, B's current chain resets to **1/3**. B is fresh, not stale.
- Global mode remains `bootstrap_15m`.

Coordination heartbeat does not satisfy `ART-V10-WORKER-HEARTBEAT`. Neither host has proven a repo-assigned autonomous self-launch plus attributable source push, so `ART-OPS-AUTONOMOUS-WORKERS` remains drafting.

A assignment: `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled with only `OPS-AUTO-001-R`. B assignment: `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, disabled pending independent review/propagation of the shared runner repair. Never replay older generations.

## External worker-pc / G13 truth

Attempt 01 was cancelled with no result/branch. Attempt 02 at `worker/swarmai-v13-task-pool-freeze-02@bbe41b7770123fef4eb03c4f03f95fc18eefc692` was independently reviewed changes-required. Attempt 03 was cancelled with no result/branch.

Attempt 04 produced a real worker branch:
- `worker/swarmai-v13-task-pool-freeze-04`
- commit `6467552f86e40964e5bd26d85e3b3a74d03aa059`
- parent `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
- remote-workers run `35580580156`, job `106272271934`.

The remote task execution step succeeded and the branch was pushed, but sanitized result publication failed, so `results/swarmai-v13-task-pool-freeze-04.json` is absent. Exact-tip SwarmAI CI `35587202715` is red because offline pytest fails; Ruff, mypy, packaging and Alembic heads pass, and console CI passes.

Independent lead review disposition is **changes required**. Positive work: v2 worker-visible input-only records, 15 records per required family/size cell, opaque hidden-reference handles, versioned identities/checksums and fail-closed resolver intent. Remaining blockers:
- exact-tip offline pytest red;
- evidence doc incorrectly says the branch was uncommitted/unpushed;
- independence is not mechanically strong enough: the corpus still uses families of shared task recipes with scenario/domain substitutions and incremental structural loads, while the normalizer does not collapse ordinary scenario nouns into one semantic archetype;
- no lead-controlled sealed reference bundle/content digest is bound, so `counted_qualification_ready` remains false.

`ART-V13-TASK-POOL` therefore remains **drafting**. Counted W-131B qualification remains prohibited.

Lead review: `docs/coordination/reviews/ART-V13-TASK-POOL-RETRY04-LEAD-REVIEW.md`.
Next bounded repair: `docs/coordination/packets/EXT-WORKER-PC-V2B-001-R3.md`, based on retry-04 exact commit. It requires green exact-tip offline verification, correct provenance, and >=15 mechanically distinct semantic independence groups/archetypes per required cell rather than superficial scenario-name/seed variations.

`worker-pc` capacity is currently occupied by an unrelated remote-workers run `35590523591`, so R3 is prepared but not dispatched. Do not overlap capacity 1.

Lead also preregistered `docs/coordination/G13_SEALED_REFERENCE_BINDING_PROTOCOL.md`. It does not invent a hidden bundle; counted qualification remains blocked until an actual non-worker-readable reference bundle and immutable lead binding receipt exist.

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
- do not duplicate external task-pool repair;
- after shared runner repair/new generation: `V2B-000`, then `V2B-002` reviewer calibration/freeze where ownership is independent;
- W-131B counted qualification only after lead freezes `ART-V13-TASK-POOL` and binds a real sealed reference bundle; reviewer held-out only after reviewer design freeze.

## Gate truth and lead lane

V1.0 still blocked on separate authenticated Cursor-agent evidence. V1.1 required artifacts are verified. V1.2 broker/local admission are verified but dual-remote overlap is blocked at 0 admitted remotes. V1.3 has zero qualified cells and task pool remains drafting after retry-04 changes-required review. V1.4 first real E2E failed usefully; live adaptive proof and LIVE-142 have not started. V1.5 result acceptance remains. V1.6/V1.7 are queued behind B critical-path work. V2.0 integration/hardening remain drafting; its 168-hour reliability campaign has not started.

Zero-spend, fail-closed, no operational mocks, no known-answer substitution, no admission bypass and no fabricated worker/provider/cost/time/acceptance evidence remain mandatory.
