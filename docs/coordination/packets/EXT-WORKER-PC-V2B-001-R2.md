# EXT-WORKER-PC-V2B-001-R2 — bounded G13 task-pool freeze repair

Artifact: `ART-V13-TASK-POOL`
Intended artifact transition: `drafting -> drafting` (remove repair blockers only; lead freeze remains separate)
Story points: SP2
Preferred executor: `worker-pc` / Claude branch mode
Owner/reviewer: ChatGPT lead

## Why this packet exists

External retry 03 (`swarmai-v13-task-pool-freeze-03`, run `35566726945`) was cancelled after the submitted-task step ran for roughly two hours. It produced neither `results/swarmai-v13-task-pool-freeze-03.json` nor a `worker/swarmai-v13-task-pool-freeze-03` branch. Retry 02 remains the last real scoped source branch and is independently changes-required.

This packet narrows the repair so the worker can produce a reviewable core freeze without attempting unrelated repo-wide work. It does not run or authorize counted qualification.

## Base

Use the last real scoped repair base unless the lead explicitly supplies a newer reviewed base:

- branch: `worker/swarmai-v13-task-pool-freeze-02`
- exact reviewed commit: `bbe41b7770123fef4eb03c4f03f95fc18eefc692`

Create only a fresh `worker/<task-id>` branch through the remote-workers protocol. Never merge automatically.

## Bounded deliverables

1. Create a new versioned freeze-v2 held-out corpus. Worker/model-visible records must be input-only: no plaintext expected output, reference solution, grader result, hidden unit expected value, or equivalent answer-bearing field.
2. Freeze at least 15 independent held-out input cases for each required product-family × size cell: coding/planning/reasoning/extraction × S/M/L/XL (16 cells, minimum 240 counted-input records total).
3. Define a sealed grader-reference boundary. Public records bind each case to an opaque `hidden_reference_id` and version/digest identity only. Actual hidden references are not committed to the worker-visible branch. Missing/mismatched identity must fail closed.
4. Implement/version the independence and contamination verifier for calibration/held-out ID overlap, record/input digest overlap, prompt overlap, duplicate held-out prompt, duplicate normalized/template input, and seed-isomorphic/template-equivalent cases. Such cases are ineligible rather than silently counted.
5. Pin non-floating identities for the pool, records, split, size classifier, scorer/grader contract, prompt, tool protocol, exact-model-config schema, independence checker, and sealed-reference interface/bundle identity.
6. Make `counted_qualification_ready` true only when all required freeze conditions above are mechanically satisfied. This flag means the pool is eligible for later lead review; it does not qualify any model/route.
7. Add focused negative tests for the highest-risk freeze failures: visible answer leakage; <15 independent inputs in any required cell; split/input/prompt/template overlap; missing or mismatched hidden-reference identity; mutated pool bytes; incomplete/floating required identity. Preserve retry-02/v1 files as historical incomplete evidence.

## Scope / ownership

Stay in benchmark/evaluation/evidence/test paths. Do not edit Session-A-owned shared API/store/routes/schemas/CLI/database migration/lockfile files. If a shared change is needed, record a handoff note rather than changing it.

## Verification

Run the freeze-v2 generator/verifier and the focused task-pool test module(s). Run Ruff on changed Python and mypy on affected modules when available. Do not spend the remote task window on unrelated broad suites; GitHub CI can supply broader independent evidence after a branch exists.

If the executor denies a command or the packet reaches its runtime boundary, report exactly what did and did not run. Do not invent passing checks. A partial branch is useful only when clearly labelled partial.

## Required return

Push the fresh worker branch and report:

- exact commit SHA and parent;
- changed files;
- exact commands, exit codes/results, and unexecuted checks;
- freeze-v2 manifest/pool identities;
- held-out independent input count for every required cell;
- total worker-visible answer-leak count (must be zero for eligibility);
- sealed-reference interface identity/digest behavior;
- independence/contamination statistics;
- remaining blockers.

Request lead review only. Do not claim `ART-V13-TASK-POOL` reviewable, verified, accepted, or frozen yourself. Do not run W-131B counted qualification.

## Packet acceptance

The packet is reviewable when a real source branch/commit exists with scoped changes, the v2 corpus contains the required input depth, hidden answers are absent from worker-visible counted data, the sealed-reference and independence checks fail closed, and focused verification has actually executed or any unavailable verification is explicitly recorded. Artifact lifecycle promotion remains an independent lead decision.
