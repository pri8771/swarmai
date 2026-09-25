# TH-07 evidence summary

**Date:** 2026-09-25T15:59Z  
**Hostname:** `swarm.splitsignal.ai`  
**Dataset:** `benchmarks/starter.jsonl` (128 cases)

## Outcome

Synthetic evaluation harness prepared and proven **independently of live route/budget grants**. Live gate remains blocked. Production ProfileStore was not mutated. No auto production routing changes.

## Suite coverage

| Axis | Coverage |
|---|---|
| Difficulties | easy / medium / hard / expert (S/M/L/XL) |
| Families | extraction, classification, evidence_qa, code_generation, code_repair, dependency_planning, tool_selection, context_compaction |
| Splits | calibration 64 / holdout 64 (reported separately) |
| Graders | json_exact, python_unit, topological_order |

## Results

| Check | Result |
|---|---|
| pytest `test_synthetic_harness_th07` | **pass** (10) |
| pytest evals suite (related) | **pass** (24 incl. prior) |
| `scripts/th07_synthetic_eval_harness.py` | **pass** |
| Oracle full suite | **128/128** |
| Holdout vs calibration | **64/64 each** |
| Fixture-fail negative control | **0/8** (expected) |
| Live gate without grant | **blocked** |
| Live dispatch with probe grant | **still blocked** (TH-07 first cut) |
| Production routing mutation | **none** |
| Spend | **$0** |

## Commands

```sh
uv run pytest tests/evals/test_synthetic_harness_th07.py -q
uv run python scripts/th07_synthetic_eval_harness.py
```

## Artifacts

- `manifest.json` — suite prepare-only description
- `latest.json` — oracle run report
- `proof-latest.json` — proof script aggregate
- `th07-synthetic-harness-*.json` — stamped proof

## Not run / blocked

Live provider dispatch (needs approved route+budget grant + live wiring), R730, `.ai` DNS, Cloudflare Tunnel, Linear MCP (`needsAuth`), paid inference.
