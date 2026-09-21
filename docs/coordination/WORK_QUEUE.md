# SwarmAI artifact-derived execution queue — after LEAD-20260921-024

Canonical state: `ARTIFACT_REGISTRY.json`. This file is a derived execution view.
Immediate target: V2.0 implementation/artifact-complete candidate. Main merge/public release/additional spend remain separately gated.

Active team:
- Session A / HOST-MAC-DEV / `cursor/v2-runtime-lane`: runtime/control-plane/distributed/recovery + integration ownership.
- Session B / HOST-WIN-DEV / `cursor/v2-product-lane`: evals/knowledge/tools/product/beta.
- ChatGPT: lead/architect/independent reviewer/artifact owner.
- verification lane: dormant reserve.

## Heartbeat bootstrap — not yet verified

Only `trigger=scheduler` counts. Manual/install packet heartbeats are coordination events only.

- A: **1/3** counted scheduler heartbeats (`2026-09-21T02:31:49Z`). Later A updates were manual. Pull/reinstall corrected heartbeat client because the old clock let manual updates suppress scheduler publication.
- B: **0/3**. Only install event `2026-09-21T02:29:19Z`; no scheduler event. Pull/reinstall with diagnostics.
- Do not graduate to hourly until both have 3 consecutive scheduler timestamps 10–25 minutes apart.
- Coordination heartbeat is not `ART-V10-WORKER-HEARTBEAT` authenticated Cursor-agent evidence.

## Source truth

- Main: `b9141fa3150f853586dede0334a47b344571bc16`.
- A runtime: `f393f7fa0ed62d5233350740515ed77069fd4eef`; Actions `35555605844` green.
- B product: `5ede4bf39734462bbaff6dc9e13a5255f58af80d`; Actions `35554834325` green, but no product-source review packet yet.
- Reviewed integration: `9ce727842446b98cfa55c28c7e70808f57f17d7b` / code `ee5a06612aa2e4409fa8bbfd1969225c16887615`.

## Latest independent decisions

- `V2A-003b-R2` / SP1: **accepted packet**. Renewal/expiry terminal + revision/source/cancellation fences satisfy the requested repair. Parent `ART-V15-LEASE-FENCING` remains drafting until V2A-003c.
- `V2A-H6A-R` / SP1: **accepted packet**. Secret-file permissions + fail-closed fresh-config overwrite semantics repaired. Parent hardening artifact remains drafting.
- `V2A-003X` / SP2: **accepted spike packet**. DBOS recommendation = partial reuse for worker execution only; Swarm durable authority remains Postgres-owned. No production migration.
- `V14-REAL-001` / SP2: **changes required**. Real mission used actual brokered local inference at $0, but model output produced an empty worktree diff and review correctly rejected it. Failure preserved.
- `A5-LOCAL-G12-CURRENT-TIP` / SP2: **accepted live-local packet**. Actual Ollama inventory, two brokered local routes, killed-route alternate, quota settlement/deny; no remote claim.
- G12 remote admission: still **0 admitted remote routes**. Metadata auth is not account-specific free/zero-charge eligibility.

## Session A — priority queue

### A0 — V14-REAL-001-R / ART-V14-REAL-E2E / SP2 — immediate
Packet: `docs/coordination/packets/V14-REAL-001-R.md`.

Repair the generic model-response -> isolated-worktree materialization path that yielded an empty diff in the first real mission. No `token_hash.py` special case, supplied defect or fallback answer. Add an unrelated deterministic regression proving valid generic materialization and fail-closed malformed/no-op behavior. Then preregister/run a new actual local brokered mission on a **different bounded subsystem**. Preserve the first failed evidence unchanged.

Acceptance: source repair + regression + new immutable real mission evidence; lead review required. No primary checkout apply.

### A1 — V2A-003c / ART-V15-LEASE-FENCING / SP2 — ready
R2 is lead-reviewed, so result acceptance is unblocked.

Implement durable result acceptance such that:
- current worker generation and project authority match;
- lease belongs to the attempt/task and is unexpired/current;
- task/attempt revision, source revision and cancellation generation match durable authority;
- stale/cancelled/superseded results are denied;
- duplicate submissions are idempotent or rejected without duplicate acceptance/effects;
- exactly one result can become accepted under a race.

Add DB-backed race/negative regressions and exact evidence. Do not integrate until lead-reviewed.

### A2 — reviewed-slice integration receipt / SP1
After A1 review, import only independently reviewed slices into `cursor/v2-integration` using explicit cherry-picks/receipt. Do not bulk-merge runtime history.

### A3 — V12-REMOTE-ADMIT-01 / G12 — blocked external lane
Credentials are reported present and metadata auth works, but exact account Free tier / route zero-charge proof remains unverified. Do not canary with unknown cost. When exact eligibility is established, admit two routes then run actual overlapping governed remote calls. Otherwise keep `ART-V12-REMOTE-OVERLAP` blocked and continue A0/A1.

### A4 — V2A-004 durable worker service/client / SP3
Ready only after A1 lead review. Registration/heartbeat/claim/result/drain over durable store with restart-safe tests; then real Mac+Windows worker evidence.

## Session B — priority queue

### B-HB — scheduler repair / SP1 operational
Pull the corrected heartbeat client and reinstall Windows scheduler with diagnostics. Need scheduler-triggered heartbeats; install/manual events do not count.

### B0 — V2B-000 / integration sync / SP1
Merge only reviewed `origin/cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b` into product lane. Preserve branch-local session/heartbeat files. Do not import runtime V15 WIP. Run Windows baseline Python + console checks and push exact merge SHA/evidence.

### B1 — V2B-001 / ART-V13-TASK-POOL / SP2 — critical path
Freeze calibration vs held-out IDs/hashes for required family x S/M/L/XL coverage plus source/license, size classifier, scorer/grader, prompt, tool and exact model configuration versions. Hidden answers must not be worker-visible. No counted qualification before lead freeze.

### B2 — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3
Calibration only. Repair/freeze weak reviewer benchmark/scorer, version the design, prevent held-out contamination. No reviewer qualification claim yet.

### B3 — W-131B / ART-V13-QUALIFIED-MATRIX / SP2 batches
Starts immediately after B1 lead freeze. Five-observation held-out batches under frozen protocol; count all planning/coordination/retry/review overhead; preserve failures; no threshold changes after results. Continue until required cells meet frozen criterion or honestly block.

### B4 — reviewer held-out qualification
Starts after B2 design freeze. Required for G14 role manifest. Independent lead verifies; no self-qualification.

### B5 — V2B-003a+H1 / ART-V16-PROVENANCE / SP2
Project-scoped versioned provenance/tombstones/non-leak tests. Session B owns domain/repository; hand central migration delta to A.

### B6 — V2B-004a+H4 / ART-V17-APPROVAL-BINDING / SP2
ActionEnvelope / ApprovalGrant / ActionReceipt with mandatory project identity, exact operation/destination/payload digest, expiry/revocation and explicit test fixtures only.

## Honest blocked acceptance artifacts

- `ART-V10-WORKER-HEARTBEAT`: blocked on live authenticated `cursor agent` receipts; coordination heartbeat does not satisfy it.
- `ART-V12-REMOTE-OVERLAP`: 0 admitted remotes.
- `ART-V13-QUALIFIED-MATRIX`: task/version pool not frozen; zero qualified cells.
- `ART-V14-REAL-E2E`: first real attempt failed; A0 repair/rerun required.
- `ART-V14-ROLE-MANIFEST` / live adaptive proof: blocked on G12/G13.
- `ART-LIVE142-CAMPAIGN`: not started; wall-clock cannot be accelerated/backfilled.
- V2.0 accepted reliability: not started; lead reliability protocol requires a frozen candidate and seven real wall-clock days.

## Lead lane

`ART-V20-RELIABILITY-PROTOCOL` was materially advanced in LEAD-024: immutable candidate manifest, invalidating-change rules, seven-day real wall-clock observation, append-only evidence, explicit failure taxonomy, mandatory recovery/security drills and zero-tolerance safety invariants.

Continue V2 security/recovery/integration acceptance plus V2.3/V3 architecture while workers execute routine implementation. Do not steal SP1-SP3 work from Cursor merely because lead could code it faster.
