# Integration note — shared-file deltas implied by ART-V13-TASK-POOL (V2B-001 / W-131C1)

Packet V2B-001 edited **no** Session-A-owned shared file. Nothing under
`src/swarm/api/store.py`, `routes_v1.py`, `schemas.py`, `src/swarm/cli.py`,
`src/swarm/db/models.py`, `migrations/**`, `pyproject.toml` or `uv.lock` was
touched. `benchmarks/starter.jsonl` was **read only**; its bytes are unchanged
and are pinned by the freeze.

The deltas below are the ones counted qualification will need. They are written
down here rather than implemented, because they land in files this lane does not
own.

## D1 — `EvalResult` cannot carry the frozen identities (owner: contracts lane)

`src/swarm/contracts/workspace.py :: EvalResult` has `grader_version` and
`exact_prompt_hash`, but no field for the exact model configuration, the pool
freeze, the size classifier or the tool protocol. Today
`swarm/evals/live_benchmark.py` writes `grader_version="1"` and
`model_fingerprint=<alias>` — an alias, which the freeze explicitly rejects as
an identity.

Needed on a counted observation:

```
pool_freeze_id        : "g13-pool-freeze-v1"
exact_model_config_id : "emc_<32 hex>"          # per identity_model_config_schema_v1.json
exact_model_config    : object                  # the full identity, stored once per cell
scorer_id             : "g13-scorer-v1"
prompt_id             : "g13-prompt-v1"
tool_protocol_id      : "g13-tool-protocol-v1-no-model-visible-tools"
size_classifier_id    : "g13-size-classifier-v1"
split                 : "holdout"
batch_index           : int                     # batches of five
wall_ms, prompt_tokens, completion_tokens, attempts, retry_count, cost_usd
```

`CapabilityProfile` already has `prompt_version`, `tool_protocol`,
`dataset_version` and `harness_version`; `ProfileStore.record_result` currently
defaults them to `"1"` / `"none"` / `"starter-v1"`. Counted runs must pass the
frozen ids instead of accepting those defaults, otherwise every profile key
collapses onto the screening key and provisional screening data pools with
counted data.

## D2 — Wilson z (owner: evaluation lane, but a shared default)

`swarm.evals.wilson.wilson_lower_bound` defaults to `z = 1.96`, a one-sided
97.5% bound. The protocol requires one-sided **90%**,
`z = 1.2815515655446004`. `ProfileStore.record_result` and
`live_benchmark._aggregate_cells` both call it with the default.

**No default was changed by this packet.** The counted-qualification harness
must pass `z` explicitly, or a reviewed change must add an explicit
`z_one_sided_90` constant. Silently reusing 1.96 would make every published
bound tighter-looking than the protocol allows.

## D3 — sealed hidden-answer store (owner: evaluation lane + repo policy)

Blocker B2 in `TASK_POOL_FREEZE.md`. Removing `expected_output`, `grader`,
`reference_solution` and `broken_code` from the worker-visible pool changes the
record bytes, so it invalidates every record digest in
`POOL_RECORD_DIGESTS.txt` and requires minting `g13-pool-freeze-v2`. It should
therefore be done **together** with the held-out expansion in D4, not before or
after it, so the pool is re-frozen once rather than three times.

## D4 — held-out expansion (owner: evaluation lane)

Blocker B1. 160 additional distinct held-out records to reach the `n >= 15`
floor across the 16 required cells; 880 to reach the `n = 60` ceiling. The
generator should also vary structure, not only the seed integer, so the new
records are not template-isomorphic to the existing ones (blocker B3).

## D5 — no CLI surface was added

A `swarm evals freeze-pool` subcommand would belong in `src/swarm/cli.py`, which
this lane does not own. The equivalent entry point is
`scripts/g13_freeze_task_pool.py`. If the lead wants it on the CLI, that is a
Session-A change referencing
`swarm.evals.task_pool_freeze.verify_pool_freeze` and
`verify_checksums`.
