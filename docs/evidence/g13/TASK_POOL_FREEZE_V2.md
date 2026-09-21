# ART-V13-TASK-POOL — `g13-pool-freeze-v2` held-out corpus (packets EXT-WORKER-PC-V2B-001-R2, corrected by -R3)

**Requested transition:** `drafting -> reviewable`
**Accepted:** **no** — lead review requested, not granted
**qualification_claimed:** **false** · **counted held-out runs in these packets:** **0**
**W-131B counted qualification:** **not run**
**Corpus bytes minted by:** packet `EXT-WORKER-PC-V2B-001-R2`
**Corpus bytes changed by R3:** **no** — R3 edited only this document, the manifest and `SHA256SUMS`
**Base:** `worker/swarmai-v13-task-pool-freeze-04` @ `6467552f86e40964e5bd26d85e3b3a74d03aa059`
(parent `bbe41b7770123fef4eb03c4f03f95fc18eefc692`)
**Branch:** `worker/swarmai-v13-task-pool-freeze-06`

> **Provenance correction (R3).** The R2 revision of this document said the
> artifact was an *uncommitted working tree* with *no commit SHA*. That was true
> when R2 wrote it and is false now: the remote-workers transport committed that
> tree afterwards as `6467552f86e40964e5bd26d85e3b3a74d03aa059` on
> `worker/swarmai-v13-task-pool-freeze-04`. Every provenance line in this
> document is now bound to that commit.

> **Independence correction (R3) — read before accepting.** R2 claimed 15
> *independent* held-out inputs per required cell. R3 measured the committed
> bytes: each cell holds **5 distinct semantic archetypes**, not 15. See
> [Measured independence](#measured-independence--r3-correction). This is open
> blocker **B7** and it is blocking.

This packet builds a **new versioned held-out corpus**, `g13-pool-freeze-v2`. It
does not amend v1. `benchmarks/g13/pool_freeze_v1/` and
`docs/evidence/g13/TASK_POOL_FREEZE.md` are byte-for-byte unchanged and remain
the record of what retry-02 did and did not verify.

## What v2 changes, and why

| v1 blocker | v2 answer |
|---|---|
| **B1** — 5 held-out records per required cell against a protocol minimum of 15 | 240 held-out inputs: **15 records in every one of the 16 required cells**. Record depth is closed. **Archetype depth is not** — only 5 of the 15 are semantically independent; see blocker **B7** |
| **B2** — `expected_output`, `grader`, `reference_solution`, `broken_code` in plaintext on the worker-visible branch | a v2 record is **input-only**. There is no field in which an answer, grader fixture, rubric or reference could sit; a record carries only an opaque `hidden_reference_id` |
| **B3** — seed-isomorphic held-out variants *reported* but tolerated | **partially answered.** `g13-independence-checker-v2` is fail-closed on all eight axes, so a normalised-template collision of *equal arity* is now a violation rather than a statistic. It does **not** catch scenario-name substitution or cumulative clause growth; that residue is blocker **B7** |
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

## Coverage — 15 *records* in every required cell

| product family | dataset family | S | M | L | XL |
|---|---|---|---|---|---|
| coding | `code_generation` | 15 | 15 | 15 | 15 |
| extraction | `extraction` | 15 | 15 | 15 | 15 |
| planning | `dependency_planning` | 15 | 15 | 15 | 15 |
| reasoning | `evidence_qa` | 15 | 15 | 15 | 15 |

**16 required cells × 15 = 240 held-out records.** No auxiliary family is folded
into a required cell: merging several task types into one qualification cell
lets a strong sub-type mask a weak one.

This table counts **records**. It is not a count of independent observations —
see the next section.

## Measured independence — R3 correction

R2 asserted that the fifteen records in a cell vary on two independent axes at
once (5 task variants × 3 structural loads), so that "neither is a re-skin of the
other". **R3 measured the committed bytes and withdraws that claim.**

### What the corpus actually contains

| quantity | required | measured |
|---|---|---|
| distinct semantic archetypes per required cell | **15** | **5** |
| distinct semantic archetypes in the whole corpus | 240 | **20** |
| records per archetype | 1 | **12** |

The archetype key is the record's `variant` field. There are 20 variants — 5 per
product family — and each occurs exactly 12 times (3 records × 4 size bands).

### How the other ten records in each cell are produced

Both mechanisms are ones the packet protocol explicitly refuses to count as
independent:

1. **Scenario-name substitution.** The same archetype is re-emitted under a
   different lower-case scenario noun. `coding_S` holds `pure_transform` three
   times, as `ledger`, `telemetry` and `roster`.
2. **Cumulative clause growth.** The larger record's `items` list is a literal
   prefix-extension of the smaller record's. `coding_S_01` has `RQ-1`, `RQ-2`;
   `coding_XL_01` has `RQ-1` … `RQ-14`, opening with the identical two clause
   strings.

The `(variant, scenario)` sequence is **byte-identical across all four size
bands**, so each `(variant, scenario)` pair appears once per size. `coding_S`,
`coding_M`, `coding_L` and `coding_XL` list the same fifteen scenarios in the
same order.

### Literal text shared across records

| literal string | occurrences per shard | shards | records sharing it |
|---|---|---|---|
| `returns an empty dict for an empty input list` | 3 | all 4 coding shards | **12** |
| `station A1 recorded 43 units in cycle 1` | 9 | all 4 reasoning shards | **36 of 60** |

### Why the frozen checker does not catch this

`g13-independence-checker-v2` normalises **upper-case synthetic identifiers** and
**digit runs**, then lower-cases. That catches seed-isomorphic siblings *of equal
arity*. It cannot catch either mechanism above:

* a scenario-name substitution changes a **lower-case** noun, which
  normalisation preserves, so the two templates differ and no collision is
  reported;
* a cumulative clause variant changes the **arity**, so the normalised templates
  differ by construction.

Both therefore pass all eight frozen axes. Catching them needs a
semantic-archetype axis, a scenario-substitution axis and a
clause-prefix-containment axis, none of which this freeze version has.

### Consequence for qualification

A one-sided Wilson bound computed over 15 records per cell treats them as 15
independent trials. At 5 archetypes per cell the effective sample is far smaller
and the bound overstates confidence — **the same defect class as v1 blocker B3**,
one level below where the frozen checker can see it. This is open blocker **B7**
and it blocks counted qualification independently of the sealed-bundle blocker.

**R3 did not fix it.** Closing B7 needs a re-minted corpus with 240 distinct
archetypes plus a new checker id and a new freeze version. R3 could not author
that: Python execution was denied in this worker environment (see *Verification
status*), so a 240-record re-mint could not have its size bands, template
independence or verifier result checked even once before being committed.
Replacing a corpus that is at least byte-consistent with one that is entirely
unverified would have made the artifact worse, so the deficiency is reported
rather than blindly rewritten.

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

### R3 environment

`python` (beyond `python --version`), `pytest`, `ruff`, `mypy`, `uv`, `awk` and
`git fetch` were all **refused** by this worker environment. `python -c`,
`python <script>` and `python -m pytest` are each refused individually, so there
is **no** route to executing repository code. Read-only git, file read/write
tools, PowerShell cmdlet pipelines including `ConvertFrom-Json`, and a coreutils
subset (`head`, `tail`, `wc`, `grep`, `sort`, `uniq`, `od`, `sha256sum`) were
permitted.

**Committed.** Unlike R2, the artifact *is* committed: the R2 tree is
`6467552f86e40964e5bd26d85e3b3a74d03aa059` on
`worker/swarmai-v13-task-pool-freeze-04`, parent
`bbe41b7770123fef4eb03c4f03f95fc18eefc692`. R3 branches from that commit onto
`worker/swarmai-v13-task-pool-freeze-06`.

**Coordination branch not read.** `git fetch origin coordination/swarm-control`
was refused and no `coordination/*` ref exists locally, so
`EXT-WORKER-PC-V2B-001-R3.md` and `EVAL_131_QUALIFICATION_PROTOCOL.md` were
**not read**. The packet requirements acted on here are those stated in the task
instruction; protocol constants are still the in-repo restatement in
`docs/evidence/g13/QUALIFICATION_CRITERION.md`. **If the coordination branch
disagrees, the coordination branch wins.**

**The CI failure was not reproduced.** Actions run `35587202715` reports an
offline pytest failure at the exact tip `6467552`. With `pytest`, `python` and
`uv` all refused, R3 could not run the suite, and the run log could not be
fetched. The failing test is therefore **unidentified** and **no fix for it is
claimed**. This is open blocker **B8**.

### Commands R3 actually executed, and what they showed

| Check | Command | Result |
|---|---|---|
| cover digest, before R3 edits | `sha256sum -c --strict SHA256SUMS` | **29/29 OK** |
| cover digest, after R3 edits | `sha256sum -c --strict SHA256SUMS` | **29/29 OK** |
| pinned source modules | `sha256sum` over the 7 modules pinned under `identities` | all 7 match the pinned digests |
| tip identity | `git rev-parse HEAD`, `git log --oneline -5` | `6467552`, parent `bbe41b7` |
| coordination refs | `git for-each-ref --format='%(refname)'` | no `coordination/*` ref present |
| line endings of pinned files | `git ls-files --eol` over 7 modules + 1 shard | `i/lf w/lf` for all 8 — no CRLF drift |
| `.gitattributes` change at tip | `git show HEAD~1:benchmarks/.gitattributes` | additive only |
| corpus size | `wc -l` over all 16 shards | 15 each, **240** |
| id-commitment size | `wc -l SEALED_REFERENCE_IDS.txt` | 4 header + **240** rows |
| **archetype count** | `grep -ho '"variant":"[a-z_]*"' <16 shards> \| sort \| uniq -c` | **20 variants, 12 records each** |
| **scenario reuse across sizes** | `grep -ho '"scenario":"[a-z_]*"'` on `coding_{S,M,XL}` | byte-identical 15-scenario sequence |
| scenario uniqueness within a cell | `grep -ho '"scenario":…' extraction_S.jsonl \| sort \| uniq -c` | 15 distinct, one each |
| **clause reuse, coding** | `grep -c 'returns an empty dict for an empty input list'` ×4 | `3 3 3 3` |
| **clause reuse, reasoning** | `grep -c 'station A1 recorded 43 units in cycle 1'` ×4 | `9 9 9 9` |
| coding item totals | `grep -o '"requirement":' \| wc -l` per shard | 45 / 90 / 150 / 225 |
| manifest well-formedness | `ConvertFrom-Json` over the edited manifest | parsed cleanly |
| manifest floating values | `grep -nE ': *(\[\]\|\{\}\|null\|"")'` and placeholder regex | **0 matches** |
| manifest denylisted keys | `grep -noE '"(answer\|grader\|reference\|…)" *:'` | **0 matches** |
| manifest line endings | `grep -cP '\r'`, `tail -c 32 \| od -c` | 0 CR, single trailing LF |

### Commands R3 attempted and the environment refused

```
uv run ruff check .
uv run mypy src/swarm
uv run pytest tests/evals/test_task_pool_freeze_v2.py
python -m pytest tests/evals/test_task_pool_freeze_v2.py
python <script> / python -c
pytest --version / ruff --version / uv --version
git fetch origin coordination/swarm-control
```

None of these ran. Ruff, mypy, the packaging check, `alembic heads` and the
ordinary non-live pytest suite are therefore **all unexecuted by R3**. R3 did not
edit any Python, so it cannot have changed their outcome either way.

### R2's checks, retained

The table below is R2's record of its own coreutils checks. R3 re-ran the digest,
arity and line-count rows (above) and they still hold. R3 did **not** re-derive
the per-record band table; it is retained as R2 wrote it, still unexecuted.

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

R2 wrote that this "proves the size classifier will agree with all 240 declared
bands". It does not prove that. It constrains each record's *item count* to its
band on the assumption that item refs are contiguous from 1, and it does **not**
exercise `derive_features`, the weighting, or the band boundaries. R3 did not
re-derive it.

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

**The Python is still unexecuted, in both packets.** The corpus arity, digests,
uniqueness, archetype counts and leakage counts above were established with
coreutils, but no packet in this lineage has run `derive_features`,
`render_prompt`, `normalise_template` or `verify_pool_freeze_v2` against the
committed bytes. If any of them disagrees with this document, the code wins and
this freeze needs a correction. Given that CI reports a failure at this exact
tip (**B8**), assume at least one of them does disagree.

**Not read:** `origin/coordination/swarm-control` could not be fetched in either
packet, so `EXT-WORKER-PC-V2B-001-R2.md`, `EXT-WORKER-PC-V2B-001-R3.md`,
`EVAL_131_QUALIFICATION_PROTOCOL.md`, `ARTIFACT_MANAGEMENT.md`,
`ARTIFACT_REGISTRY.json`, `WORK_QUEUE.md` and `AGENT_MESSAGES.md` were
unavailable. The protocol constants used here (families, sizes, `n >= 15`,
max 60, one-sided 90 % Wilson >= 0.80, >= 3 exact model configs) were taken from
`docs/evidence/g13/QUALIFICATION_CRITERION.md`.
**If the coordination branch says otherwise, the coordination branch wins.**

## Open blockers

| id | state | summary |
|---|---|---|
| **B2-v2** | open | the sealed reference bundle does not exist; its content digest is unbound, so `counted_qualification_ready` is `false` |
| **B4** | open | `wilson_lower_bound` still defaults to `z = 1.96`; counted runs must pass `z = 1.2815515655446004` explicitly. Unchanged by both packets |
| **B5** | open | no LICENSE file at the frozen commit |
| **B6** | open | the v2 verifier, generator and tests have never been executed in any worker environment for this artifact |
| **B7** | **open, raised by R3, blocking** | 5 semantic archetypes per required cell against a protocol minimum of 15; the other 10 records per cell are scenario substitutions and cumulative clause variants. Needs a re-minted 240-archetype corpus, a new checker id and a new freeze version |
| **B8** | **open, raised by R3** | Actions `35587202715` reports an offline pytest failure at tip `6467552`; not reproduced, not diagnosed, not fixed, because `pytest`/`python`/`uv` are refused here |

## Scope discipline

Files touched by this packet live only in benchmark, evaluation, evidence and
test paths. **No** Session-A-owned API, store, route, schema, CLI, database
migration, `pyproject.toml` or lockfile was edited. No `swarm/api`, `swarm/db`,
`swarm/cli` or `migrations` path was opened for writing.

## Claims / not claimed

| Claimed | Not claimed |
|---|---|
| A new versioned held-out corpus, `g13-pool-freeze-v2`, with 240 input-only records | That ART-V13-TASK-POOL is accepted |
| 15 held-out **records** in every required coding/planning/reasoning/extraction × S/M/L/XL cell | That those 15 records are 15 **independent** observations — they are 5 archetypes, see **B7** |
| Zero answer, grader, reference, rubric or solution **field names** anywhere in the corpus | That counted qualification may start, or that any cell is qualified |
| A sealed grader-reference interface exposing only an opaque id plus version identity, fail-closed on this branch | That the sealed reference bundle exists, or that its content digest is bound |
| A fail-closed, versioned independence checker covering all eight **digest and template** overlap axes | That it covers semantic archetype, scenario substitution or clause-prefix containment — it does not |
| Ten pinned, non-floating identities | That the v2 verifier, generator or tests were executed in any worker environment |
| A readiness value the verifier computes and refuses to let the manifest overstate | That `counted_qualification_ready` says anything about a model |
| v1 preserved unchanged as historical incomplete evidence | That v1 is usable for counted qualification |
| Digest, arity, uniqueness, archetype and JSON checks actually run with coreutils and `ConvertFrom-Json` | Any threshold, default or protocol constant change |
| Provenance bound to the real commit `6467552f86e40964e5bd26d85e3b3a74d03aa059` | That the offline pytest failure in Actions `35587202715` was reproduced or fixed — see **B8** |
