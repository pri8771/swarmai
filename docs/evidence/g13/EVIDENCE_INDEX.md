# G13 / EVAL-131 evidence index

**Tip binding:** `f75c6cb5bb8e0d2d2d2c0c6e4061fe2909f11efc` (screening tip; docs tip advances with this commit)  
**Qualification claimed:** **false** · S/M/L/XL dual-model + third model (qwen3.5:9b) on S+M measured; acceptance criterion still open

| Artifact | Claim | Not claimed |
|----------|-------|-------------|
| `eval-131/coverage-matrix-scaffold.json` | 4×4×model scaffold | Qualification |
| `eval-131/aggregated-provisional-matrix.json` | Aggregated local $0 provisional; **60 cells at n≥5**; 3 models; sizes S/M/L/XL | Automatic qualification |
| `benchmarks/starter.jsonl` | 5 holdouts per family×size (224 rows) | Automatic qualification |
| `eval-131/holdout-S-n5-all-families-dual-model-screening-summary.json` | S × gemma3:4b+qwen3.5:4b | Qualification |
| `eval-131/holdout-M-n5-all-families-dual-model-screening-summary.json` | M × gemma3:4b+qwen3.5:4b | Qualification |
| `eval-131/holdout-L-n5-all-families-dual-model-screening-summary.json` | L × gemma3:4b+qwen3.5:4b, 60 trials, $0 | Qualification |
| `eval-131/holdout-XL-n5-all-families-dual-model-screening-summary.json` | XL × gemma3:4b+qwen3.5:4b, 60 trials, $0 | Qualification |
| `eval-131/holdout-S-n5-third-model-qwen35-9b-screening-summary.json` | Third model qwen3.5:9b × S, 30 trials, $0 | Qualification |
| `eval-131/holdout-M-n5-third-model-qwen35-9b-screening-summary.json` | Third model qwen3.5:9b × M, 30 trials, $0 | Qualification |

**This tranche (no CLI login):** third local model config (qwen3.5:9b) on S+M; L+XL dual-model $0 screening. Strong provisional: planning nearly all sizes/models; coding S/M/XL qwen family; extraction L qwen3.5:4b=1.0. Persistently weak: review + summarization. Still **provisional** — `qualification_claimed=false`. SKIP uncleared.
