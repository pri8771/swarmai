> **Latest owner assignment — 2026-09-22:** GPT-6 Sol in a new Codex task is the next SwarmAI implementation owner; target accepted LIVE V1.7. Read `docs/coordination/OWNER_RACE_V17_20260922.md` and `docs/coordination/GPT6_SOL_SWARM_V17_RACE_20260922.md` first. State: ASSIGNED_WAITING_FOR_WORKER, not launched. This supersedes older worker/pause routing below only; existing evidence, review holds and action grants are unchanged. No new scheduler or watcher.

# SwarmAI execution queue — single active Cursor session

Date: 2026-09-21
Canonical artifact lifecycle: `ARTIFACT_REGISTRY.json`

## Active session

Session: `CURSOR-V17-SINGLE`
Branch: `cursor/v17-single-session`
Heartbeat: exactly one producer per `SINGLE_SESSION_HEARTBEAT.md`

No other implementation lanes are authorized.

## Queue

### 0. Bootstrap
- read canonical coordination;
- stop legacy A/B local heartbeat/autonomous processes if present;
- start exactly one 5-minute heartbeat producer;
- baseline test/lint/typecheck;
- inspect runtime/product/integration donor branches.

### 1. Current gating work
- reconcile V1.3 registry/state discrepancy before claiming status;
- finish reviewer calibration/qualification machinery;
- preserve held-out answer sealing;
- complete generic V1.4 materialization repair;
- run a new genuine real E2E mission when prerequisites are available;
- preserve local inference and fail-closed remote admission.

### 2. V1.5
- durable result acceptance fencing;
- worker protocol/service/client;
- restart/drain/cancel;
- multi-host/recovery harness and real evidence only when actually available.

### 3. V1.6
- versioned scoped knowledge repository;
- permission-first retrieval;
- provenance receipts;
- supersession/contradiction/deletion;
- MemoryStore adapter;
- context-budget evidence.

### 4. V1.7
- ActionEnvelope / ApprovalGrant / ActionReceipt;
- ToolGateway policy/approval/effect integration;
- adapter interface + manifest;
- local/API/browser-session integration classes;
- safe session recovery;
- permission/effect negative suite.

## Completion

Stop current implementation scope after a V1.7 implementation-complete/reviewable candidate is pushed.

Do not self-accept.
Do not merge main.
Do not public deploy/release.
Do not spend.
Do not fabricate unavailable live/provider/OS/multi-host evidence.

Future V1.8-V3.0 work is planning only in the forward-plan/backlog documents.
