# ART-V13-TASK-POOL repair contract — qualification-ready freeze v2

Date: 2026-09-21
Artifact: `ART-V13-TASK-POOL`
Repair packet: `EXT-WORKER-PC-V2B-001-R1`
Authority: `docs/coordination/EVAL_131_QUALIFICATION_PROTOCOL.md`

## Review finding that requires this repair

External worker retry `swarmai-v13-task-pool-freeze-02` produced a real, scoped branch at `bbe41b7770123fef4eb03c4f03f95fc18eefc692`, but independent lead review did **not** freeze or promote the task-pool artifact.

The proposed v1 freeze is useful implementation/evidence, but it is not qualification-ready:

1. `benchmarks/starter.jsonl` exposes plaintext hidden-answer/grader/reference fields to a worker that can read the branch. Counted held-out workers must never receive those fields.
2. The frozen required cells contain only five held-out cases each. EVAL-131 requires at least fifteen **independent** held-out observations before a cell can qualify; replaying the same five cases cannot create independent observations.
3. The v1 verifier reports seed-isomorphic held-out variants. Isomorphic variants must not be counted as independent observations for the Wilson confidence criterion.
4. The remote worker environment did not execute Python, pytest, Ruff or mypy and no GitHub workflow ran for `bbe41b...`. A reviewable repair requires executable verification evidence from an environment that can run it.

Preserve v1 and its review as immutable failed/incomplete evidence. Do not rewrite it into a successful freeze.

## Required v2 boundary

Create a new freeze/version rather than mutating the meaning of `g13-pool-freeze-v1`.

### 1. Worker-visible held-out inputs are input-only

For records eligible for **counted qualification**, the worker/model-visible repository material may contain only task input, permitted resources, public metadata, case identity/version, size features and opaque hidden-reference identity/digest.

It must not expose answer-bearing fields, including at minimum:

- `expected_output`
- hidden grader fixtures or expected grader results
- `reference_solution`
- hidden unit-test cases/outputs
- `broken_code` when it reveals the expected repaired answer rather than legitimate task input
- any equivalent renamed field whose semantics reveal the held-out answer

A verifier must fail closed if counted-held-out worker-visible material contains these fields or known answer-bearing equivalents.

Existing `benchmarks/starter.jsonl` may remain preserved as historical screening/calibration source where appropriate, but any record whose hidden reference is readable by the worker is **ineligible for counted qualification**.

### 2. Sealed hidden-reference interface

Define a grader-side hidden-reference contract without committing plaintext hidden references on the worker branch.

The public manifest should bind each counted case to an opaque `hidden_reference_id` and cryptographic digest/version of the hidden-reference bundle or record. The actual hidden reference lives in a private/sealed location available only to the grading harness after a model response is captured.

The contract must make these boundaries explicit:

- worker/model receives input only;
- evaluator captures immutable response/attempt metadata first;
- grader resolves hidden reference separately;
- grader output is stored after the attempt and is not fed back as a new independent sample;
- absence/mismatch of the sealed bundle fails the run closed;
- no fallback to plaintext repository answers.

Do not put credentials, private paths, or secret values in Git. Use an opaque reference/config key for the sealed source.

### 3. Minimum independent held-out depth

For each required product family × size cell:

- families: `coding`, `planning`, `reasoning`, `extraction`;
- sizes: `S`, `M`, `L`, `XL`;
- minimum independent counted-held-out case count in the frozen pool: **15**;
- maximum sampling remains governed by EVAL-131 (60 per exact model configuration/cell).

This is pool depth, not a qualification claim. No model configuration becomes qualified merely because 15 cases exist.

Generate enough distinct input cases for at least 15 per required cell. If more are generated for reserve capacity, identify the pool depth exactly and preserve immutable IDs/hashes.

### 4. Independence / contamination invariants

For each required counted-held-out cell, fail the freeze if any of the following occur:

- case-ID overlap with calibration;
- exact record/input digest overlap with calibration;
- exact model-visible prompt/input digest overlap with calibration;
- duplicate model-visible prompt/input within held-out;
- duplicate normalized/template digest within held-out counted cases;
- generated variants that differ only by synthetic identifiers/numbers or otherwise fail the versioned independence rule.

Document the normalization/independence algorithm and version it. If semantic independence cannot be established deterministically, mark the affected records ineligible and do not count them toward the minimum 15.

### 5. Frozen identities

The v2 manifest must bind immutable/versioned identities for:

- task/input pool and per-record hashes;
- calibration/held-out split;
- structured size classifier;
- scorer/grader implementation contract;
- prompt assembly contract;
- tool protocol;
- exact model-configuration schema;
- independence/contamination checker;
- hidden-reference bundle/interface version/digest identity.

No `TBD`, floating `latest`, null required values, or mutable path-only identity may pass verification.

### 6. Readiness semantics

`counted_qualification_ready` may be `true` only when all are satisfied:

- every required family × size has >=15 independent held-out inputs;
- worker-visible counted-held-out material contains no hidden/reference answers;
- sealed grader reference contract is bound and verifiable;
- calibration/held-out contamination checks pass;
- held-out independence checks pass;
- scorer/prompt/tool/size/model-config identities are pinned;
- deterministic verifier/tests pass on the exact commit.

This means only that counted qualification **may begin** after lead freeze. It does not mean any route/cell is qualified.

### 7. Required negative tests

At minimum verify the checker rejects:

- calibration/held-out ID overlap;
- calibration/held-out input/prompt overlap;
- duplicate held-out prompt;
- duplicate normalized/template held-out input;
- visible hidden-answer field/value in counted held-out data;
- missing/mismatched hidden-reference identity/digest;
- fewer than 15 independent held-out inputs in a required cell;
- incomplete/floating identity manifest;
- mutated task-pool bytes;
- mutated scorer/prompt/tool/size/independence implementation identity.

Test fixtures may contain explicit hidden answers but must be clearly test-only and never used as live qualification evidence.

## Verification required before lead freeze

On the exact repair commit, run and report:

- the freeze generator/verifier in verify mode;
- focused task-pool tests;
- Ruff for changed Python;
- mypy for changed/affected modules when the repository configuration supports it;
- relevant broader offline tests or exact reason they are unavailable;
- GitHub CI if the branch/workflow receives a run.

The lead independently inspects branch parentage, diff ownership, manifest, hashes and actual test evidence. Worker self-report alone cannot promote the artifact.

## Explicit non-goals

This repair must NOT:

- run counted held-out qualification;
- change EVAL-131 statistical thresholds after seeing results;
- claim any model/cell qualified;
- expose hidden answers to workers;
- call paid providers or add spend;
- merge to integration/main;
- modify Session-A-owned shared API/store/schema/CLI/migration/lockfile files merely for convenience.

Successful completion moves `ART-V13-TASK-POOL` at most to `reviewable`; independent lead freeze is still required before W-131B counted qualification begins.
