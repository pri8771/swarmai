# ART-V14-REAL-E2E materialization audit 01 — independent lead review

Date: 2026-09-21
Lead run: LEAD-20260921-036
Remote task: `swarmai-v14-materialization-audit-01`
Worker: `worker-pc` / Claude
Mode: read-only
Remote result: success as diagnostic transport; no source branch/commit expected
Disposition: **useful diagnostic evidence; no artifact transition; Lane A still owns V14-REAL-001-R**

## Independently verified path

Current Lane-A source at `cursor/v2-runtime-lane@11a7e1d51c4c4d630c7d83c1af65e380c32ad80f` implements the generic path through:

- goal/plan: `src/swarm/mission/planner.py`
- orchestration/retry: `src/swarm/mission/runtime.py`
- implement worker: `src/swarm/mission/worker.py::RepoWorker._implement`
- model call: `RepoWorker._chat` -> governed brokered inference when required
- parser/materializer: `worker.py::_extract_python_file` then `target.write_text(...)`
- isolation/diff: `src/swarm/mission/worktree.py::create_worktree` and `worktree_diff`
- verify/review: `RepoWorker._verify` / `_review`

The failed real mission remains valid negative evidence: it used actual local brokered inference at $0 and review rejected an empty material diff rather than inventing success.

## Confirmed generic defects / repair targets

### 1. Parser contract and prompt contract are inconsistent

`RepoWorker._implement` asks the model to **return only the full corrected file contents**. For generic missions it then calls `_extract_python_file(inference.text)`.

But `_extract_python_file` only accepts:
- a Markdown triple-backtick fence matching ` ```(?:python)?\n...``` `; or
- a fixture-specific fallback containing the exact symbol `def inclusive_range_count`.

Therefore a completely valid generic model response containing raw Python source exactly as requested — with no Markdown fence — is rejected as unparsable. The only raw-source fallback is explicitly tied to the parser-dogfood fixture and cannot safely serve generic missions.

This is a generic materialization defect and is consistent with a model producing useful implementation text while no worktree edit is made. Repair must not add target-specific known-answer logic.

### 2. Empty-diff/no-op implementation reporting is ambiguous

After writing `patched`, `_implement` computes `diff = worktree_diff(handle)` and returns:

- `ok = bool(diff.strip()) or patched != original`
- `summary = "implement_applied"` unconditionally.

This allows the summary/retry trace to say `implement_applied` even when `ok` is false and the material git diff is empty. The preserved V14-REAL-001 evidence contains `implement_applied` retry reasons while final review correctly reports no material diff.

The repaired path should fail closed with a specific no-material-diff/no-op reason whenever the isolated worktree has no material diff. It must never promote a write attempt or in-memory textual inequality as mission success when the repository diff is empty.

### 3. Keep the real git diff as acceptance authority

`worktree_diff` is a straightforward `git diff -- .` over the isolated worktree. No evidence currently justifies weakening this boundary. The repair should improve parsing/materialization and result classification, not bypass git-diff evidence.

## Required Lane-A regression shape

Use an unrelated temporary git repository/file, not `token_hash.py` and not `inclusive_range_count`.

At minimum prove:
1. raw valid Python source matching the prompt contract materializes and creates a non-empty isolated-worktree git diff;
2. fenced valid Python source still materializes;
3. malformed/non-Python output is rejected with no write and no fallback;
4. a no-op candidate is rejected as no material diff and is not summarized as `implement_applied`;
5. known-answer substitution remains absent;
6. primary checkout remains unchanged;
7. focused mission/runtime/worktree tests plus Ruff/mypy pass on the exact repair tip.

After source repair, execute the separately preregistered new real mission required by `V14-REAL-001-R` against a different subsystem and preserve any second failure honestly.

## Acceptance consequence

No lifecycle transition is justified by this audit alone. `ART-V14-REAL-E2E` remains drafting until Lane A supplies a green generic repair and a new independently reviewable genuine real mission satisfying `REAL_V14_E2E_PROTOCOL.md`.
