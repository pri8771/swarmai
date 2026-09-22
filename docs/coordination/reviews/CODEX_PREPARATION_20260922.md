# Codex independent review preparation — SwarmAI

Reviewer: Codex portfolio coordinator, with bounded lower-cost mechanical checks. ChatGPT remains formal reviewer/acceptor. Owner minimum and native ceiling: genuinely live V1.7, then stop.

## Identity and ownership

Canonical scope/reviews: `coordination/swarm-control@580f11867496958e5ef7756894888771667da65d`. Exact tested implementation: `cursor/v17-single-session@05fe7807db3509d68dd8a86a0616c9e8ffaa2307`; R27c production repair under review remains `8dbe5d810d732f17806ac9611bec78383201ac82` plus later R27d integrity changes.

Sole worker: Fable, epoch `fable-v17-20260922-01`, existing CURSOR-V17-SINGLE stream. Canonical takeover record describes prior Cursor idle/clean inspection; Codex did not independently inspect those historical processes or take ownership. Latest observed tick at `02:20:06Z` repeats R02b attempt 2 and meaningful activity `02:08:48Z`. A timer publication is not proof of continued model activity; no crash inference or takeover follows.

Origins verified and isolated worktrees clean. Worker dirty state/process is not inspected. Native heartbeat and lead writers are preserved. Existing ChatGPT task reports its lead-sync automation disabled; no schedule change was made or independently audited here. This proposal claims only new review/evidence paths, not the queue, execution control or implementation.

## Review reconciliation

Canonical `ART-V17-APPROVAL-BINDING-R27C-LEAD-REVIEW.md` already says **CHANGES REQUIRED**, not awaiting an initial review. R27d is a bounded accepted slice; parent artifact remains drafting. R02a guard and R17a local harness have narrow accepted evidence, not CP1/CP3 mission-path acceptance.

Current source still calls `begin_execution(..., fence_reader=None)` in `src/swarm/tools/v17_gateway.py:150–152`. `effects.py:487–519` consumes an approval only when the effect's approval_consumed_at is null; an already-attempted effect using a new grant validates it without consuming/rebinding it. Thus both existing R27c blockers remain. Preserve R27e/R28a holds.

## Independent checks

Evidence: `docs/coordination/reviews/evidence/CODEX-20260922/`.

- R02c targeted edit tests: 7 passed; cancellation/transaction/reservation tests: 20 passed on a wholly separate PostgreSQL 16.13 cluster, TCP disabled. That test cluster was stopped. No production DB was touched.
- Existing gateway negatives: 13 passed, 1 durable test deselected (durable coverage separately above).
- Ruff and mypy (169 source files): pass. Full suite not repeated.
- Separate executable offline reproducer: after failed/provably-not-applied attempt A, replacement one-use grant B admits retry but retains used_count=0; B then admits a second effect. Two simulated adapter calls occur for one permitted use. The controlled not_applied seam mirrors the existing test; this is in-memory engineering evidence, not external/live proof.
- Hosted run `35678356314` at `32ddb911...` has three failed jobs, each runner_id=0 and zero steps: no executable CI evidence.

Recommendation: **REWORK_FOUND** for R27c, corroborating the authorized review; **REVIEW_BLOCKED** for the V1.7 live milestone.

## Smallest next action — existing R27c-R1

State: **PREPARED / WAITING_FOR_WORKER_ACK**. Request ChatGPT confirm the existing repair decision and route it to the same Fable session at a safe boundary; preserve any R02b attempt already running and its original evidence. Do not start a third attempt or another implementation worker.

Use the existing native R27c review; no new roadmap. First bind authoritative durable lease/cancellation fences inside admission and prove a generation change after precheck denies the adapter with zero approval use. Then consume/rebind each distinct replacement grant exactly once while preserving same-grant/same-effect retry semantics. Shared surfaces: `src/swarm/tools/effects.py`, `src/swarm/tools/v17_gateway.py`, focused integration tests and minimal owning fence provider. Split into small reviewable concerns where possible without weakening the atomic transaction.

Return current-base implementation SHA, exact command/exits, both regressions, focused transaction/reservation tests x5, full offline suite, Ruff and mypy. R27e/R28a stay held until an actual authorized independent review records the repaired source. Update the worker's next action to repair rather than waiting for an initial review, only after it acknowledges current canonical direction.

## Live frontier

CP1 attempt 008/2 was reported running; no terminal result exists in the inspected source. CP3 evidence is a local separate-process harness; production mission wiring and second physical host remain separate gates. CP4, CP5, R33c real external action and integrated CP6 are not passed. Required lower-version provider/sealed-reference/host/review/elapsed-time gates remain; the 24-hour LIVE142 campaign cannot be backfilled. A running loopback API at the worker's recorded older candidate is not V1.7 live.

Reuse native gate records for exact host/account/action requests. GitHub access in this review environment is not proof of the worker host's authenticated action path, and no issue/comment/close checkpoint was performed outside SwarmAI. No scope/control change, external model call, new spend, main merge or public release.

## Subsequent read-only local evidence — 2026-09-22T02:39Z

The actual runbook-named local checkout was verified: origin `pri8771/swarmai`, branch `cursor/v17-single-session`, HEAD `05fe780...`. It has untracked `docs/evidence/v14-real-e2e/v14-real-008/attempt2/`; preserve it. `mission-run.stdout.json` is terminal **failed / repair_required**, mission `ec5bf495ed3d4318b97af2ea2840b5be`, updated `02:11:59.854522Z`, cost $0, project_id null. SHA256 `45a5236057ab57c53c555542f17a4d945f06f4d21c5699c863dc0131eb7e47f2`; stderr empty. This supersedes the reported RUNNING interpretation above, but is uncommitted local evidence, not accepted or remotely retained proof. Sanitized observation: `evidence/CODEX-20260922/local-readback.json`; original bytes remain untouched with the worker.

`com.swarmai.v17-candidate` is running and loopback health/live and health/ready both return 200 (operational, database up, allow_paid=false). Loaded process source identity is not bound by reading the newer checkout HEAD. The existing periodic heartbeat job is active and between invocations, last exit 0; this does not prove model progress. No service, process, evidence or worker file was changed.

Priority at the worker's next safe boundary: preserve/package failed attempt 2, reconcile its own stale status, then acknowledge the existing R27c-R1 repair. No third attempt, new model call, reset or implementation takeover. The lead was sent this material update through the existing task. PR #17 remains a recommendation awaiting formal verdict/worker acknowledgement.
