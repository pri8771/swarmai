# G13 benchmark freezes

`pool_freeze_v1/` is the frozen EVAL-131 calibration / held-out task pool for
artifact **ART-V13-TASK-POOL** (packet V2B-001, work item W-131C1).

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

## Independent verification

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

## Status

`qualification_claimed = false`. The freeze does **not** authorise counted
qualification: `qualification_readiness.counted_qualification_ready` is `false`
because the required cells hold 5 distinct held-out records each and the
protocol needs `n >= 15`. See `docs/evidence/g13/TASK_POOL_FREEZE.md`.
