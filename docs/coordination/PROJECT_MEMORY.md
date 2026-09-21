# SwarmAI compact project memory

Curated 2026-09-21 after `LEAD-20260921-024`. `ARTIFACT_REGISTRY.json` is canonical; this is a compact derived orientation, not proof by itself.

## Authority and team

Owner authorizes source implementation through V3.0. Major milestones: V1.7, V2.3, V3.0. Immediate target: V2.0 implementation/artifact-complete candidate. Main merge, public release/deployment and additional spend remain separately gated.

Active implementation team:
- ChatGPT: lead/architect/independent reviewer/artifact owner.
- Cursor A / HOST-MAC-DEV / `cursor/v2-runtime-lane`: runtime, control plane, distributed/recovery + integration owner on `cursor/v2-integration`.
- Cursor B / HOST-WIN-DEV / `cursor/v2-product-lane`: evaluation, knowledge, tools, product, beta.
- verification lane is dormant reserve.

Artifacts are primary; packets advance artifact states. Cursor should do routine SP1-SP3 work. Lead reviews independently and advances contracts/recovery/security/evaluation/future artifacts in parallel.

## Current source truth

Main: `b9141fa3150f853586dede0334a47b344571bc16`.
A runtime: `f393f7fa0ed62d5233350740515ed77069fd4eef`, Actions `35555605844` green.
B product: `5ede4bf39734462bbaff6dc9e13a5255f58af80d`, Actions `35554834325` green, but no product implementation packet yet.
Reviewed integration baseline: `9ce727842446b98cfa55c28c7e70808f57f17d7b`, code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.

## Heartbeat truth

`HEARTBEAT_PROTOCOL.md` controls. Only `trigger=scheduler` counts toward bootstrap proof; manual/install work-status updates do not. Need 3 consecutive scheduler heartbeats 10–25 minutes apart for BOTH workers before effective cadence graduates to hourly.

At LEAD-024:
- A: **1/3** counted scheduler heartbeats, timestamp `2026-09-21T02:31:49Z`. Later A heartbeats are manual and do not advance streak.
- B: **0/3**. One `trigger=install` event at `2026-09-21T02:29:19Z`; no scheduler event.
- Old heartbeat client let manual updates suppress scheduler timing; branch fix exists. A/B must pull/reinstall; B needs diagnostics.
- No graduation. Coordination heartbeat is not `ART-V10-WORKER-HEARTBEAT` authenticated Cursor-agent evidence.

## Lead-reviewed new work

**V2A-003b-R2 / SP1 accepted packet.** Source `685810cc84d17594fa54a168c1d23b8463dc0871`, evidence `391e8ea...`; current descendant CI green. Renewal now fences terminal task/attempt and current revision/source/cancellation authority; expiry compares lease/attempt stamps before requeue. Whole `ART-V15-LEASE-FENCING` stays drafting until V2A-003c result-acceptance fencing.

**V2A-H6A-R / SP1 accepted packet.** Source `d40c1fd420cd489e30c9ef567691c9fc0d1638e5`. Generated compose secret file gets POSIX 0600; overwrite requires explicit fresh-config acknowledgement and is documented as not live Postgres credential rotation. Parent V2 hardening artifact stays drafting.

**V2A-003X / SP2 accepted architecture spike.** Source `0fe0831a642039feae48e63076b6889a195f6036`. DBOS 3.0.0 demonstrates workflow/step durability/idempotency but not Swarm source/cancel/project/lease authority. Recommendation: partial reuse for worker execution only after Swarm fencing; keep durable authority in Postgres. No production migration.

**V14-REAL-001 was a genuine failed mission, not a pass.** Mission `d9379d80277644998353a9ca3614eba7` used 3 actual brokered `qwen3.5:4b` calls at $0 with real repo inspection, but model implementation text created no material worktree diff; review correctly rejected it. Failure is preserved. Immediate repair packet: `V14-REAL-001-R` in `docs/coordination/packets/`.

**A5 local G12 proof accepted as live-local packet.** Execution `84df040...`, evidence/branch `f393f7fa...`: actual Ollama 0.21.0 inventory, real brokered gemma3:4b + qwen3.5:4b calls with tokens/$0, killed-route denial -> real alternate route, quota settlement -> fourth request denied. No remote claim. Broader G12 remains blocked.

Remote admission probe reports OpenRouter/Groq/Gemini credentials present/auth metadata OK, but exact account free tier/zero-charge eligibility is unverified; canaries correctly fail closed. G12 remote overlap remains **0 admitted routes**.

## Immediate queues

A priority:
1. `V14-REAL-001-R` SP2 — generic model-output -> isolated-worktree materialization repair + unrelated regression + new preregistered real mission on a different subsystem.
2. `V2A-003c` SP2 — durable result acceptance: stale generation/lease/task/source/cancellation and duplicate result denial; exactly one accepted result.
3. integrate only newly lead-reviewed slices with receipt; no wholesale runtime merge.

B priority:
1. pull/reinstall corrected Windows heartbeat scheduler.
2. `V2B-000` SP1 — merge only reviewed integration baseline into product lane; run Windows baseline.
3. `V2B-001` SP2 — freeze G13 calibration/held-out IDs/hashes and scorer/size/prompt/tool/model versions.
4. `V2B-002` SP3 — reviewer calibration/freeze. Counted held-out qualification starts only after frozen manifests are lead-reviewed.

## Gate truth

V1.0 still blocked on separate authenticated Cursor-agent worker evidence. V1.1 required artifacts are verified. V1.2 broker is verified but dual-remote overlap blocked at 0 admitted remotes. V1.3 has 72 provisional screening cells but zero qualified cells; task pool/reviewer design not frozen. V1.4 real E2E first run failed usefully; live adaptive proof and LIVE-142 have not started. V1.5 lease claim/renew/expire repair is review-passed at packet level; result acceptance remains. V1.6/V1.7 are ready for B implementation. V2.0 integration/hardening remain drafting.

Lead advanced `ART-V20-RELIABILITY-PROTOCOL`: frozen-candidate manifest, change invalidation, seven-day real wall-clock observation, append-only evidence, mandatory restart/worker/provider/quota/tool/knowledge/backup/site-epoch/migration drills and zero-tolerance safety invariants. No elapsed time is claimed.

Zero-spend, fail-closed, no operational mocks, no known-answer substitution, no admission bypass, no fabricated worker/provider/cost/time/acceptance evidence remain mandatory.
