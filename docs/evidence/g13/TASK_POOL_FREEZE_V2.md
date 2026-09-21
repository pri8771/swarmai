# ART-V13-TASK-POOL — `g13-pool-freeze-v2` held-out corpus (packet EXT-WORKER-PC-V2B-001-R2)

**Requested transition:** `drafting -> reviewable`
**Accepted:** **no** — lead review requested, not granted
**qualification_claimed:** **false** · **counted held-out runs in this packet:** **0**
**W-131B counted qualification:** **not run**
**Base:** `worker/swarmai-v13-task-pool-freeze-02` @ `bbe41b7770123fef4eb03c4f03f95fc18eefc692`
**Branch:** `worker/swarmai-v13-task-pool-freeze-04` — **uncommitted working tree**, no commit SHA (writing git was denied; see *Verification status*)

This packet builds a **new versioned held-out corpus**, `g13-pool-freeze-v2`. It
does not amend v1. `benchmarks/g13/pool_freeze_v1/` and
`docs/evidence/g13/TASK_POOL_FREEZE.md` are byte-for-byte unchanged and remain
the record of what retry-02 did and did not verify.

## What v2 changes, and why

| v1 blocker | v2 answer |
|---|---|
| **B1** — 5 held-out records per required cell against a protocol minimum of 15 | 240 held-out inputs: **15 independent inputs in every one of the 16 required cells** |
| **B2** — `expected_output`, `grader`, `reference_solution`, `broken_code` in plaintext on the worker-visible branch | a v2 record is **input-only**. There is no field in which an answer, grader fixture, rubric or reference could sit; a record carries only an opaque `hidden_reference_id` |
| **B3** — seed-isomorphic held-out variants *reported* but tolerated | `g13-independence-checker-v2` is **fail-closed on all eight axes**; a normalised-template collision is a violation, not a statistic |
| **B4** — `wilson_lower_bound` defaults to `z = 1.96` | recorded again in `identity_scorer_v2.json`. **No threshold or default was changed by this packet**; counted runs must pass the one-sided 90 % `z = 1.2815515655446004` explicitly |
| **B5** — no LICENSE file at the frozen commit | recorded again in `source_and_license.license_blocker`; it affects redistribution, not contamination or immutability |

## What is frozen

| Frozen thing | Identity | Where |
|---|---|---|
| Pool | `g13-pool-freeze-v2`, 16 shards, 240 records | `identity_pool_v2.json` |
| Records | `g13-records-v2`, input-only, closed key allowlist | `identity_records_v2.json` |
| Split | `g13-split-v2`, holdout-only, membership = the shard table | `identity_split_v2.json` + `CORPUS_SHARD_DIGESTS.txt` |
| Structured size classifier | `g13-size-classifier-v2`, 5 derived features, global bands | `identity_size_classifier_v2.json` + `src/swarm/evals/g13_size_classifier_v2.py` |
| Scorer / grader contract | `g13-scorer-v2`, pins `graders.py`, `sandbox_runner.py`, `wilson.py` | `identity_scorer_v2.json` |
| Prompt / model-visible surface | `g13-prompt-v2`, refuse-not-sanitise | `identity_prompt_v2.json` + `src/swarm/evals/g13_prompt_v2.py` |
| Tool protocol | `g13-tool-protocol-v2-no-model-visible-tools` | `identity_tool_protocol_v2.json` |
| Exact model config schema | `g13-exact-model-config-v2` (JSON Schema, 14 required fields, no nullable field) | `identity_model_config_schema_v2.json` |
| Independence checker | `g13-independence-checker-v2`, fail-closed | `identity_independence_checker_v2.json` + `src/swarm/evals/g13_independence.py` |
| Sealed reference interface | `g13-sealed-reference-interface-v2` | `identity_sealed_reference_v2.json` + `src/swarm/evals/g13_sealed_reference.py` |
| Cover digest | every file above, recursively | `SHA256SUMS` |

Every identity is pinned by a spec-file sha256 **and**, where it has one, by the
sha256 of its implementation module. Nothing is floating: the verifier rejects
`null`, an empty container, and any placeholder string (`tbd`, `todo`, `unknown`,
`none`, `n/a`, `fixme`, …) anywhere in the manifest or any identity spec.

### Corpus identity

```
corpus.shard_table.sha256 = d9d0c074eb303db5ae243bfce1b2b1d707181a4e0d578d25b6bc66f215bbf6c6
sealed_reference.id_commitment.sha256 = 43220642751fc1bd025c65b59d56e27297b5691d8d29e84c24b3402081677727
```

The shard table byte-pins all 16 shards; the manifest pins the shard table; the
manifest is pinned by `SHA256SUMS`. Per-record digests are therefore **not**
stored — every record's bytes are already pinned exactly, and the verifier
recomputes record, payload, prompt and normalised-template digests at
verification time, which is where the contamination decisions are actually made.

## Coverage — 15 independent inputs in every required cell

| product family | dataset family | S | M | L | XL |
|---|---|---|---|---|---|
| coding | `code_generation` | 15 | 15 | 15 | 15 |
| extraction | `extraction` | 15 | 15 | 15 | 15 |
| planning | `dependency_planning` | 15 | 15 | 15 | 15 |
| reasoning | `evidence_qa` | 15 | 15 | 15 | 15 |

**16 required cells × 15 = 240 held-out inputs.** No auxiliary family is folded
into a required cell: merging several task types into one qualification cell
lets a strong sub-type mask a weak one.

### How the fifteen inputs in a cell are made independent

Two independent axes vary at once inside every cell:

* **5 task variants** per required family — different instruction, different
  question, different `output_contract.fields`. For coding: pure transform, lazy
  iterator, record parser, stateful accumulator, typed error contract. For
  planning: topological order, critical path, parallel waves, blocked set,
  prerequisite closure. And so on.
* **3 distinct structural loads** per variant, so payload arity differs too.

5 × 3 = 15. Two inputs in the same cell therefore differ in both wording and
payload arity; neither is a re-skin of the other. Across cells the structural
loads are disjoint by band (S 6–8, M 11–13, L 17–19, XL 24–26), so no cross-cell
pair can collide either.

## Sealed grader-reference interface

A v2 record exposes exactly two hidden-reference fields, and the allowlist is
closed, so nothing else can ride along:

```json
"hidden_reference": {
  "interface_id": "g13-sealed-reference-interface-v2",
  "hidden_reference_id": "g13hr2-0001"
}
```

`hidden_reference_id` is an **opaque surrogate key**: a bare index into the
sealed bundle's own ordering. It is not derived from the reference content and
reveals nothing about it — not its value, not its length, not its shape, not a
digest of it, not whether two cases share a reference.

**Identity without content.** `SEALED_REFERENCE_IDS.txt` commits all 240
`<case_id> <hidden_reference_id>` rows. That file is worker-visible and
answer-free, and its sha256 is the **commitment digest**. A sealed bundle is
accepted only if it quotes the same commitment digest, which binds the external
references to exactly this corpus and this split without revealing anything.

**The bundle's own content digest is deliberately not declared here.** The
bundle is not authored on this branch and must not be, so a content digest
quoted here would be fabricated. The manifest records
`content_digest_binding.declared_here = false` with the reason, which is an
explicit boolean, not an unfilled slot.

**Fail-closed behaviour on this branch.** `resolve()` has no default source and
no local fallback path. On this branch there is no bundle, so every call raises
`SealedReferenceUnavailable`. Even given a source it refuses unless the bundle
id matches *and* an expected commitment digest is supplied *and* it matches.
Tests assert all four refusals and the one success path.

## Independence / contamination boundary — fail-closed

`g13-independence-checker-v2` rejects, as hard failures:

Inside the held-out partition:

1. `holdout_case_id_duplicate`
2. `holdout_payload_digest_duplicate` — identical model-visible input
3. `holdout_prompt_digest_duplicate` — identical rendered prompt
4. `holdout_template_duplicate` — **seed-isomorphic siblings**

Between the held-out partition and **every** foreign partition:

5. `cross_partition_case_id_overlap`
6. `cross_partition_payload_digest_overlap`
7. `cross_partition_prompt_digest_overlap`
8. `cross_partition_template_isomorph`

The declared foreign corpus is the **entire v1 pool, both splits**
(`benchmarks/starter.jsonl` @ `573bad7f…be78`, 224 records). Its calibration
split is the screening split; its held-out split is *burned*, because its
reference answers were worker-visible in plaintext. A split that was ever
readable cannot be reused, so v2 treats it as contaminating rather than as a
sibling held-out set.

**Normalisation.** A prompt is reduced to its structure by erasing what a seeded
generator varies for free: runs of two or more capitals with optional
`-`/`_`-joined groups (`EV-3`, `ORD-310-001`, `ING`) become `@`, digit runs
become `#`, and the remainder is lower-cased. The normalisation is deliberately
aggressive: a false collision fails the freeze, which is recoverable; a missed
collision silently inflates a qualification bound, which is not.

## Structured size classifier

`g13-size-classifier-v2` **derives** its features from the model-visible payload
instead of reading a number the record declares about itself:

```
structural_load = entity_count + constraint_count + 2*dependency_depth
                + output_field_count + distractor_count
S <= 8   M <= 14   L <= 21   XL > 21
```

v1 bucketed on `size_features.input_tokens_estimate`, a generator-declared
number: nothing stopped a record from declaring a token estimate that did not
describe its own payload, and the classifier could not tell. v2 removes the
declaration entirely — v2 records carry **no** `size_features` block — so a
record cannot misdescribe its own size. `dependency_depth` carries weight 2
because one more level of a dependency chain costs more reasoning than one more
flat entity; a dependency cycle is a hard failure, not a measurable graph.

Bands are **global**, not per family. v1 needed per-family bounds because its
decision feature's scale differed wildly between families; `structural_load` is
measured in comparable units — countable payload elements — so one table works.

## `counted_qualification_ready` is computed, not asserted

The verifier computes

```
counted_qualification_ready == (freeze_conditions_pass and sealed_bundle_content_digest_bound)
```

and fails the freeze if the manifest's declared value disagrees. The declaration
therefore cannot drift into an unearned claim.

It is currently **false**, blocked on
`sealed_reference_bundle_content_digest_not_bound`: the freeze conditions are
mechanical and self-contained, but the sealed bundle is minted outside this
branch and its content digest is not yet bound, so no held-out response can be
scored.

**`counted_qualification_ready` is a statement about the freeze, never about a
model.** It says nothing about whether any model, cell or capability profile is
qualified.

## Negative tests

`tests/evals/test_task_pool_freeze_v2.py` builds a complete synthetic freeze
under `tmp_path` and breaks it one way at a time. Each of these must produce the
named violation code:

| Broken this way | Expected code |
|---|---|
| answer committed onto a record | `visible_answer_leak` + `visible_payload_refused` |
| grader fixture nested inside `input` | `visible_answer_leak` |
| 14 inputs in a required cell | `required_cell_below_minimum`, `corpus_below_minimum_total` |
| a required cell removed entirely | `required_cell_below_minimum` |
| case id shared with a foreign corpus | `cross_partition_case_id_overlap` |
| model-visible input shared with a foreign corpus | `cross_partition_payload_digest_overlap` |
| rendered prompt shared with a foreign corpus | `cross_partition_prompt_digest_overlap` |
| seed-isomorphic sibling of a foreign record | `cross_partition_template_isomorph` |
| two held-out records isomorphic to each other | `holdout_template_duplicate` |
| two held-out records with an identical prompt | `holdout_payload_digest_duplicate`, `holdout_prompt_digest_duplicate` |
| `hidden_reference` block deleted | `hidden_reference_identity_invalid`, `commitment_case_not_in_corpus` |
| `hidden_reference_id` changed | `hidden_reference_id_mismatch` |
| two records sharing one `hidden_reference_id` | `hidden_reference_id_duplicate` |
| commitment digest tampered | `sealed_reference_commitment_digest_mismatch` |
| commitment entry count wrong | `sealed_reference_entry_count_mismatch` |
| reference bundle declared inside the branch | `sealed_reference_bundle_inside_branch` |
| bundle claims a digest it does not declare | `sealed_reference_bundle_digest_absent` |
| one byte of a shard changed | `shard_digest_mismatch` |
| shard table edited | `shard_table_digest_mismatch`, `shard_record_count_mismatch` |
| undeclared shard added on disk | `shard_not_in_table` |
| file not covered by `SHA256SUMS` | `checksum_uncovered_file` |
| an identity block missing | `identity_missing` |
| a placeholder value in the manifest | `floating_manifest_value` |
| an empty container in the manifest | `floating_manifest_value` |
| a placeholder value in an identity spec | `floating_identity_value` |
| an identity spec digest drifted | `identity_spec_digest_mismatch` |
| an identity id disagreeing with its module | `identity_id_code_mismatch` |
| `counted_qualification_ready = true` claimed | `readiness_declaration_mismatch` |
| a size band the classifier does not derive | `size_classifier_disagreement` |

## Verification status — read this before accepting

The worker environment for this packet **denied execution** of `python` (beyond
`python --version`), `pytest`, `ruff`, `mypy`, and **every writing git command**
(`git add`, `git commit`, `git fetch`, `git push`). Read-only git, file tools,
PowerShell `ConvertFrom-Json` and a coreutils subset (`head`, `tail`, `wc`,
`grep`, `sort`, `uniq`, `od`, `sha256sum`) were permitted.

**Not committed.** The artifact exists in the **working tree** of
`worker/swarmai-v13-task-pool-freeze-04` only. There is no commit and no pushed
branch, so **there is no commit SHA to quote**; the branch ref is at the
unchanged base `bbe41b7770123fef4eb03c4f03f95fc18eefc692`. This is the same
environment restriction retry-02 hit, recorded again rather than worked around.

**Actually executed, and what it showed:**

| Check | Command | Result |
|---|---|---|
| cover digest over all 29 frozen files | `sha256sum -c --strict SHA256SUMS` | **29/29 OK** |
| corpus size | `wc -l holdout/*.jsonl` | 16 shards × 15 = **240** |
| answer-key leakage over the whole corpus | `grep -E '"(answer\|expected_output\|grader\|reference_solution\|rubric\|solution\|label\|…)"\s*:'` | **0 matches** |
| hidden-reference id uniqueness | `grep -o 'g13hr2-[0-9]{4}' \| sort -u \| wc -l` | **240 distinct**, `uniq -d` empty |
| case id uniqueness | `grep -o '"id":"g13v2_…"' \| sort \| uniq -d` | **empty** |
| id-commitment size | `wc -l SEALED_REFERENCE_IDS.txt` | 4 header + **240** rows |
| per-shard item totals | `grep -o … \| wc -l` per shard | matched the declared structural loads exactly, all 16 shards |
| constraint / distractor / output-field arity | `grep -c` on exact-arity regexes | 240/240 records matched the declared shape |
| **per-record** item count inside its band | lowest- and first-out-of-band item ref present/absent per shard | all 16 shards band-consistent (see below) |
| planning graph depth | sink-has-no-outgoing-edge and full-chain greps | depth 1 / 2 / 3 / 5 confirmed for S / M / L / XL |
| JSON well-formedness | `ConvertFrom-Json` over every record and every spec | **240/240** records, **10/10** identity specs, manifest |
| line endings | `tail -c 24 … \| od -c` | LF, single trailing LF |

A shard total alone cannot rule out a compensating miscount (one record +1, another
−1). Because a record's item refs are contiguous from 1, the presence of the
lowest in-band ref in all 15 records and the absence of the first out-of-band ref
pins every record's item count into the band:

| shard | band admits | lowest ref present in all 15 | first out-of-band ref | result |
|---|---|---|---|---|
| `coding_S` | items <= 4 | — | `RQ-5` absent | ✓ |
| `coding_M` | 3..8 | `RQ-3` 15/15 | `RQ-9` absent | ✓ |
| `coding_L` | 7..13 | `RQ-7` 15/15 | `RQ-14` absent | ✓ |
| `coding_XL` | >= 12 | `RQ-12` 15/15 | — | ✓ |
| `extraction_S` | items <= 4 | — | `-105` absent | ✓ |
| `extraction_M` | 3..8 | `-103` 15/15 | `-109` absent | ✓ |
| `extraction_L` | 7..13 | `-107` 15/15 | `-114` absent | ✓ |
| `extraction_XL` | >= 12 | `-112` 15/15 | — | ✓ |
| `reasoning_S` | items <= 4 | — | `EV-5` absent | ✓ |
| `reasoning_M` | 3..8 | `EV-3` 15/15 | `EV-9` absent | ✓ |
| `reasoning_L` | 7..13 | `EV-7` 15/15 | `EV-14` absent | ✓ |
| `reasoning_XL` | >= 12 | `EV-12` 15/15 | — | ✓ |
| `planning_S` | items <= 4 | — | `IDX` absent | ✓ |
| `planning_M` | 3..6 | `VAL` 15/15 | `ARC` absent | ✓ |
| `planning_L` | 4..10 | `ENR` 15/15 | `AUD` absent | ✓ |
| `planning_XL` | >= 6 | `PUB` 15/15 | — | ✓ |

This proves the size classifier will agree with all 240 declared bands. It does
**not** prove the classifier code computes what this table assumes — that still
needs `python`.

**Not executed — the lead must run all four:**

```sh
python scripts/g13_freeze_task_pool_v2.py --verify --stats
python -m pytest tests/evals/test_task_pool_freeze_v2.py -q
ruff check src/swarm/evals/g13_*.py src/swarm/evals/task_pool_freeze_v2.py \
           scripts/g13_freeze_task_pool_v2.py tests/evals/test_task_pool_freeze_v2.py
mypy src/swarm/evals/g13_size_classifier_v2.py src/swarm/evals/g13_prompt_v2.py \
     src/swarm/evals/g13_sealed_reference.py src/swarm/evals/g13_independence.py \
     src/swarm/evals/task_pool_freeze_v2.py
```

**The new Python is unexecuted.** The corpus arity, digests, uniqueness and
leakage counts above were established with coreutils, but nothing has run
`derive_features`, `render_prompt`, `normalise_template` or
`verify_pool_freeze_v2` against the committed bytes. If any of them disagrees
with this document, the code wins and this freeze needs a correction.

**Not read:** `origin/coordination/swarm-control` could not be fetched, so
`EXT-WORKER-PC-V2B-001-R2.md`, `EVAL_131_QUALIFICATION_PROTOCOL.md`,
`ARTIFACT_MANAGEMENT.md`, `ARTIFACT_REGISTRY.json`, `WORK_QUEUE.md` and
`AGENT_MESSAGES.md` were unavailable. The protocol constants used here
(families, sizes, `n >= 15`, max 60, one-sided 90 % Wilson >= 0.80, >= 3 exact
model configs) were taken from `docs/evidence/g13/QUALIFICATION_CRITERION.md`.
**If the coordination branch says otherwise, the coordination branch wins.**

## Scope discipline

Files touched by this packet live only in benchmark, evaluation, evidence and
test paths. **No** Session-A-owned API, store, route, schema, CLI, database
migration, `pyproject.toml` or lockfile was edited. No `swarm/api`, `swarm/db`,
`swarm/cli` or `migrations` path was opened for writing.

## Claims / not claimed

| Claimed | Not claimed |
|---|---|
| A new versioned held-out corpus, `g13-pool-freeze-v2`, with 240 input-only records | That ART-V13-TASK-POOL is accepted |
| 15 independent held-out inputs in every required coding/planning/reasoning/extraction × S/M/L/XL cell | That counted qualification may start |
| Zero answer, grader, reference, rubric or solution fields anywhere in the corpus | That any cell is qualified |
| A sealed grader-reference interface exposing only an opaque id plus version identity, fail-closed on this branch | That the sealed reference bundle exists |
| A fail-closed, versioned independence checker covering all eight overlap axes | That the v2 verifier, generator or tests were executed here |
| Ten pinned, non-floating identities | Any threshold, default or protocol constant change |
| A readiness value the verifier computes and refuses to let the manifest overstate | That `counted_qualification_ready` says anything about a model |
| v1 preserved unchanged as historical incomplete evidence | That v1 is usable for counted qualification |
| Digest, arity, uniqueness, JSON and band checks actually run with coreutils and `ConvertFrom-Json` | That the branch was committed or pushed — writing git was denied, so no commit SHA exists |
