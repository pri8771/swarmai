# SwarmAI artifact-derived execution queue — V2 acceleration

Canonical state: `ARTIFACT_REGISTRY.json`.
Active implementation team: Cursor Session A on Mac + Cursor Session B on Windows.
ChatGPT remains lead/reviewer/architect. Reserve verification branch is dormant.
Immediate target: V2.0 implementation/artifact-complete candidate.
Main merge/public release/additional spend remain separately gated.

## Pull-driven operating model

Each active application branch now contains:
- `SESSION_INSTRUCTIONS.md`
- cross-platform durable heartbeat client
- platform-specific heartbeat installer

The operator should only need to tell each Cursor session:

> Pull your branch, read SESSION_INSTRUCTIONS.md, and continue.

Every worker then fetches `coordination/swarm-control`, reads the canonical registry/queue/backlog/new lead messages, installs/verifies heartbeat, works the next packet, pushes evidence, and immediately claims another dependency-ready packet.

## Heartbeat bootstrap

Protocol: `HEARTBEAT_PROTOCOL.md`
State: `HEARTBEAT_STATE.json`

Worker cadence:
- A and B publish at effective 15-minute cadence during bootstrap.
- Each needs 3 consecutive valid 15-minute heartbeats.
- Lead validates both histories on the hourly automation.
- Only after both satisfy the requirement does lead set worker effective cadence to hourly.
- Lead automation itself remains hourly because ChatGPT Automations cannot run faster than hourly.
- Stale thresholds: >35m during bootstrap, >90m after hourly graduation.

Notifications:
worker heartbeat/commit/CURSOR message -> GitHub coordination -> hourly lead review -> operator notification.

Heartbeat is coordination liveness, NOT ART-V10 authenticated Cursor-agent evidence.

## Current source truth

### Session A / Mac runtime
- Branch tip: `859271e7adfec892a1fdf1a5dcb6c2612846606d` (coordination-only session-instruction commit).
- Last meaningful implementation source: `e764834a69315d1c2c85f00322c3392aa5037fd9`.
- Evidence-binding tip for submitted V2A-003b-R: `c6e0a8f0634eddc473fe66aa1d3cb55352dc25a6`.
- V2A-003b-R local focused evidence: 52 passed.
- Independent lead review: **changes required**, not accepted.

### Session B / Windows product
- Branch tip: `770c80b6ccbcef8f442696508ab95f3696aa3176` (heartbeat/session bootstrap commits only).
- No product implementation has been pushed yet.
- Before B1, Session B should merge reviewed `origin/cursor/v2-integration` into its clean product branch as V2B-000.

### V2 integration
- Branch: `cursor/v2-integration`
- Tip: `9ce727842446b98cfa55c28c7e70808f57f17d7b`
- Application code baseline: `ee5a06612aa2e4409fa8bbfd1969225c16887615`
- Contains only lead-reviewed V2A-001 broker closure + V2A-002 real process restart.
- CI `35550653160` green.
- Do not bulk-merge runtime branch.

## Session A — ready queue

### A0 — V2A-003b-R2 / ART-V15-LEASE-FENCING / SP1
Finish the claim/renew/expire slice; do not restart prior work.

Required:
1. renewal explicitly rejects terminal/incompatible TaskRow state;
2. renewal explicitly rejects terminal/incompatible TaskAttemptRow or accepted-result state;
3. expiry compares lease/attempt task revision, source revision and cancellation generation against current durable authority before returning work to ready;
4. regressions for terminal task, terminal/accepted attempt, post-claim source drift and cancel/revision drift at expiry;
5. preserve prior 52-test behaviors;
6. exact source/evidence SHA + exact-tip CI.

Artifact remains drafting. V2A-003c still follows after lead verification.

### A1 — V2A-H6A-R / ART-V20-FOUNDATION-HARDENING / SP1
Independent while A0 review waits:
- generated compose secret file owner-only on POSIX;
- safe fresh-config overwrite semantics;
- `--force` must not imply safe DB password rotation;
- no secret output;
- focused tests + exact evidence.

### A2 — V2A-003X / ART-V15-DBOS-REUSE / SP2
If A0/H6A wait on lead:
- isolated spike only;
- actual pinned DBOS API/version;
- durable workflow/queue restart/duplicate semantics;
- demonstrate Swarm fencing remains independent;
- ADR: reuse / partial reuse / do not adopt;
- no production transport switch.

### A3 — current-tip local G12 proof / SP2
After critical V15 work or in a non-conflicting A worktree:
- actual local Ollama route inventory;
- actual brokered local inference;
- controlled route disable -> actual permitted alternative;
- reservation/settlement/quota deny;
- exact source/model/config identity;
- no remote claim.

Historical stub evidence remains deterministic regression prep only.

### After A0 lead verification
- V2A-003c result acceptance fence.
- V2A-004 durable worker service/client.
- actual Mac+Windows multi-host worker proof.
- V1.8 site epoch / real backup restore.
- integrate only reviewed slices.

## Session B — ready queue

### B0 — V2B-000 / integration-sync / SP1
Because no product implementation exists yet:
- merge only `origin/cursor/v2-integration` into product lane;
- keep branch-local heartbeat/session files;
- do not import runtime V15 WIP;
- run available baseline Python + console checks;
- push exact merge SHA and Windows observations.

### B1 — V2B-001 / ART-V13-TASK-POOL / SP2
Freeze calibration vs held-out task/version manifest. No counted qualification before lead freeze.

### B2 — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair/freeze. No held-out contamination or qualification claim.

### B3 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned knowledge/provenance; permission filter before ranking; tombstones/supersession; two-project non-leak tests. Send central migration delta to A.

### B4 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope / ApprovalGrant / ActionReceipt with mandatory project identity and exact effect binding; no operational demo default.

Then permission-first retrieval -> supersession/deletion -> effect-key semantics -> extensions -> beta/non-demo self-development.

## Honest blocked acceptance artifacts

- ART-V10-WORKER-HEARTBEAT: live Cursor-agent authentication/receipts still blocked; coordination heartbeat does not satisfy it.
- ART-V12-REMOTE-OVERLAP: 0 admissible remote routes.
- ART-V13-QUALIFIED-MATRIX: blocked until B1 freeze and counted held-out runs.
- ART-V14 live adaptive proof: blocked on G12/G13.
- LIVE-142 and V2 reliability observation: real wall-clock only.

## Lead lane

Lead reviews every new A/B artifact, updates registry first, fixes architecture ambiguity, maintains V2.3/V3 contracts, and restocks the two queues. Verification branch remains dormant unless a concrete isolated bottleneck is explicitly reassigned.
