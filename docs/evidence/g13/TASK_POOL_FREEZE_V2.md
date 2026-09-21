# ART-V13-TASK-POOL — `g13-pool-freeze-v2` held-out corpus (packets EXT-WORKER-PC-V2B-001-R2, corrected by -R3, repaired by -R4)

**Requested transition:** `drafting -> reviewable`
**Accepted:** **no** — lead review requested, not granted
**qualification_claimed:** **false** · **counted held-out runs in these packets:** **0**
**W-131B counted qualification:** **not run, not started**
**Corpus bytes minted by:** packet `EXT-WORKER-PC-V2B-001-R4` (all 240 records re-authored)
**Base:** `worker/swarmai-v13-task-pool-freeze-06` @ `f7800332594d67c8b872b3597abd59f35987a2a0`
(parent `6467552f86e40964e5bd26d85e3b3a74d03aa059`)
**Branch:** `worker/swarmai-v13-task-pool-freeze-07`

> **R4 repair notice — read this first.** Retry 06 was independently rejected on
> two grounds. Both are addressed here.
>
> 1. **Archetype depth.** R3 measured 5 distinct semantic archetypes per
>    required cell against a protocol minimum of 15. **All 240 records have been
>    re-authored** as 240 distinct archetypes, 15 in every cell, and a new
>    fail-closed axis — `g13-semantic-group-axis-v1` — now *enforces* that depth
>    instead of merely asserting it. The old [Measured
>    independence](#measured-independence--r3-correction) section is retained
>    **verbatim as history**: it describes a corpus that no longer exists.
> 2. **Red CI.** The offline pytest failure at the exact tip is identified and
>    fixed. See [The offline pytest failure](#the-offline-pytest-failure--r4).
>
> What R4 did **not** do: it did not touch `g13-independence-checker-v2`, did
> not relax any existing invariant, did not delete, skip, xfail or loosen any
> task-pool assertion, did not change `counted_qualification_ready` (still
> `false`), and did not start W-131B.

> **Execution notice.** No repository Python was executed in the R4 worker
> session: `python`, `pytest`, `ruff`, `mypy`, `uv` and `node <script>` are all
> refused by that environment, and so are `sed`, `awk`, shell redirection,
> process substitution and PowerShell script blocks. Everything below that
> concerns *bytes* was checked with `grep`, `sort`, `uniq`, `tr`, `wc`, `od`,
> `sha256sum` and PowerShell `ConvertFrom-Json`. Everything that concerns
> *behaviour* is unexecuted here. **GitHub Actions on the transport-created
> commit is the executable verification environment; read that exact run.**

This packet builds a **new versioned held-out corpus**, `g13-pool-freeze-v2`. It
does not amend v1. `benchmarks/g13/pool_freeze_v1/` and
`docs/evidence/g13/TASK_POOL_FREEZE.md` are byte-for-byte unchanged and remain
the record of what retry-02 did and did not verify.

## What v2 changes, and why

| v1 blocker | v2 answer |
|---|---|
| **B1** — 5 held-out records per required cell against a protocol minimum of 15 | 240 held-out inputs: **15 records in every one of the 16 required cells**, and since R4 those 15 are **15 distinct semantic archetypes**, not 5 archetypes plus 10 re-skins. Record depth and archetype depth are both closed |
| **B2** — `expected_output`, `grader`, `reference_solution`, `broken_code` in plaintext on the worker-visible branch | a v2 record is **input-only**. There is no field in which an answer, grader fixture, rubric or reference could sit; a record carries only an opaque `hidden_reference_id` |
| **B3** — seed-isomorphic held-out variants *reported* but tolerated | **answered in two layers.** `g13-independence-checker-v2` is fail-closed on all eight digest and normalised-template axes, so a template collision of *equal arity* is a violation rather than a statistic. `g13-semantic-group-axis-v1` adds the axes string equality cannot see: scenario rename, numeric or seed substitution, and cumulative clause growth. What remains is blocker **B9** |
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
| Independence checker | `g13-independence-checker-v2`, fail-closed, **byte-identical to R2** | `identity_independence_checker_v2.json` + `src/swarm/evals/g13_independence.py` |
| **Semantic archetype axis** (new in R4) | `g13-semantic-group-axis-v1`, fail-closed, ≥15 groups per required cell | `identity_semantic_group_v1.json` + `src/swarm/evals/g13_semantic_group.py` |
| Sealed reference interface | `g13-sealed-reference-interface-v2` | `identity_sealed_reference_v2.json` + `src/swarm/evals/g13_sealed_reference.py` |
| Cover digest | every file above, recursively | `SHA256SUMS` |

## The semantic archetype axis — R4

`g13-independence-checker-v2` compares **strings**. Three cheap transformations
produce a string it has never seen while producing no new information:

| transformation | what the old axes see | why it is not a new observation |
|---|---|---|
| scenario / domain rename (`harbor` → `orchard`) | a different prompt **and** a different normalised template, because a lower-case noun survives normalisation | the task is identical; only a label moved |
| numeric / seed / synthetic-id substitution (`ORD-310-001` → `ORD-998-777`) | a different prompt; the normalised template **does** collapse, so v2 already catches this one | same |
| cumulative clause-only growth (append clauses to one recipe) | a different arity, so every equality-based axis sees two distinct records | one recipe, measured twice |

A Wilson bound counts observations. Fifteen re-skins of one recipe are one
observation repeated fifteen times, which is v1 blocker **B3** at a level string
equality cannot reach. The new axis closes it:

* a record is reduced to a **recipe digest** — the content tokens of `task`,
  `instruction`, `question`, `signature` and the output contract — plus one
  **clause digest** per `items`, `constraints` and `distractors` entry, tagged
  with the section it came from;
* two records are **siblings** when their recipe digests are equal *and* one
  clause-digest set is **contained in** the other. Containment rather than
  equality is what makes cumulative growth collapse;
* a semantic group is a connected component of that relation, and every
  required cell must hold **≥ 15 distinct groups**. The axis floors that
  minimum at 15 whatever the manifest declares, and rejects a manifest that
  tries to declare less (`semantic_group_minimum_below_protocol`).

**Normalisation, and why the declared `scenario` cannot inflate a count.**
Before tokenising, the axis erases synthetic identifiers and digit runs exactly
as `g13-independence-checker-v2` does, lower-cases, drops tokens shorter than
three characters, drops a frozen 44-word stopword list, and drops the
**corpus-wide union of every declared `scenario` slug** — not just the record's
own. Erasing a token can only make two records look *more* alike, so it can only
merge groups and never split them. A record whose declared scenario does not
occur in its own rendered prompt is refused outright.

The committed corpus is authored so that this is checkable by inspection: each
of the 15 scenario nouns occurs **exactly 32 times** across the corpus — once as
the `scenario` field and once inside the instruction carrier, in each of the 16
cells. A scenario noun never appears in an item, a constraint, a distractor, a
question, a signature or an output contract, so scenario erasure removes the
domain label and nothing else, and the 240 instruction tails that remain are
240 distinct strings.

**Additive, not a replacement.** `src/swarm/evals/g13_independence.py` and
`identity_independence_checker_v2.json` are byte-identical to the R2 versions
— their digests in the manifest are unchanged, which is the evidence that R4
weakened nothing. The group axis runs *after* all eight existing invariants and
can only add violations.

**Residual limitation (blocker B9).** The axis is lexical, not semantic. Two
records that share a recipe but whose clause sets merely *overlap* without
containment are counted as two groups, so an adversary willing to re-author
clauses rather than append them can still buy a group. Closing that needs a
model, not a digest. It is recorded rather than papered over.

## The offline pytest failure — R4

**Run:** GitHub Actions `35610017583` at tip
`f7800332594d67c8b872b3597abd59f35987a2a0`, and `35587202715` at
`6467552f86e40964e5bd26d85e3b3a74d03aa059` before it. R3 could not identify the
failing test because it could not run or fetch anything. R4 found it by reading.

**Failing test:** `tests/evals/test_task_pool_freeze_v2.py::test_commitment_renders_opaque_ids_only`.

**Cause.** The test asserts that the rendered hidden-reference commitment
carries no held-out-content vocabulary, and asserted specifically that the
substring `grader` does not occur in it. The frozen `COMMITMENT_HEADER` in
`src/swarm/evals/g13_sealed_reference.py` named the very words it promised to
exclude:

```
# contains opaque surrogate keys only: no reference answer, no grader fixture, no rubric, no answer digest
```

So the rendered file contained `grader`, and the assertion failed on **every**
run since the header was introduced. It is a self-inflicted wound in prose, not
a defect in the freeze logic.

**Fix.** The header now states the same promise without using any of the
forbidden words:

```
# contains opaque surrogate keys only: no held-out content of any kind, and no digest of any held-out content
```

The assertion was **strengthened**, not loosened: it now checks eleven words
rather than two, and a second test applies the same check to the committed
`SEALED_REFERENCE_IDS.txt` on disk. No task-pool assertion was deleted, skipped,
xfailed or weakened anywhere in this packet.

**Blast radius.** The commitment file's 240 rows are byte-identical — the
re-authored corpus kept every case id and every `hidden_reference_id`
assignment — so only the third header line changed. That still changes the
commitment digest, which is pinned in the manifest and which
`g13_sealed_reference.resolve` requires a sealed bundle to quote, so a bundle
minted against the old digest cannot be used by accident.

Every identity is pinned by a spec-file sha256 **and**, where it has one, by the
sha256 of its implementation module. Nothing is floating: the verifier rejects
`null`, an empty container, and any placeholder string (`tbd`, `todo`, `unknown`,
`none`, `n/a`, `fixme`, …) anywhere in the manifest or any identity spec.

## Corpus identity

```
corpus.shard_table.sha256 = cae0aecd1a04c37197de500fd3e20e42960def44e1b072c0c36939a7d8bad6e1
sealed_reference.id_commitment.sha256 = 8bc1950cf78feddace6bea7d44db3543507900528abd9aa3619043d405aa1dbb
```

Both changed in R4: the shard table because every shard was re-authored, the id
commitment because its third header line was reworded. The commitment's 240
rows are byte-identical to R2.

The shard table byte-pins all 16 shards; the manifest pins the shard table; the
manifest is pinned by `SHA256SUMS`. Per-record digests are therefore **not**
stored — every record's bytes are already pinned exactly, and the verifier
recomputes record, payload, prompt and normalised-template digests at
verification time, which is where the contamination decisions are actually made.

## Coverage — 15 records *and* 15 archetypes in every required cell

| product family | dataset family | S | M | L | XL |
|---|---|---|---|---|---|
| coding | `code_generation` | 15 / 15 | 15 / 15 | 15 / 15 | 15 / 15 |
| extraction | `extraction` | 15 / 15 | 15 / 15 | 15 / 15 | 15 / 15 |
| planning | `dependency_planning` | 15 / 15 | 15 / 15 | 15 / 15 | 15 / 15 |
| reasoning | `evidence_qa` | 15 / 15 | 15 / 15 | 15 / 15 | 15 / 15 |

Read each cell as **records / distinct semantic groups**. **16 required cells ×
15 = 240 held-out records and 240 distinct archetypes** — every record in the
corpus is its own archetype, in its own cell and across every other cell. No
auxiliary family is folded into a required cell: merging several task types into
one qualification cell lets a strong sub-type mask a weak one.

Measured on the committed bytes, without executing anything: 240 distinct
`variant` slugs, 240 distinct case ids, 240 distinct opaque hidden-reference
ids, and 240 distinct instruction tails once the scenario noun is removed.

### Structural loads actually present

| size | band rule | loads in this corpus |
|---|---|---|
| S | `structural_load ≤ 8` | 6, 7, 8 |
| M | `9 … 14` | 11, 12, 13, 14 |
| L | `15 … 21` | 16, 17, 18, 19 |
| XL | `> 21` | 22, 23, 24, 25 |

The planning family carries a dependency spine, weighted 2 per edge, so its
loads sit one to two points above the other three families in every band. The
spine is exactly `depth` edges over the first `depth + 1` steps, plus single
edges from the first step to each remaining step, so `dependency_depth` is
exactly 1, 2, 3 and 4 for S, M, L and XL.

## Measured independence — R3 correction

> **Historical. Superseded by R4; describes a corpus that no longer exists.**
> Everything in this section was true of the corpus
> committed at `6467552…` and `f780033…`. That corpus has been discarded and
> replaced: all 240 records were re-authored, and the deficiency measured below
> is what blocker **B7** recorded and what R4 closed. The section is preserved
> verbatim because the measurement itself is evidence, and because a reader must
> be able to see exactly what was wrong before deciding whether it is now right.

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

> **R4 closed B7 anyway, and here is the honest account of the risk R3 named.**
> Python execution was denied in the R4 session too, and so were `git add` and
> `git commit`, so the re-minted corpus reaches the branch the same way R2's and
> R3's did — the transport commits the working tree — and the verifier has still
> never been run against it. R4 judged that trade differently from R3 for two
> reasons. First, the packet that commissioned R4 *requires* the re-mint;
> reporting the deficiency a third time is not one of the options it offers.
> Second, the properties a blind re-mint could get wrong are exactly the ones
> that are checkable with `grep`, `sort`, `uniq`, `tr` and `wc`: per-record item
> arity (and therefore every structural load), id and reference-id uniqueness,
> scenario containment, JSON well-formedness, byte hygiene and archetype
> distinctness. All of those were checked, cell by cell, and the commands are
> listed in `provenance_commands_executed` in the manifest. What remains
> unchecked here is *behaviour* — whether the verifier agrees — and that is what
> CI on the transport commit is for.

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

**R4 added a ninth and tenth failure, on a separate axis.** These are *extra*
codes, not replacements — the eight above are unchanged and
`g13_independence.py` is byte-identical to R2:

9. `required_cell_below_minimum_semantic_groups` — the cell holds fewer than 15
   distinct semantic groups, however many records it holds
10. `semantic_group_unreducible` — a record cannot be reduced to a fingerprint
    at all (no usable id, no scenario slug, a scenario the record's own prompt
    never mentions, a missing or empty output contract, a clause section that is
    not an array, or nothing left after normalisation)

plus `semantic_group_minimum_below_protocol`, which rejects a manifest that
declares a per-cell minimum below 15.

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

### Negative tests added by R4 — the semantic archetype axis

These are the axis' own negative cases. Each builds the exact transformation the
packet protocol refuses to count as independent, **asserts that the pre-existing
axes cannot always see it**, and asserts that the group axis collapses it to one
group anyway.

| Broken this way | Assertion |
|---|---|
| scenario-name sibling: one domain noun swapped | rendered prompt **and** normalised template both differ (old axes blind), yet the pair is **one** group |
| numeric / seed / synthetic-id sibling | normalised template **collapses** (the old axis already catches it), and the group axis agrees rather than being laxer — **one** group |
| cumulative clause-only sibling: clauses appended to one recipe | normalised templates differ by construction (old axes blind), yet the pair is **one** group |
| a 15-record cell holding one archetype | `required_cell_below_minimum_semantic_groups`, cell group count `== 1`, cell **record** count still `== 15`, and `required_cell_below_minimum`, `holdout_template_duplicate`, `holdout_payload_digest_duplicate`, `holdout_prompt_digest_duplicate` are all **absent** |
| a manifest declaring a per-cell minimum of 5 | `semantic_group_minimum_below_protocol` |
| a record whose `scenario` is not a slug | `semantic_group_unreducible` + `required_cell_below_minimum_semantic_groups` |
| a `scenario` the record's own prompt never mentions | `SemanticGroupError` |
| a contaminated record reaching the axis | `SemanticGroupError` |
| a duplicate case id inside the axis | `SemanticGroupError` |
| two genuinely different archetypes | **two** groups — the positive control |

The fourth row is the case the packet names: full record depth, zero archetype
depth, and every pre-existing axis passing it. That test is the evidence that
the new axis was necessary and that it was not bought by weakening an old one.

## Verification status — read this before accepting

### R4 environment

`python` beyond `--version`, `pytest`, `ruff`, `mypy`, `uv`, **`node <script>`
beyond `--version`**, `sed`, `awk`, shell redirection to a file, shell process
substitution, PowerShell script blocks, `git fetch` **and `git add` / `git
commit`** were all **refused**. There is no route to executing repository code
and no route to scripting a per-record computation in any language. R4 therefore
did **not** author its own commit and cannot quote its own SHA: as in R2 and R3,
the remote-workers transport commits the working tree after the session ends,
and the lead must read the branch tip for the authoritative SHA. Read-only git,
file read/write tools,
PowerShell `ConvertFrom-Json` over a single file path, and a coreutils subset
(`grep` including `-P`, `head`, `tail`, `wc`, `sort`, `uniq`, `tr`, `od`,
`sha256sum`, `diff`) were permitted.

**Consequence, stated plainly.** R4 verified *bytes*: arity, uniqueness, JSON
well-formedness, scenario containment, archetype distinctness, byte hygiene and
every pinned digest. R4 verified **no behaviour**. The freeze verifier, the
generator and the test suite have never been executed in any worker session for
this artifact, including this one. **CI on the transport-created commit is the
first machine check of any of it, and the lead should read that exact run rather
than this document.**

**Coordination branch not read.** `git fetch origin coordination/swarm-control`
was refused again and no `coordination/*` ref exists locally, so
`EXT-WORKER-PC-V2B-001-R4.md`, `EVAL_131_QUALIFICATION_PROTOCOL.md` and
`ART-V13-TASK_POOL_REPAIR_CONTRACT.md` were **not read**. The requirements acted
on are those stated in the task instruction; protocol constants are the in-repo
restatement in `docs/evidence/g13/QUALIFICATION_CRITERION.md`. **If the
coordination branch disagrees, the coordination branch wins.**

### Commands R4 actually executed, and what they showed

| Check | Command | Result |
|---|---|---|
| inherited cover digest, before any R4 edit | `sha256sum -c --strict SHA256SUMS` | **29/29 OK** |
| re-minted cover digest, after every R4 edit | `sha256sum -c --strict SHA256SUMS` | **30/30 OK** |
| tip identity | `git rev-parse HEAD`, `git log --oneline -5` | `f780033`, parent `6467552` |
| coordination refs | `git branch -r --list '*coordination*'` | none reachable |
| line endings | `git ls-files --eol benchmarks/g13/pool_freeze_v2` | `i/lf w/lf attr/-text` for all frozen files |
| CR bytes in re-authored bytes | `grep -c -U -P '\r'` over 16 shards + table + commitment | **0** everywhere |
| trailing newline | `od -c` over the tail of each shard | exactly one `\n` |
| corpus size | `wc -l` over all 16 shards | 15 each, **240** |
| JSON well-formedness | `Get-Content <shard> \| ConvertFrom-Json \| Measure-Object`, per shard | `Count: 15` for all 16 |
| **archetype count** | `grep -ho '"variant":"[a-z_]*"' <16 shards> \| sort -u \| wc -l` | **240 distinct over 240 records** |
| case-id uniqueness | `grep -ho '"id":"g13v2_…"' \| sort \| uniq -d` | no duplicate |
| reference-id uniqueness | `grep -hoP '"hidden_reference_id":"\Kg13hr2-[0-9]+' \| sort -u \| wc -l` | **240** |
| id ↔ reference-id binding | `grep -cE` over the first and last record of every shard | **2 per shard** — every shard boundary matches the committed commitment |
| answer-key leakage | `grep -l` for the 21 denylisted key names over all 16 shards | **no file matches** |
| **scenario containment** | `grep -oh <15 nouns> \| sort \| uniq -c` | **exactly 32 each** — one `scenario` field and one instruction carrier per record, never a clause |
| **archetype distinctness** | `grep -hoP` instruction tail after the scenario noun `\| sort -u \| wc -l` | **240** |
| archetype distinctness, normalised | instruction `\| tr A-Z a-z \| tr -c a-z ' ' \| sort -u \| wc -l` | **240** |
| per-cell item arity | `grep -o '"ref":"RQ-[0-9]*"' \| sort \| uniq -c` and the `ROW`/`STP`/`EV` equivalents | every structural load in the table above |
| dependency endpoints | item-id count vs fan-out edge count, per boundary index, per planning shard | **exact match** — no dangling endpoint |
| dependency edge totals | `grep -o` edge pattern `\| wc -l` per planning shard | 20 / 60 / 90 / 135 for S / M / L / XL |
| placeholder + empty-container scan | `grep -nE '\[\s*\]\|\{\s*\}\|:\s*null'` and the placeholder-word scan over every frozen `.json` | **no match** |
| manifest well-formedness | `Get-Content … -Raw \| ConvertFrom-Json` | parses |

### R3 environment (historical)

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

### R2's checks, retained (historical; measured the discarded corpus)

> **Superseded by R4.** The two tables in this section measured the R2 corpus
> bytes, which no longer exist. They are retained because they are the record of
> what was checked at the time. The equivalent R4 measurements over the
> re-authored corpus are in *Commands R4 actually executed* above; in particular
> the per-record band table below uses R2's item refs and planning step ids
> (`IDX`, `VAL`, `ENR`, `PUB`), which the re-authored planning corpus replaced
> with `STP-1 … STP-11`.

The table below is R2's record of its own coreutils checks. R3 re-ran the digest,
arity and line-count rows and they held for the R2 corpus. R3 did **not**
re-derive the per-record band table; it is retained as R2 wrote it, still
unexecuted.

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

**Not executed by any packet in this lineage — the lead must run all four:**

```sh
python scripts/g13_freeze_task_pool_v2.py --verify --stats
python -m pytest tests/evals/test_task_pool_freeze_v2.py -q
ruff check src/swarm/evals/g13_*.py src/swarm/evals/task_pool_freeze_v2.py \
           scripts/g13_freeze_task_pool_v2.py tests/evals/test_task_pool_freeze_v2.py
mypy src/swarm/evals/g13_size_classifier_v2.py src/swarm/evals/g13_prompt_v2.py \
     src/swarm/evals/g13_sealed_reference.py src/swarm/evals/g13_independence.py \
     src/swarm/evals/g13_semantic_group.py src/swarm/evals/task_pool_freeze_v2.py
```

**The Python is still unexecuted, in all three packets.** The corpus arity,
digests, uniqueness, archetype counts and leakage counts above were established
with coreutils, but no packet in this lineage has run `derive_features`,
`render_prompt`, `normalise_template`, `semantic_fingerprint` or
`verify_pool_freeze_v2` against the committed bytes. If any of them disagrees
with this document, the code wins and this freeze needs a correction. **The CI
run on the transport-created commit is the only machine check that exists, and
it is the thing to read.**

**Not read:** `origin/coordination/swarm-control` could not be fetched in any of
the three packets, so `EXT-WORKER-PC-V2B-001-R2.md`, `-R3.md`, `-R4.md`,
`EVAL_131_QUALIFICATION_PROTOCOL.md`, `ART-V13-TASK_POOL_REPAIR_CONTRACT.md`,
`ARTIFACT_MANAGEMENT.md`, `ARTIFACT_REGISTRY.json`, `WORK_QUEUE.md` and
`AGENT_MESSAGES.md` were unavailable. The protocol constants used here
(families, sizes, `n >= 15`, max 60, one-sided 90 % Wilson >= 0.80, >= 3 exact
model configs) were taken from `docs/evidence/g13/QUALIFICATION_CRITERION.md`.
**If the coordination branch says otherwise, the coordination branch wins.**

## Open blockers

| id | state | summary |
|---|---|---|
| **B2-v2** | open | the sealed reference bundle does not exist; its content digest is unbound, so `counted_qualification_ready` is `false`. It must now be minted against the **re-authored** corpus and quote the current id-commitment digest |
| **B4** | open | `wilson_lower_bound` still defaults to `z = 1.96`; counted runs must pass `z = 1.2815515655446004` explicitly. Unchanged by all three packets |
| **B5** | open | no LICENSE file at the frozen commit |
| **B6** | open | the v2 verifier, generator and tests have never been executed in any worker environment for this artifact, R4 included. CI on the transport commit is the first machine check |
| **B7** | **closed by R4** | the corpus was re-authored as 240 distinct archetypes, 15 per required cell, and `g13-semantic-group-axis-v1` now fails the freeze when any cell falls below 15 |
| **B8** | **closed by R4** | the failure is `test_commitment_renders_opaque_ids_only`; the frozen commitment header named the words it promised to exclude. Header reworded, assertion strengthened. See [The offline pytest failure](#the-offline-pytest-failure--r4) |
| **B9** | **open, raised by R4** | the semantic group axis is lexical. A re-skin that re-authors clauses rather than appending them, and rewords the recipe, would still buy a group. The axis closes the three transformations the packet names and no more |

## Scope discipline

Files touched by this packet live only in benchmark, evaluation, evidence and
test paths. **No** Session-A-owned API, store, route, schema, CLI, database
migration, `pyproject.toml` or lockfile was edited. No `swarm/api`, `swarm/db`,
`swarm/cli` or `migrations` path was opened for writing. No coordination
acceptance state, provider config, secret, or `main`/release/deployment state
was touched, and nothing was merged.

## Claims / not claimed

| Claimed | Not claimed |
|---|---|
| A versioned held-out corpus, `g13-pool-freeze-v2`, with 240 input-only records re-authored by R4 | That ART-V13-TASK-POOL is accepted |
| 15 held-out records **and 15 distinct semantic archetypes** in every required coding/planning/reasoning/extraction × S/M/L/XL cell | That any repository Python was executed in the R4 worker session — none was |
| Zero answer, grader, reference, rubric or solution **field names** anywhere in the corpus | That counted qualification may start, or that any cell is qualified |
| A sealed grader-reference interface exposing only an opaque id plus version identity, fail-closed on this branch | That the sealed reference bundle exists, or that its content digest is bound |
| A fail-closed, versioned independence checker covering all eight digest and template overlap axes, **unchanged and byte-identical to R2** | That R4 strengthened, relaxed or otherwise touched that checker — it did not |
| A second fail-closed, versioned axis covering semantic archetype depth, scenario substitution and clause containment | That the new axis catches every possible re-skin — see **B9** |
| Eleven pinned, non-floating identities | That the v2 verifier, generator or tests were executed in any worker environment |
| A readiness value the verifier computes and refuses to let the manifest overstate | That `counted_qualification_ready` says anything about a model |
| v1 preserved unchanged as historical incomplete evidence | That v1 is usable for counted qualification |
| Digest, arity, uniqueness, archetype, scenario-containment and JSON checks actually run with coreutils and `ConvertFrom-Json` | Any threshold, default or protocol constant change |
| The exact-tip offline pytest failure identified by reading, fixed at source, and its assertion strengthened | That the fix was observed to pass — it was not run here; read the CI on the transport commit |
| Provenance bound to the real parent commit `f7800332594d67c8b872b3597abd59f35987a2a0` | That W-131B was started — it was not |
