# SwarmAI worker packet backlog — current

> **SUPERSEDED (2026-09-21, proposed by Fable planning pass):** two-lane backlog, history only. It also still says `ART-V13-TASK-POOL verified/frozen`, which contradicts the registry (`reviewable`). Canonical: `V17_RECOVERY_PACKET_QUEUE.json`.

Updated by `LEAD-20260921-037`. Canonical artifact lifecycle remains in `ARTIFACT_REGISTRY.json`; this file tracks bounded execution state only. `WORK_QUEUE.md`, assignment files, and artifact acceptance contracts control ordering and scope.

## A / HOST-MAC-DEV / `cursor/v2-runtime-lane`

Current tip: `11a7e1d51c4c4d630c7d83c1af65e380c32ad80f`; exact-tip CI `35615739781` green.  
Assignment: `A-RESET-BATCH-04`, generation 4, enabled.

Execute sequentially, one bounded packet per invocation:
1. `V14-REAL-001-R` / `ART-V14-REAL-E2E` — generic model-output materialization repair plus new real non-mock brokered mission.
2. `V2A-003c` / `ART-V15-LEASE-FENCING` — durable result acceptance fencing.

`OPS-AUTO-001-R` was accepted source but human-prompted and must not replay or count as autonomous proof. No generation-4 autonomous source push is visible.

A heartbeat ledger is still publishing, but fresh epoch `reset-20260921-new-lanes-01` was never registered and `status/HOST-MAC-DEV.md` is stale. Refresh the repo-defined heartbeat and autonomous-worker services before trusting new self-launch evidence.

## B / HOST-WIN-DEV identity / `cursor/v2-product-lane`

Current tip: `534476393257794c4e8ebf8d65f44fd090ab28eb`; exact-tip CI `35625964121` green.  
Assignment: `B-RESET-BATCH-05`, generation 5, enabled.

Generation 4 is closed and must not replay:
- `B-OPS-AUTO-SYNC-02` completed at `2693bb59d9142a753546ed55ccb787223572ea94`; CI `35624109265` green.
- `V2B-000` synchronized reviewed integration baseline `9ce727842446b98cfa55c28c7e70808f57f17d7b` onto the product lane.
- `V2B-001-R4` completed at `534476393257794c4e8ebf8d65f44fd090ab28eb`; exact-tip CI `35625964121` green; lead independently froze `ART-V13-TASK-POOL`.

Current generation-5 packet:
1. `V2B-002` / `ART-V13-REVIEWER-QUALIFICATION` — calibration-only reviewer benchmark/scorer repair and freeze candidate. No reviewer held-out qualification and no W-131B product counted qualification in this packet.

The generation-4 source work was human-prompted. An autonomous launch of `V2B-001-R4` exited without a source push, so B autonomous acceptance remains unproven. Generation 5 intentionally contains one dependency-safe packet to create a clean self-launch opportunity.

The active B implementation session reported Linux while using HOST-WIN-DEV coordination identity. Do not use that work as Windows-specific runtime/install evidence.

## ART-OPS-AUTONOMOUS-WORKERS

Status remains **drafting**.

Acceptance still requires A and B each to self-launch at least one repo-assigned packet through the autonomous runner and push attributable implementation evidence without a human prompting the Cursor conversation.

- A: not proven.
- B: not proven; blocked self-launch attempt exists but no attributable source push from that attempt.

Heartbeat/status commits are liveness only.

## G13 / ART-V13-TASK-POOL

### Local B v3 — independently frozen

Authoritative implementation: `cursor/v2-product-lane@534476393257794c4e8ebf8d65f44fd090ab28eb`  
Freeze: `g13-pool-freeze-v3`  
CI: `35625964121` success  
Lead review: `docs/coordination/reviews/ART-V13-TASK-POOL-V3-LEAD-REVIEW.md`

Verified properties:
- 240 held-out inputs / 16 required cells / 15 semantic archetypes per cell;
- materially distinct objectives rather than scenario/numeric/clause-growth siblings;
- fail-closed semantic-archetype, scenario-substitution, clause-containment, digest/template and cross-partition checks;
- separate calibration/held-out identities;
- worker-visible held-out records are input-only with opaque reference handles;
- no local sealed-reference fallback and no fabricated bundle content digest;
- `counted_qualification_ready=false`, `w131b_started=false`;
- generator/verifier + Ruff + mypy + focused/offline pytest reported successful; exact-tip GitHub CI green.

Disposition: **ART-V13-TASK-POOL verified/frozen**. Any semantic change requires a new version/freeze and new lead review.

Still blocked:
- real lead-controlled sealed-reference bundle content digest binding;
- W-131B product counted qualification;
- reviewer calibration/freeze and reviewer held-out qualification.

### External retry-07 — support only

`worker/swarmai-v13-task-pool-freeze-07@02cd0a2ea23342c331e83efd78b7682617dd16d3` is real, one commit above retry06, G13-scoped, and exact-tip CI `35625433324` is green. It remains support/reference evidence only and is not automatically merged or substituted for v3.

### Lane C current

Task: `swarmai-v13-task-pool-v3-audit-01`  
Mode: read-only  
Dispatch: `31b0234a93fe2043b250af91a0f97c6b8561504d`  
Workflow: `35629554863` in progress.

This audit is intentionally static/adversarial and has no acceptance authority.

## Heartbeat stress test

Mode: `stress_5m`; effective worker cadence 5 minutes; only scheduler receipts count.

- A: **0/3 counted** because the fresh reset epoch is not registered. Latest ledger receipt is `16:52:23Z`; status markdown is stale.
- B: **Phase-1 verified 3/3** on `16:17:56Z -> 16:22:59Z -> 16:28:03Z`; status publishing is current.
- Phase 2 (`soak_15m_24h`) has not started. No soak time may be backfilled.

## V14 / ART-V14-REAL-E2E

The first genuine mission remains preserved as failed evidence: real local brokered inference produced implementation text but no material isolated-worktree diff, which was correctly rejected.

Lane A owns the generic repair. Preserve git diff as material authority, fix the raw-source/fenced-parser mismatch and no-op status classification generically, add unrelated temporary-repo regressions, then run a separately preregistered real mission against a different subsystem. No target-specific known answer is permitted.

## V15 / durable worker path

- `V2A-003b-R2`: accepted bounded claim/renew/expire repair slice.
- `ART-V15-LEASE-FENCING`: drafting until `V2A-003c` result acceptance is implemented/reviewed.
- `V2A-H6A-R`: accepted hardening slice.
- DBOS decision: partial reuse only.

After `V2A-003c` review: integrate reviewed slices with a receipt, then `V2A-004` durable worker service/client and real Mac+Windows recovery/multi-host evidence.

## Retained hard blockers

- G12 remote overlap: **0 admitted remote routes**; no paid fallback and no remote canary without exact account/model zero-charge eligibility.
- G13 product counted qualification: sealed reference bundle not yet bound; zero qualified cells.
- G13 reviewer benchmark/qualification incomplete.
- G14 role/live-adaptive proof blocked on G12/G13.
- LIVE-142 campaign not started; real wall clock cannot be backfilled.
- V2.0 168-hour reliability campaign not started; real wall clock cannot be backfilled.
- No main merge, public release/deploy, force push, additional spend, fabricated success or known-answer substitution.
