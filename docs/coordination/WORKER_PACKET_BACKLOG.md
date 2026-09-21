# SwarmAI worker packet backlog — current

Updated: 2026-09-21T03:05:30Z. Canonical artifact lifecycle remains in `ARTIFACT_REGISTRY.json`; this backlog contains bounded execution packets only.

## Latest lead review dispositions

- **V2A-003b-R2 / ART-V15-LEASE-FENCING / SP1 — accepted packet.** Source `685810cc84d17594fa54a168c1d23b8463dc0871`; evidence `391e8ea217c792cca19de4a2409d06e427c15866`; current descendant `f393f7fa...`, Actions `35555605844` green. Terminal task/attempt renewal fences and lease/attempt-bound expiry revision/source/cancellation authority are present. Parent artifact remains drafting pending V2A-003c.
- **V2A-H6A-R / ART-V20-FOUNDATION-HARDENING / SP1 — accepted packet.** Source `d40c1fd420cd489e30c9ef567691c9fc0d1638e5`; evidence tip `b1a8eee...`; current descendant CI green. Compose secret file gets owner-only POSIX permissions; existing config overwrite is fail-closed without explicit fresh-config acknowledgement; documentation says this is not initialized-DB password rotation. Parent hardening artifact remains drafting.
- **V2A-003X / ART-V15-DBOS-REUSE / SP2 — accepted spike.** Source `0fe0831a642039feae48e63076b6889a195f6036`; evidence `d88a3a6...`. DBOS 3.0.0 proves workflow/step idempotency, not Swarm authority fencing. ADR recommendation = partial reuse only after Swarm durable fencing; no production migration.
- **V14-REAL-001 / ART-V14-REAL-E2E / SP2 — changes required.** Actual mission `d9379d80277644998353a9ca3614eba7`, three brokered qwen3.5:4b calls at $0, but model implementation text yielded an empty worktree diff and review correctly rejected. Failure preserved; repair = `V14-REAL-001-R`.
- **A5-LOCAL-G12-CURRENT-TIP / SP2 — accepted live-local packet.** Execution `84df040...`, evidence/current branch `f393f7fa...`: actual Ollama inventory, real brokered gemma3:4b/qwen3.5:4b calls, killed-route alternate, quota settlement + fourth-call denial. No remote claim.
- **V12-REMOTE-ADMIT-01 — blocked honestly.** OpenRouter/Groq/Gemini metadata auth present; exact account/tier/model zero-charge eligibility not established, so remote canaries remain denied and remote-admitted count remains 0.

## Heartbeat setup packets

Only `trigger=scheduler` counts for the 15-minute bootstrap streak.

### HB-A-BOOTSTRAP / SP1 — active repair
- Host: `HOST-MAC-DEV`; branch `cursor/v2-runtime-lane`.
- Current counted streak: **1/3** (`2026-09-21T02:31:49Z`).
- Pull current heartbeat client and reinstall scheduler; old client allowed manual updates to suppress scheduler clock.
- Produce scheduler-triggered timestamps 10–25m apart; manual packet updates do not count.

### HB-B-BOOTSTRAP / SP1 — active repair
- Host: `HOST-WIN-DEV`; branch `cursor/v2-product-lane`.
- Current counted streak: **0/3**. Only install event at `2026-09-21T02:29:19Z`.
- Pull current heartbeat client and reinstall with diagnostics; produce scheduler-triggered heartbeats.

These coordination packets do not satisfy `ART-V10-WORKER-HEARTBEAT` Cursor-agent authentication evidence.

## Session A — runtime/control-plane/integration

### READY A0 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2 — immediate
Full packet: `docs/coordination/packets/V14-REAL-001-R.md`.

Repair generic model-response -> isolated-worktree materialization without target-specific logic or known answers. Add unrelated valid-patch + malformed/no-op regressions. Then preregister/run a new actual local brokered mission on a different bounded subsystem. Preserve first failed evidence. No primary checkout mutation.

### READY A1 — V2A-003c / ART-V15-LEASE-FENCING / SP2
Dependencies: V2A-003b-R2 lead-accepted.

Implement durable result acceptance:
1. worker generation/project still current;
2. lease current/unexpired and bound to attempt/task;
3. task/attempt revision, source revision and cancellation generation match durable authority;
4. cancelled/superseded/stale result denied;
5. duplicate submissions cannot create duplicate acceptance/effects;
6. race permits exactly one accepted result.

Evidence: DB-backed positive/negative/race tests, exact source/evidence SHA, current-tip CI. Parent artifact stays drafting until lead review.

### READY A2 — reviewed-slice integration receipt / SP1
After A1 lead review, integrate only lead-reviewed V15/H6A slices into `cursor/v2-integration` with explicit receipt. Do not wholesale merge runtime history.

### READY A3 — V2A-004 durable worker service/client / ART-V15-WORKER-PROTOCOL / SP3
Dependency: A1 lead review. Build registration/heartbeat/claim/result/drain client/service against durable store with restart-safe tests. Then prepare Mac+Windows multi-host proof; do not claim it before execution.

### BLOCKED A-G12 — V12-REMOTE-ADMIT-01 / ART-V12-PROVIDER-ELIGIBILITY + REMOTE-OVERLAP
0 admitted remotes. Do not call remote inference until exact account Free tier, exact model zero price, quota/health and bounded-canary eligibility are independently established. If dashboard authentication requires MFA/passkey/consent, request only that precise human step and continue other packets.

### LATER A4 — V2A-018a/b/c/d
Site epoch, backup/restore/reconcile, stale-site fencing after durable worker/control state is reviewable. Source implementation authorized; public deployment is not.

## Session B — evaluation/knowledge/tools/product/beta

No product-source review packet observed yet. Current branch `5ede4bf39734462bbaff6dc9e13a5255f58af80d` has green CI but coordination-only changes.

### READY B0 — V2B-000 / integration sync / SP1
Merge only reviewed `origin/cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b` into product lane. Preserve session/heartbeat files. Do not import runtime V15 history. Run Windows Python+console baseline and return exact merge SHA/results.

### READY B1 — V2B-001 / ART-V13-TASK-POOL / SP2 — critical path
Freeze calibration vs held-out task IDs/hashes for required family x S/M/L/XL coverage plus source/license, size-classifier, scorer/grader, prompt, tool and exact model config versions. Hidden answers not worker-visible. Intended transition: drafting -> reviewable. No counted qualification before lead freeze.

### READY B2 — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration-only reviewer benchmark/scorer repair and freeze. No held-out contamination; no qualification claim. Return versioned benchmark/scorer design for lead review.

### READY-AFTER-B1 B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Use only lead-frozen held-out IDs and versions. Five-observation bounded batches; count planning/coordination/retry/review calls/tokens/cost; preserve all failures; no post-result threshold changes. Continue until required cells meet frozen criterion or honestly block.

### READY B4 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned provenance repository, permission labels, tombstones, two-project non-leak tests. B owns domain/repository; hand central migration delta to A.

### READY B5 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope/ApprovalGrant/ActionReceipt with mandatory project ID and exact operation/destination/payload digest, expiry/revocation and explicit test fixtures only. No operational demo project/default.

## Integration rule

`cursor/v2-integration` receives only independently lead-reviewed slices with an integration receipt. Green descendant CI does not convert an unreviewed ancestor into accepted code.

## Acceptance blockers — do not relabel

- authenticated Cursor-agent worker receipts absent;
- remote overlap = 0 admitted routes;
- G13 task pool/reviewer not frozen; zero qualified cells;
- V14 real E2E first attempt failed; repair/rerun required;
- G14 live adaptation blocked on G12/G13;
- LIVE-142 not started;
- V2.0 reliability wall-clock not started.

## Lead-owned parallel work

`ART-V20-RELIABILITY-PROTOCOL` is now substantially specified: frozen candidate manifest/invalidation rules, seven consecutive real wall-clock days, immutable run evidence, expected/unexpected failure taxonomy, mandatory recovery/security drills and release-level safety invariants. Lead continues V2 security/recovery and V2.3/V3 architecture without taking routine SP1-SP3 implementation from Cursor.
