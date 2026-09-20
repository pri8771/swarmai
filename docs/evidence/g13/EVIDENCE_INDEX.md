# G13 / EVAL-131 evidence index

**Tip binding:** `6dd568cdfda5b6dd73600915965c1abbf3b9100b`  
**Qualification claimed:** **false** · underpowered until measured ≥5 held-out/cell with acceptance criterion

| Artifact | Claim | Not claimed |
|----------|-------|-------------|
| `eval-131/coverage-matrix-scaffold.json` | 4×4×model scaffold; untested/provisional cells explicit | Qualification |
| `eval-131/aggregated-provisional-matrix.json` | Aggregated local $0 provisional cells (≤2/cell historically) | ≥5/cell qualification |
| `eval-131/holdout-*-summary.json` + `run_*.json` | Brokered local screening runs | Paid/remote qualification |
| `benchmarks/starter.jsonl` | **Expanded to 5 holdout cases per family×size** (224 rows) | Automatic qualification |
| `eval-131/holdout-S-n5-partial-screening-summary.json` | Partial n=5 path: coding+planning × S × gemma3:4b, 10 trials, $0 | Full matrix qualification |

**This tranche advance (no CLI login):** dataset holdout floor raised 2→5; selector `max_per_cell` default 5; partial S n=5 brokered screening recorded. Screening/qualification still requires measured runs across required cells; do not invent scores. `dependency_planning` S/gemma3 pass_rate=1.0 at n=5 remains **provisional** (single model/cell; acceptance criterion not declared-complete).
