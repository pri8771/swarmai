# Final engineering checks

| Check | Exact source | Result |
|---|---|---|
| Baseline offline probe | accepted base `ba458eb` | PASS after explicit `PYTHONPATH`; inline/vocabulary/digest gaps reproduced |
| Manifest contract + receipt PostgreSQL proof | settled production behavior | 19 passed; exit 0; disposable DB cleanup 0 |
| Compatibility-focused PostgreSQL rerun | `1ea1ca55` | 35 passed in 4.60s; exit 0; cleanup 0 |
| Full suite with PostgreSQL | `1ea1ca55` | 612 passed in 39.74s; exit 0; cleanup 0 |
| Migrated production permission path | `1ea1ca55` | migration 0; workflow 0; 1 effect / 1 receipt / 1 used approval; stored canonical 64-hex digest; cleanup 0 |
| Ruff | `1ea1ca55` | all checks passed |
| Mypy | `1ea1ca55` | 173 source files passed |
| Worktree | `1ea1ca55` / tree `1b8577c9` | clean |

Preserved adverse evidence: provisional full run 41 failed / 571 passed. The settled four-file test-helper correction and green compatibility/full reruns close that failure; it was not deleted or rewritten.

An earlier inherited compatibility selection was root-reported as 46 passed / 51 skipped without a raw log supplied to the packet owner. It remains historical engineering context and is not used as final proof.
