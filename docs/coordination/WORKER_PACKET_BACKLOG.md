# SwarmAI worker packet backlog — current

Updated: 2026-09-21T03:48:22Z after `LEAD-20260921-025`. Canonical artifact lifecycle remains in `ARTIFACT_REGISTRY.json`; this backlog contains bounded execution packets only.

## New shared execution blocker

A and B both contain the newly added repo-driven autonomous-runner source, and both exact-tip offline CI jobs are red at Ruff:
- A `1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, run `35558067148`, offline job `106205483700`.
- B `6b0e1277051ae90fe1d56825d3e771b042380755`, run `35558073323`.

A's log reports 32 findings, dominated by E501 in `scripts/coordination/autonomous_worker.py` plus F841 unused `last_sent` in `scripts/coordination/heartbeat.py`. Console jobs are green; later offline checks are skipped. No repo-assigned autonomous packet self-launch has been observed on either host.

### READY A-AUTO — OPS-AUTO-001-R / ART-OPS-AUTONOMOUS-WORKERS / SP1 — immediate
Packet: `docs/coordination/packets/OPS-AUTO-001-R.md`.
Assignment: `A-AUTONOMY-RUNNER-REPAIR-02`, generation 2, enabled.

Fix coordination-script Ruff failures without weakening one-packet/generation, dirty-worktree, branch, no-remote-change, no-force-push or no-self-accept safety. Add focused regressions and return exact-tip CI. Intended parent artifact transition remains `drafting -> drafting` with source blocker removed; host proof is still required later.

B's autonomous assignment is `B-AUTONOMY-HOLD-RUNNER-02`, generation 2, disabled until this shared repair is independently reviewed and safely propagated. Its B0/B1/B2 queue is preserved and must not replay from generation 1.

## Heartbeat bootstrap

Only `trigger=scheduler` counts. Coordination liveness is separate from autonomous-worker proof and ART-V10 Cursor-agent evidence.

- A: fresh scheduler receipt `2026-09-21T03:47:19Z`; current streak **1/3**. Previous 02:31 receipt is outside the 10-25m consecutive window.
- B: first fresh scheduler receipt after reinstall `2026-09-21T03:43:40Z`; current streak **1/3**.
- Keep 15-minute effective worker publication cadence until both independently reach 3/3. ChatGPT lead remains hourly.

## Retained latest lead review dispositions

- **V2A-003b-R2 / ART-V15-LEASE-FENCING / SP1 — accepted packet.** Parent remains drafting pending result acceptance.
- **V2A-H6A-R / ART-V20-FOUNDATION-HARDENING / SP1 — accepted packet.** Parent remains drafting.
- **V2A-003X / ART-V15-DBOS-REUSE / SP2 — accepted spike.** Partial DBOS reuse only; Swarm durable authority stays PostgreSQL-owned.
- **V14-REAL-001 / ART-V14-REAL-E2E / SP2 — changes required.** Genuine brokered local mission failed because model output created no material diff; preserved as failure.
- **A5-LOCAL-G12-CURRENT-TIP / SP2 — accepted live-local evidence.** Actual local two-model broker/fallback/quota proof; no remote claim.
- **V12-REMOTE-ADMIT-01 — blocked honestly.** 0 admitted remote routes; metadata auth is not zero-charge account eligibility.

`WORKER_PERFORMANCE.json` is unchanged this heartbeat because no new bounded implementation packet reached lead review.

## Session A — runtime/control-plane/integration

### QUEUED-AFTER-AUTO A0 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2
Full packet: `docs/coordination/packets/V14-REAL-001-R.md`.

After OPS-AUTO-001-R lead review/new assignment generation, repair generic model-response -> isolated-worktree materialization without target-specific logic/known answers; add unrelated valid-patch and malformed/no-op regressions; then preregister/run a new actual local brokered mission on a different bounded subsystem. Preserve the first failed evidence.

### QUEUED A1 — V2A-003c / ART-V15-LEASE-FENCING / SP2
Dependencies: V2A-003b-R2 lead-accepted. Execute after V14 repair in the next safe generation unless lead reprioritizes.

Implement durable result acceptance:
1. worker generation/project current;
2. lease current/unexpired and bound to attempt/task;
3. task/attempt revision, source revision and cancellation generation match durable authority;
4. stale/cancelled/superseded result denied;
5. duplicate submissions cannot duplicate acceptance/effects;
6. race permits exactly one accepted result.

Evidence: DB-backed positive/negative/race tests, exact source/evidence SHA, exact-tip CI.

### BLOCKED-ON-A1 A2 — reviewed-slice integration receipt / SP1
After A1 lead review, integrate only reviewed V15/H6A slices into `cursor/v2-integration` with explicit receipt. No bulk runtime merge.

### BLOCKED-ON-A1 A3 — V2A-004 / ART-V15-WORKER-PROTOCOL / SP3
Durable registration/heartbeat/claim/result/drain client/service with restart-safe tests, then prepare actual Mac+Windows multi-host evidence.

### BLOCKED-EXTERNAL A-G12 — ART-V12-REMOTE-OVERLAP
0 admitted remotes. No remote inference until exact account Free tier/model zero price/quota/health and bounded-canary eligibility are independently established.

## Session B — evaluation/knowledge/tools/product/beta

Autonomous product execution is temporarily held because B exact-tip offline CI is knowingly red from the shared runner source. Keep heartbeat scheduler active. After repair propagation, lead issues a new enabled assignment generation with:

### B0 — V2B-000 / integration sync / SP1
Merge only reviewed `cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b` into product lane, preserving host/session files. Run Windows Python + console baseline and return exact merge/evidence.

### B1 — V2B-001 / ART-V13-TASK-POOL / SP2
Freeze calibration vs held-out IDs/hashes for family x S/M/L/XL plus source/license, size classifier, scorer/grader, prompt, tool and exact model config versions. Hidden answers remain worker-invisible. No counted qualification before lead freeze.

### B2 — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair/freeze. No held-out contamination or qualification claim.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Starts only after B1 lead freeze. Preserve all outcomes and full workflow overhead; no post-result threshold changes.

### B4 — reviewer held-out qualification
Starts only after B2 design freeze. Required for G14 role manifest.

### B5 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned provenance/tombstones/non-leak tests; B owns domain/repository and hands central migration delta to A.

### B6 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope / ApprovalGrant / ActionReceipt with mandatory project identity and exact operation/destination/payload digest, expiry/revocation, explicit test fixtures only.

## Acceptance blockers — do not relabel

- `ART-OPS-HEARTBEAT`: A 1/3, B 1/3.
- `ART-OPS-AUTONOMOUS-WORKERS`: no verified repo-assigned self-launch/push by either host.
- authenticated Cursor-agent worker receipts absent.
- remote overlap = 0 admitted routes.
- G13 task pool/reviewer not frozen; zero qualified cells.
- V14 real E2E first attempt failed; repair/rerun queued after autonomous source repair.
- G14 live adaptation blocked on G12/G13.
- LIVE-142 not started.
- V2.0 reliability wall-clock not started.

## Lead-owned parallel work

`ART-V23-OPS-PLATFORM` now includes a concrete weighted-deficit multimission scheduler contract, SchedulerDecisionReceipt, anti-spawn-amplification, restart/drain/fleet/portability invariants and a frozen-shape future acceptance protocol. It remains drafting architecture and is not assigned into V2.0 source while the current critical path is active.
