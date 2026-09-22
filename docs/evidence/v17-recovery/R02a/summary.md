# R02a — red→green defect-proof gate for real missions

Packet: R02a · Artifact: ART-V14-REAL-E2E · Worker engine: fable (epoch fable-v17-20260922-01)
Base source SHA: `c25182dfa5b03f3b9a4409282b6ea465484fe79f` · Tested source SHA: see `verify-receipt.json`.

## Why
Real missions v14-real-005 and -007 both failed independent review for the same reason: a patch that passed existing tests but never demonstrated a pre-patch defect. Review 007 asked for a reproducible pre-patch failing behavior or a targeted regression that fails before the patch. That check is mechanical, so the runtime now performs it.

## Source changes (not re-verification)
- `src/swarm/mission/acceptance.py`: `DefectProofDecision`; `prove_defect(repo, candidate_sha, worktree, diff_text, run)` — regression tests = `tests/**/test_*.py` files in the diff; a second clean detached worktree at `candidate_sha` receives **only** those test files (production stays pre-patch); pre-patch run must be pytest exit 1 (exit 0 → `regression_passes_without_patch`; 2/3/4/5 → `pre_patch_not_a_clean_failure`), post-patch run must be exit 0 (else `regression_fails_with_patch`); the clean worktree is removed in `finally`. `is_defect_repair_goal`, `regression_tests_in_diff`. `review_attempt(defect_repair=, defect_proof=)`: for defect-repair tasks anything but `proven: true` is `no_defect_demonstrated` and can never be accepted.
- `src/swarm/mission/worker.py` (`_verify`, `_review`): for defect-repair goals `_verify` runs `prove_defect` with the same `uv run pytest` command it already uses and attaches `defect_proof` to its artifacts; `_review` passes it into `review_attempt`. The gate never edits or generates tests and never tells the model what defect to find.
- `tests/mission/test_defect_proof_gate.py`: 8 tests on temporary git repositories (no model, no network): no regression test; already-green test (the 007 shape); collection error is not "red"; regression still failing post-patch; true red→green; clean worktree removed on exception; review never passes an unproven defect repair; goal detection.

## Checks (this packet's own runs)
- `uv run pytest tests/mission/test_defect_proof_gate.py -v` → 8 passed (`pytest-output.txt`); `tests/mission` → 50 passed.
- Full suite → 433 passed, 2 skipped. Ruff clean; mypy clean.

## Not claimed
No new real mission was run (that is R02b, whose result is gated by EXT-V14-LEAD-REVIEW). The mission evidence packager's `manifest.json` will carry `defect_proof` verbatim from the verify artifacts when R02b runs.
