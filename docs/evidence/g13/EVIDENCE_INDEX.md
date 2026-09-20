# G13 / EVAL-131 evidence index

**Tip binding:** `3b0011f0605573ab77318981691f588ac72f912f`  
**Qualification claimed:** **false** · S+M dual-model n=5 measured (24 cells); L/XL + third config + acceptance criterion still open

| Artifact | Claim | Not claimed |
|----------|-------|-------------|
| `eval-131/coverage-matrix-scaffold.json` | 4×4×model scaffold; untested/provisional cells explicit | Qualification |
| `eval-131/aggregated-provisional-matrix.json` | Aggregated local $0 provisional cells; **24 cells at n≥5** (S+M × 6 families × 2 models) | Automatic qualification |
| `eval-131/holdout-*-summary.json` + `run_*.json` | Brokered local screening runs | Paid/remote qualification |
| `benchmarks/starter.jsonl` | **5 holdout cases per family×size** (224 rows) | Automatic qualification |
| `eval-131/holdout-S-n5-partial-screening-summary.json` | Partial n=5 path: coding+planning × S × gemma3:4b | Full matrix |
| `eval-131/holdout-S-n5-all-families-dual-model-screening-summary.json` | All 6 families × S × gemma3:4b+qwen3.5:4b, 60 trials, $0 | Qualification |
| `eval-131/holdout-M-n5-all-families-dual-model-screening-summary.json` | All 6 families × M × gemma3:4b+qwen3.5:4b, 60 trials, $0 | Qualification |

**This tranche (no CLI login):** broader S+M all-families dual-model $0 screening at n=5 (`run_cf7c9c…`, `run_1138a279…`; 120 trials total; $0). Strong provisional: planning S/M both models =1.0; reasoning S/M qwen3.5=1.0; coding M qwen3.5=1.0. Weak/zero: review + summarization both models both sizes; gemma3 extraction/coding weak. Still **provisional** — no invented qualification. SKIP uncleared.
