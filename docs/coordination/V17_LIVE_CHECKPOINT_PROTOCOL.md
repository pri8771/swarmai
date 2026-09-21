# V1.7 live checkpoint protocol

Status: ACTIVE RECOVERY PROTOCOL
Date: 2026-09-21

Goal: no version checkpoint advances on source code alone.

Every checkpoint produces a bound evidence folder:
docs/evidence/v17-checkpoints/<checkpoint-id>/<run-id>/

Required files:
- manifest.json
- commands.json
- environment.json (redacted)
- receipts or domain evidence
- summary.md
- exact source SHA
- exact relevant contract/policy versions

## Checkpoint CP0 — exact-tip deterministic health

Must record:
- uv run ruff check ...
- uv run mypy ...
- relevant offline pytest groups;
- current branch SHA;
- GitHub CI state.

If GitHub Actions cannot start jobs, classify the infrastructure reason and record it. Do not call exact-tip CI green.

## Checkpoint CP1 — real V1.4 mission

Pass only when:
- genuine operational mission;
- brokered real local inference;
- actual repo inspection;
- material isolated diff;
- focused regression/check tied to the claimed defect;
- semantic patch correctness independently reviewed;
- reviewer output grounded in the actual diff;
- no auto-apply;
- $0;
- exact candidate/evidence binding.

Worker/model self-review is not the independent lead review.

## Checkpoint CP2 — qualification/inference prerequisites

Evidence:
- G13 pool/reviewer/calibration implementation on current branch;
- frozen digests;
- counted qualification when prerequisites are satisfied;
- exact route/model evidence;
- G12 remote admission/overlap if real zero-charge routes are available;
- blocked account/credential gates represented explicitly.

No provider admission from public metadata/key presence alone.

## Checkpoint CP3 — durable worker/result path

Live local proof must include:
- durable worker registration;
- claim;
- renew;
- process restart;
- expiry/reassignment;
- stale result rejection;
- duplicate result race;
- cancellation generation rejection;
- exactly one accepted result.

If a second physical host is available, add real multi-host proof.
If not, implementation/harness may become reviewable but formal multi-host evidence remains pending.

## Checkpoint CP4 — scoped knowledge

Create two isolated projects A/B.

Must prove live:
- accepted fact/procedure written for A;
- B cannot retrieve A content OR infer candidate existence through ranking output;
- A later mission reuses permitted accepted knowledge;
- supersession changes future retrieval;
- deletion removes future retrieval/dependent summaries;
- retrieval receipt lists selected IDs/versions/provenance/token cost;
- bounded context uses fewer tokens than whole-history baseline.

## Checkpoint CP5 — unified actions/tools/session

Must prove using one shared V1.7 boundary:
1. local/sandbox integration;
2. API/MCP-style integration;
3. session-aware web/browser-like integration.

Negative live/deterministic cases:
- wrong project;
- changed payload;
- changed destination;
- expired/revoked approval;
- stale lease/cancellation generation;
- duplicate retry;
- unknown external outcome;
- session expires/signs out, recovers destination, and does NOT duplicate submission.

## Checkpoint CP6 — V1.7 exact-tip integrated review

Must bind:
- exact source SHA;
- migrations;
- complete configured deterministic checks;
- CP1-CP5 evidence;
- artifact-by-artifact status V1.0-repair through V1.7;
- all remaining time-bound/provider/multi-host external blockers.

"Implementation complete with pending external acceptance" and "accepted V1.7" are separate states.

## Wall-clock campaigns

Any accepted protocol requiring elapsed wall clock starts as early as dependencies permit and runs while later implementation continues.

Never backfill time.
