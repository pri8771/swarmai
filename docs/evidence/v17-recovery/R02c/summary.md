# R02c — echo detection, targeted edit blocks, mandatory regression test

Packet: R02c (new, hold-independent) · Artifact: ART-V14-REAL-E2E · Worker engine: fable
Base source SHA: `ebe71f237de2536890ef4f29f27e12efb8986641` · Tested source SHA: see `verify-receipt.json`.

## Why
v14-real-006 and v14-real-008 failed the same way: asked for a full-file rewrite, the local model echoed the file back unchanged. Separately, `RepoWorker._implement` only ever wrote one production file, so the R02a red→green gate (`no_regression_test_in_patch`) could never pass on the operational path regardless of the model.

## Source changes
- `src/swarm/mission/worker.py` (generic implement path only; the parser-dogfood fixture path is unchanged):
  - Prompt now asks for `### EDIT <path>` SEARCH/REPLACE blocks against the current file **plus** a `### NEW tests/<pkg>/test_<name>.py` regression file; system prompt forbids whole-file answers.
  - `_parse_targeted_change`, `_apply_edit_blocks` (whole-line matching, each SEARCH must match exactly once — substring matches are rejected, so `return valu` cannot hit `return value`), `_is_echo` (normalized/fence-tolerant equality or difflib ratio ≥ 0.995), `_valid_new_test_path` (`tests/**/test_*.py`, no `..`, no absolute).
  - Flow: call 1 → edit blocks applied, or a non-echo full file accepted as before; echo or unmatched blocks → exactly one re-prompt with an explicit note; still nothing → `implement_no_material_diff` with `echo_detected: true` (nothing written) or `implement_failed_no_known_answer_fallback`.
  - New test files are validated (path, syntax, contains `def test_`), written into the worktree and registered with `git add -N` so the diff — and therefore the gate — sees them; `changed_files` lists them.
  - Artifacts gain `inference_calls`, `edit_blocks_applied`, `new_test_files`, `rejected_new_files`, `echo_detected`, `reprompted`, `unmatched_edit_blocks`; `inference` carries token/cost totals across both calls (`calls`).
- `src/swarm/mission/worktree.py`: `intent_to_add(handle, paths)`.
- `tests/mission/test_r02c_targeted_edits.py`: 7 tests, no model — parse/apply, echo + path rules, echo→re-prompt→edit+test in diff, double echo writes nothing, unmatched blocks fail honestly after one re-prompt, rejected test paths never written, and the end-to-end case where the model-written regression passes `prove_defect` (red pre-patch, green post-patch).

## Not claimed
No new real mission has been run with this change yet (attempt 2 of v14-real-008 follows as a separate, preregistered live packet; its result needs EXT-V14-LEAD-REVIEW).

## Checks
- `uv run pytest tests/mission/test_r02c_targeted_edits.py -v` → 7 passed (`pytest-output.txt`); `tests/mission` → 57 passed.
- Full suite → see `verify-receipt.json`. Ruff clean; mypy clean.
