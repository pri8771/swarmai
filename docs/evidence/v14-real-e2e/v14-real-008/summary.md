# v14-real-008 (R02b attempt 1 / CP1) — FAILED, preserved

- Mission: `1a3d052c8b4048ec99fa8c574f0f88c6` (persisted; visible via `GET /v1/missions` on the candidate)
- Candidate SHA: `ffa33171180a8c918b87cd86d926c497a515b099` · preregistration commit `e405077`
- Subsystem: `src/swarm/runtime/backpressure.py` (unaudited; not used by 005/006/007)
- Real brokered local inference: 3 calls to `qwen2.5-coder:14b`, spend $0.0
- Isolated worktree: yes · material diff: **no** · primary checkout modified: no · auto-apply: no
- R02a gate: `defect_proof.proven=false` (`no_regression_test_in_patch`) · review: not reached
- Self-accept: **no** · this attempt is a negative result and stays unchanged

## What happened
The model echoed the target file back verbatim as a full-file rewrite in all three rounds; `implement_no_material_diff` fired each time. Existing `tests/runtime` stayed green (12 + 18 passed), which the new gate correctly treats as insufficient.

## Why no second attempt now
Same failure class as v14-real-006 with no new diagnostic beyond "verbatim echo". The delivery contract requires a small diagnosis/repair packet instead of a blind retry: **R02c** — detect verbatim/near-verbatim echo before write and re-prompt for a diff-shaped targeted change plus regression test. After R02c, attempt 2 of v14-real-008 (or a new preregistration) can run.

## Files
`pre-run-freeze.json`, `mission-run.stdout.json` (full runtime output incl. model_output_excerpt), `mission-run.stderr.txt`, `mission-report.json`, `mission-list.json`, `cost-show.json`, `manifest.json`.
