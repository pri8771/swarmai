# SwarmAI worker packet backlog

Updated: 2026-09-20
This is an execution/decomposition aid. Gate contracts remain authoritative.

## Current V1.4 worker packets

### W-041A — Authenticate Cursor CLI
- Gate: G10 / FIX-004
- SP: 1 worker-side verification + external human auth dependency
- Worker: Cursor
- Ready: blocked on operator completing live CLI login
- Done when: `cursor agent status` and `cursor agent whoami` both verify authenticated without exposing credentials.
- Lead role: verify receipts; do not perform login.

### W-041B — Authenticated manual worker receipt
- Gate: G10 / FIX-004
- SP: 2
- Depends on: W-041A
- Worker: Cursor
- Done when: one bounded authenticated Cursor-agent invocation executes the coordination prompt, respects lease/timeout, produces sanitized receipt tied to source/config, and performs no unapproved action.

### W-041C — Two genuine hourly worker receipts
- Gate: G10 / FIX-004
- SP: 2
- Depends on: W-041B
- Worker: Cursor
- Done when: two separate scheduler-triggered invocations occur on the real hourly cadence, no overlap/lease violation, both authenticated, both produce sanitized receipts.
- Do not accelerate the cadence to manufacture evidence.

### W-111A — Actual browser console mission journey
- Gate: G11
- SP: 2
- Worker: Cursor
- Ready: evidenced under CURSOR-021; awaiting lead review (not accepted).
- Done when: actual console UI creates/opens an unfamiliar operational mission and the same durable ID/status/artifacts are observed through API and CLI.

### W-111B — Current-candidate control revalidation
- Gate: G11
- SP: 2
- Worker: Cursor
- Ready: evidenced under CURSOR-021; awaiting lead review (not accepted).
- Done when: current operational candidate reruns restart/reopen, cancellation, unsupported outcome and deliberate wrong-output rejection with FIX-003-compliant evidence.

### W-121A — Remote route eligibility ledger
- Gate: G12
- SP: 2
- Worker: Cursor
- Lead supplies shortlist/requirements.
- Done when: at least two candidate remote exact routes have current auth, price/zero-additional-spend eligibility, quota/reset, health and privacy evidence—or are explicitly rejected/blocked.
- Metadata-only auth cannot establish inference eligibility.

### W-121B — Dual-remote overlap mission
- Gate: G12
- SP: 3
- Depends on: two admissible routes from W-121A + local route.
- Worker: Cursor
- Done when: one mission produces overlapping real calls on two independently authorized remote routes plus actual local route/fallback, all through broker admission/reconcile.

### W-131A — Qualification gap map
- Gate: G13
- SP: 1
- Worker: Cursor
- Done when: machine-readable map identifies required family×size cells, existing screening counts, strongest candidate route(s), missing third-model screening, reviewer-role gaps and exact next sample batches under the frozen protocol.

### W-131B — Candidate-cell qualification batches
- Gate: G13
- SP: 2 per batch packet
- Depends on: W-131A.
- Worker: Cursor
- Done when: selected held-out candidate cells add five independent observations, preserve all attempts/overhead and recompute the one-sided Wilson bound.
- One packet = one bounded batch, not “finish all G13.”

### W-131C — Reviewer benchmark calibration/freeze
- Gate: G13/G14
- SP: 3
- Worker: Cursor with lead-owned benchmark contract.
- Done when: review benchmark/scorer defects are debugged only on calibration tasks, a new version is frozen, held-out pool hashes are recorded without exposing answers, and reviewer qualification can start.

### W-141A — Qualified route/role manifest
- Gate: G14
- SP: 1
- Worker: Cursor
- Depends on: G13 qualification evidence.
- Done when: exact planner/reviewer/worker routes permitted for the live G14 mission are enumerated with qualification/profile evidence and resource caps.

### W-141B — Live adaptive swarm proof
- Gate: G14
- SP: 5 conceptually; MUST execute as subpackets below.
- Worker: Cursor.
- Subpackets:
  - W-141B1 SP2: mission fixture/input selection + graph/event instrumentation;
  - W-141B2 SP3: two planner/reviewer configurations + qualified workers through governed broker;
  - W-141B3 SP3: evidence-driven expansion and convergence-driven merge/retire/cancel;
  - W-141B4 SP2: capture logical-agent/session/request/process counters and admission denials.
- Lead reviews after each subpacket.

### W-141C — Elastic vs fixed vs single comparison
- Gate: G14
- SP: 3
- Worker: Cursor
- Done when: same task set runs under all three modes and reports quality, latency, model calls/tokens and coordination overhead without cherry-picking.

### W-142A — Candidate freeze manifest
- Gate: LIVE-142
- SP: 2
- Worker: Cursor; lead approves.
- Done when: candidate/config/provider/profile/task-pool hashes and budgets are frozen before final campaign.

### W-142B — Positive campaign execution
- Gate: LIVE-142
- SP: 5 conceptually; split into four SP2 packets of three preregistered positive missions each.
- Worker: Cursor.
- Preserve all attempts. Do not hide failed slots.

### W-142C — Negative campaign execution
- Gate: LIVE-142
- SP: 3; split into two packets of three negative scenarios.
- Worker: Cursor.

### W-142D — 24-hour protected observation
- Gate: LIVE-142
- SP: 3 operational evidence task
- Worker: Cursor/runtime.
- Done when: real wall-clock window completes with heartbeats/logs/restart evidence and no invalidating runtime/security change.

## Lead-side parallel work

These do not replace worker implementation:
- L-121R: remote provider shortlist and exact evidence checklist.
- L-131R: compute/verify Wilson bounds and choose next candidate cells after each batch.
- L-131V: design/freeze reviewer benchmark after calibration feedback.
- L-142S: select exact final held-out task payloads only after candidate freeze.
- L-142R: independent campaign review and defect triage.

## Future preparation backlog (no V1.5+ implementation yet)

The owner asked the lead to move onto future tasks when current useful lead work is exhausted. Prepare/decompose these in advance, but current V1.5+ implementation remains version-gated until the active V1.4 tranche is accepted or the owner explicitly activates the next tranche.

### FUT-151 — distributed worker execution
- Conceptual size: SP5.
- Lead decomposition target: worker registration (SP2), durable leases/fencing (SP3), second-host enrollment (SP2), kill/recovery proof (SP3), shared-quota two-mission proof (SP3).

### FUT-161 — scoped reusable knowledge
- Conceptual size: SP5.
- Decompose: provenance schema (SP2), retrieval permission tests (SP2), contradiction/supersession logic (SP3), context-budget measurement (SP2), cross-project leak suite (SP3).

### FUT-171 — reliable tool/browser integrations
- Conceptual size: SP5.
- Decompose: integration shortlist (SP1), permission-adapter template (SP2), payload-bound approval contract (SP3), expired-session recovery proof (SP3).

### FUT-181 — cloud/local recovery
- Conceptual size: SP5.
- Decompose only after actual host entitlement is known.

### FUT-191 — independent beta/self-development
- Conceptual size: SP5.
- Decompose: clean install checklist (SP2), external install evidence (SP3), extension/SDK freeze (SP3), isolated self-development PR proof (SP3).

## Queue rule

When one packet blocks on human auth/provider reset/review, Cursor should move to the next dependency-ready packet inside the authorized V1.4 range. The lead should keep 3+ ready packets when practical. Do not jump to unauthorized V1.5 implementation merely because a V1.4 live prerequisite is temporarily blocked.
