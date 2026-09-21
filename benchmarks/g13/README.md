# G13 benchmark freezes

Two freezes live here. **`pool_freeze_v2/` is the current one**; `pool_freeze_v1/`
is retained unchanged as historical, incomplete evidence from retry-02 and must
not be used for counted qualification.

| Freeze | Status | Why |
|---|---|---|
| `pool_freeze_v2/` | current | 240 input-only held-out inputs, 15 per required cell **and 15 distinct semantic archetypes per cell**, sealed grader references, two fail-closed independence axes |
| `pool_freeze_v1/` | historical, superseded | 5 held-out records per cell against a protocol minimum of 15, and its reference answers were worker-visible in plaintext, which burns the split |

---

## `pool_freeze_v2/` — current

Frozen EVAL-131 **held-out** corpus for artifact **ART-V13-TASK-POOL** (corpus
bytes minted by packet `EXT-WORKER-PC-V2B-001-R4`). Records are **input-only**: a
v2 record has no field in which an answer, grader fixture, rubric or reference
could sit.

Independence is enforced on **two** axes. `g13-independence-checker-v2` is
fail-closed on eight id, payload-digest, prompt-digest and normalised-template
invariants. `g13-semantic-group-axis-v1` sits on top of it and is fail-closed on
*archetype* depth: a scenario rename, a numeric or seed substitution, and
cumulative clause-only growth all collapse to one semantic group, and every
required cell must hold at least fifteen distinct groups. Record depth is not
archetype depth, and a Wilson bound counts the latter.

| File | What it pins |
|------|--------------|
| `task_pool_freeze_v2.manifest.json` | freeze/corpus identity, coverage, sealed-reference binding, foreign corpora, eleven pinned identities, computed readiness |
| `holdout/<product_family>_<size>.jsonl` | one shard per required cell, 15 inputs each, each its own semantic archetype |
| `CORPUS_SHARD_DIGESTS.txt` | the split identity: one row per shard binding family, size, split, record count and sha256 |
| `SEALED_REFERENCE_IDS.txt` | the hidden-reference id commitment — opaque surrogate keys only |
| `identity_pool_v2.json` | pool identity `g13-pool-freeze-v2` |
| `identity_records_v2.json` | record identity `g13-records-v2` |
| `identity_split_v2.json` | split identity `g13-split-v2` |
| `identity_size_classifier_v2.json` | structured size classifier `g13-size-classifier-v2` |
| `identity_scorer_v2.json` | scorer / grader contract `g13-scorer-v2` |
| `identity_prompt_v2.json` | prompt and model-visible surface `g13-prompt-v2` |
| `identity_tool_protocol_v2.json` | tool protocol `g13-tool-protocol-v2-no-model-visible-tools` |
| `identity_model_config_schema_v2.json` | `exact_model_config` schema `g13-exact-model-config-v2` |
| `identity_independence_checker_v2.json` | contamination checker `g13-independence-checker-v2` |
| `identity_semantic_group_v1.json` | semantic archetype axis `g13-semantic-group-axis-v1` |
| `identity_sealed_reference_v2.json` | sealed grader-reference interface `g13-sealed-reference-interface-v2` |
| `SHA256SUMS` | digest of every file above, recursively |

### Independent verification

```sh
# immutability, with nothing but coreutils (run from inside pool_freeze_v2/)
sha256sum -c --strict SHA256SUMS

# full verification: identities, coverage, leakage, independence, readiness
python scripts/g13_freeze_task_pool_v2.py --verify --stats
python -m pytest tests/evals/test_task_pool_freeze_v2.py -q
```

### Status

`counted_qualification_ready` is **computed**, not asserted: the verifier
requires it to equal `freeze_conditions_pass and sealed_bundle_content_digest_bound`,
so the manifest cannot drift into an unearned claim. It is currently **false**,
because the sealed reference bundle is minted outside this branch and its content
digest is not yet bound. It is a statement about the freeze, never about a model.
See `docs/evidence/g13/TASK_POOL_FREEZE_V2.md`.

---

## `pool_freeze_v1/` — historical, superseded

`pool_freeze_v1/` is the frozen EVAL-131 calibration / held-out task pool for
artifact **ART-V13-TASK-POOL** (packet V2B-001, work item W-131C1). It is kept
byte-for-byte as it was, as the record of what retry-02 did and did not verify.
Its calibration split is still the screening split; its held-out split is burned.

| File | What it pins |
|------|--------------|
| `task_pool_freeze_v1.manifest.json` | split membership, coverage, source/licence metadata, identity bindings, readiness |
| `POOL_RECORD_DIGESTS.txt` | one sha256 per frozen record, in dataset file order |
| `identity_size_classifier_v1.json` | structured-feature size classifier `g13-size-classifier-v1` |
| `identity_scorer_v1.json` | deterministic scorers `g13-scorer-v1` |
| `identity_prompt_v1.json` | prompt assembly contract `g13-prompt-v1` |
| `identity_tool_protocol_v1.json` | tool protocol `g13-tool-protocol-v1-no-model-visible-tools` |
| `identity_model_config_schema_v1.json` | `exact_model_config` schema `g13-exact-model-config-v1` |
| `SHA256SUMS` | digest of every file above |

### Independent verification

Immutability, with nothing but coreutils:

```sh
sha256sum -c benchmarks/g13/pool_freeze_v1/SHA256SUMS   # run from inside that directory
sha256sum benchmarks/starter.jsonl                      # must equal pool_source.sha256
head -n 1 benchmarks/starter.jsonl | tail -n 1 | sha256sum   # must equal line 1 of the digest file
```

Full verification, including the contamination boundary:

```sh
python scripts/g13_freeze_task_pool.py --verify --stats
python -m pytest tests/evals/test_task_pool_freeze.py -q
```

### Status

`qualification_claimed = false`. The v1 freeze does **not** authorise counted
qualification: `qualification_readiness.counted_qualification_ready` is `false`
because the required cells hold 5 distinct held-out records each and the
protocol needs `n >= 15`. See `docs/evidence/g13/TASK_POOL_FREEZE.md`.
