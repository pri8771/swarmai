# ART-V13-TASK-POOL — frozen G13 calibration vs held-out pool (packet V2B-001 / W-131C1)

**Requested transition:** `drafting -> reviewable`
**Accepted:** **no** — lead review requested, not granted
**qualification_claimed:** **false** · **counted held-out runs in this packet:** **0**
**Base:** `cursor/v2-integration` @ `9ce727842446b98cfa55c28c7e70808f57f17d7b`
**Branch:** `worker/swarmai-v13-task-pool-freeze-02`

## What is frozen

| Frozen thing | Identity | Where |
|---|---|---|
| Task pool | `g13-pool-freeze-v1` over `benchmarks/starter.jsonl` @ `573bad7f…be78`, 224 records | `benchmarks/g13/pool_freeze_v1/task_pool_freeze_v1.manifest.json` |
| Per-record immutability | 224 × sha256 of the exact record line including its LF | `POOL_RECORD_DIGESTS.txt` @ `c8ca2abf…b051` |
| Size classifier | `g13-size-classifier-v1`, 6 structured features, per-family bands | `identity_size_classifier_v1.json` + `src/swarm/evals/size_classifier.py` |
| Scorer | `g13-scorer-v1` (json_exact, topological_order, python_unit) | `identity_scorer_v1.json`, pins `graders.py`, `sandbox_runner.py`, `wilson.py` |
| Prompt | `g13-prompt-v1`, verbatim passthrough, no system prompt, no exemplars | `identity_prompt_v1.json`, pins `dataset.py` |
| Tool protocol | `g13-tool-protocol-v1-no-model-visible-tools` | `identity_tool_protocol_v1.json` |
| Model config identity | `g13-exact-model-config-v1` (JSON Schema) | `identity_model_config_schema_v1.json` |
| Cover digest | every file above | `SHA256SUMS` |

## Split design

| | calibration / screening | qualification held-out |
|---|---|---|
| ids | `<family>_<size>_01`, `_02` | `<family>_<size>_03` … `_07` |
| count | 64 | 160 |
| per required cell | 2 | 5 |
| may be used for | screening, routing calibration, prompt inspection | counted qualification only |

Required product families map one-to-one onto dataset families, following
`swarm.evals.live_benchmark.FAMILY_MAP`:

| product family | dataset family | sizes |
|---|---|---|
| coding | `code_generation` | S, M, L, XL |
| planning | `dependency_planning` | S, M, L, XL |
| reasoning | `evidence_qa` | S, M, L, XL |
| extraction | `extraction` | S, M, L, XL |

The other four dataset families (`classification`, `code_repair`,
`tool_selection`, `context_compaction`) are frozen as **auxiliary**: in the pool,
out of the required coverage. They are not folded into the required families,
because merging several dataset families into one qualification cell lets a
strong sub-family mask a weak one.

## Contamination boundary

Enforced as hard failures by `swarm.evals.task_pool_freeze.verify_pool_freeze`:

1. no case id in both splits;
2. no record sha256 in both splits;
3. no identical model-visible prompt digest across splits;
4. no two held-out records sharing a model-visible prompt digest (which would
   inflate distinct-case counting).

Derived digests (visible prompt, hidden answer, normalised template) are
deliberately **not** stored. They are pure functions of the frozen record bytes,
which are already pinned by the whole-file digest and by all 224 record digests,
so storing them would only add a second thing to drift. The verifier recomputes
them.

## Size classifier

`g13-size-classifier-v1` reads the structured features already persisted on each
record — `input_characters`, `input_tokens_estimate`, `entity_count`,
`dependency_depth`, `file_count`, `tool_steps` — and buckets on
`input_tokens_estimate` using **per-family** inclusive upper bounds. Per-family
is not a stylistic choice: a global cut cannot work, because
`dependency_planning` XL (471–535 estimated tokens) sits below `classification`
L (538). The verifier asserts the classifier reproduces the declared band for
all 224 records, and a test asserts the JSON spec mirrors the module exactly.

The classifier does **not** re-derive character or token counts from prompt
text. Those numbers are owned by the pool generator (`seed-v1`); re-deriving
them here would fork one definition into two.

## Blockers (why this artifact does not unblock counted qualification)

**B1 — held-out depth is 5, the protocol needs 15.**
`docs/coordination/EVAL_131_QUALIFICATION_PROTOCOL.md` (as restated in
`QUALIFICATION_CRITERION.md`) requires `n >= 15` independent held-out
observations per `(exact_model_config, family, size)` cell, and
`swarm.evals.profiles.ProfileStore` counts **distinct** cases for the Wilson
bound. Five distinct held-out records per required cell cannot reach 15 by
re-running the same five. Closing the minimum needs **160** additional distinct
held-out records (10 × 16 required cells); reaching the `n = 60` ceiling needs
**880**. The manifest declares both numbers and the verifier recomputes them, so
the declaration cannot silently drift.

**B2 — hidden answers are worker-visible on this branch.**
`expected_output`, `grader`, `reference_solution` and `broken_code` sit in
plaintext inside `benchmarks/starter.jsonl`. Any worker with repository read
access can read the held-out answers. This **predates** packet V2B-001 and is
not introduced by it; this artifact commits no reference answer, grader fixture
or solution text, and a test asserts that no frozen file contains any hidden
value from the pool. But the condition means the held-out split is not truly
sealed, and counted qualification run under it is contestable. Remediation is
recorded in `hidden_answer_policy.remediation_required_before_counted_qualification`
and requires a re-freeze to `g13-pool-freeze-v2`, because moving the hidden
fields changes the record bytes and therefore every record digest.

**B3 — seed-isomorphic held-out variants.**
The generator emits variants that differ only in their synthetic identifiers
(`task_514_08` vs `task_548_08`). Such records are distinct by digest but are
not statistically independent, so a Wilson bound over them overstates
confidence. The verifier reports `cross_split_template_isomorphs` and
`distinct_held_out_templates` as statistics; it does not enforce them, because
driving them to zero requires regenerating the pool.

**B4 — the Wilson default z is wrong for this protocol.**
`swarm.evals.wilson.wilson_lower_bound` defaults to `z = 1.96` (one-sided 97.5%).
The protocol wants a one-sided **90%** bound, `z = 1.2815515655446004`. Counted
runs must pass `z` explicitly. Recorded in `identity_scorer_v1.json`; **no
threshold or default was changed by this packet.**

**B5 — no LICENSE file at the frozen commit.**
The pool is fully synthetic and generated in-repo (zero third-party datasets,
zero scraped records, no personal data), so it inherits repository terms — but
the repository states none. Recorded as `license_blocker`; it affects
redistribution, not contamination or immutability.

## Verification status (read this before accepting)

The worker environment for this packet **denied execution** of `python`,
`pytest`, `ruff`, `mypy` and every writing git command (`git add`,
`git commit`, `git fetch`, `git push`). Read-only git, file tools, PowerShell
`ConvertFrom-Json` and coreutils (`head`, `tail`, `cut`, `diff`, `sort`,
`uniq`, `od`, `sha256sum`) were permitted.

What that means, precisely:

* **Not committed:** the artifact exists in the **working tree** of
  `worker/swarmai-v13-task-pool-freeze-02` only. There is no commit and no
  pushed branch, so there is **no commit SHA to quote**. The branch is at the
  unchanged base `9ce7278`.
* **Not run:** `pytest tests/evals/test_task_pool_freeze.py`, `ruff check`,
  `mypy`, `python scripts/g13_freeze_task_pool.py --verify`. The lead must run
  all four. The new code is unexecuted.
* **Not read:** `origin/coordination/swarm-control` could not be fetched, so
  `ARTIFACT_MANAGEMENT.md`, `ARTIFACT_REGISTRY.json`,
  `EVAL_131_QUALIFICATION_PROTOCOL.md`, `WORK_QUEUE.md`,
  `WORKER_PACKET_BACKLOG.md` and `AGENT_MESSAGES.md` were unavailable. The
  protocol constants used here (families, sizes, n ≥ 15, max 60, one-sided 90%
  Wilson ≥ 0.80, ≥ 3 exact model configs) were taken from
  `docs/evidence/g13/QUALIFICATION_CRITERION.md`, which states it is aligned to
  the frozen lead protocol v1.0 + LEAD-20260920-013. **If the coordination
  branch says otherwise, the coordination branch wins and this freeze needs a
  correction.**
* **Actually verified, with the tools that were available:**
  1. all seven frozen files hash as recorded (`sha256sum`), and `SHA256SUMS`
     was produced by `sha256sum` itself;
  2. the digest file's 224 ids match the dataset's record order exactly
     (`cut` + `diff`, zero differences);
  3. three record digests recomputed by an independent command path
     (`tail -n +K | head -n 1`) matched entries 1, 100 and 224;
  4. all 224 record digests are distinct (`sort | uniq -d`, empty);
  5. every committed JSON file parses;
  6. manifest membership equals the dataset id set: calibration is exactly the
     64 `_01`/`_02` ids, held-out exactly the 160 `_03`…`_07` ids, union 224,
     intersection empty;
  7. the per-family size bands were derived from, and checked against, every
     observed `input_tokens_estimate` value in the pool.

## Claims / not claimed

| Claimed | Not claimed |
|---|---|
| A frozen, digest-pinned calibration/held-out split with stable hashes | That ART-V13-TASK-POOL is accepted |
| Required coverage: 4 product families × S/M/L/XL, 5 held-out + 2 calibration per cell | That counted qualification may start |
| Persisted identities for size classifier, scorer, prompt, tool protocol and exact model config | That any cell is qualified |
| A deterministic verifier and test suite for overlap and incomplete/floating manifests | That the verifier or tests have been executed in this environment |
| An honest readiness verdict: `counted_qualification_ready = false` | Any threshold, default or protocol constant change |
