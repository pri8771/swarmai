# G13 / EVAL-131 evidence index

**Tip binding:** advances with packaging commit over feature `d9da26c7a8b47d1ffeabf866250cdbf30d14ffce`  
**Qualification claimed:** **false** · criterion aligned to LEAD-013 / protocol v1.0 · W-131A gap map packaged · no W-131B volume

| Artifact | Claim | Not claimed |
|----------|-------|-------------|
| `g13/QUALIFICATION_CRITERION.md` | Frozen rule pointer: n≥15, Wilson 90% LB≥0.80, families coding/planning/reasoning/extraction | Qualification |
| `eval-131/w131a-qualification-gap-map.json` | Machine-readable W-131A gap map vs protocol; strongest candidates; missing third-model L/XL; planned W-131B batches **not executed** | n≥15/n≥30 qualification |
| `eval-131/coverage-matrix-scaffold.json` | 4×4×model scaffold | Qualification |
| `eval-131/aggregated-provisional-matrix.json` | Aggregated local $0 provisional; **60 cells at n≥5**; 3 models; sizes S/M/L/XL | Automatic qualification |
| `benchmarks/starter.jsonl` | 5 holdouts per family×size (224 rows) | Automatic qualification |
| `eval-131/holdout-S-n5-all-families-dual-model-screening-summary.json` | S × gemma3:4b+qwen3.5:4b | Qualification |
| `eval-131/holdout-M-n5-all-families-dual-model-screening-summary.json` | M × gemma3:4b+qwen3.5:4b | Qualification |
| `eval-131/holdout-L-n5-all-families-dual-model-screening-summary.json` | L × gemma3:4b+qwen3.5:4b, 60 trials, $0 | Qualification |
| `eval-131/holdout-XL-n5-all-families-dual-model-screening-summary.json` | XL × gemma3:4b+qwen3.5:4b, 60 trials, $0 | Qualification |
| `eval-131/holdout-S-n5-third-model-qwen35-9b-screening-summary.json` | Third model qwen3.5:9b × S, 30 trials, $0 | Qualification |
| `eval-131/holdout-M-n5-third-model-qwen35-9b-screening-summary.json` | Third model qwen3.5:9b × M, 30 trials, $0 | Qualification |

**W-131A:** required family×size screening present; 8 missing third-model L/XL n=5 cells identified; 14 strong provisional candidates mapped for later W-131B; reviewer role weak. Still **provisional** — `qualification_claimed=false`. SKIP uncleared.
