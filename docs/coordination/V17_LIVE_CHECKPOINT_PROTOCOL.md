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

---

## Proposed amendments (Fable planning pass, 2026-09-21 — effective only after lead approval)

Motivation: findings V1–V5 of `V17_CODE_AUDIT_20260921_2030_FABLE.md`.

1. **Operational-path rule.** A checkpoint for a subsystem passes only if the evidence shows the subsystem was reached from an operational entrypoint (mission, API or CLI), not only from a test or a standalone script. CP4 requires real missions; CP5 requires all three integrations to pass through one gateway object; CP6 requires one mission whose record contains broker, lease, knowledge and action receipts.
2. **Own-run rule.** Every packet's test output is produced by that packet's own run. Byte-identical outputs shared across packets count once.
3. **Skips are not passes.** Evidence lists every skipped or deselected test by name. A required case that was skipped is `not_run`.
4. **Requirement tables.** CP evidence carries a machine-readable `requirements` map (`name → demonstrated, detail`) covering every bullet of the checkpoint definition.
5. **CP3 additions made explicit.** Duplicate-result race must be concurrent across processes; cancellation-generation rejection must be exercised (packet `R17a`).
6. **CP4 additions made explicit.** Existence-inference negative (B's actor-visible receipt is invariant to the size of A's corpus) and strict token savings (`<`, not `>= 0`) (packet `R25b`).
7. **CP5 additions made explicit.** Response loss, kill between `begin_execution` and finalize, concurrent execution from two processes, login-never-submits (packets `R33a`/`R33b`, cases in `packets/R32a.md`).
8. **Run directories are write-once.** A rerun gets a new run-id; failed runs stay committed.
