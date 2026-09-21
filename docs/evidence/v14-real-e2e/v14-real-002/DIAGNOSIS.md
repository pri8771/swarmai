# v14-real-002 diagnosis (fail-closed)

**Status:** failed / accepted=false / summary=`repair_required`  
**Mission:** `18b9b59bd8a8479cb2152c13d3240d1b`  
**Run tip:** `17bf3a1c939df291023048b59bfcec6c2805eae6`  
**Spend:** $0.00 (local Ollama `qwen3.5:4b` via broker)

## Root cause

1. `RepoWorker._implement` requested `max_tokens=800` (`src/swarm/mission/worker.py` at run tip).
2. Broker receipts show `completion_tokens=800` exactly (×3) — generation truncated at the cap.
3. Model output opened a Markdown fence (`` ```python ``) and never closed it (text ends mid-comment).
4. `_extract_python_file` at run tip only accepted **closed** fences (`re.search(r"```(?:python)?\n(.*?)```", ...)`), so extract returned `None`.
5. Operational path correctly refused known-answer `GOOD_FIX` → `implement_failed_no_known_answer_fallback`.
6. No write → `changed_files=[]` → review reject (`no_material_diff`, `implementation_missing`).

This is **not** a materialization empty-diff after write; the parser never produced a candidate file.

## Proposed repair (already on branch tip; does not pass this run)

Commit `4224b9071360d52a8593f4b8cd16485d13778f80`:
- accept unclosed/truncated fences when body looks like Python;
- raise implement `max_tokens` to 4096.

A **new** preregistered freeze/run is required after lead authorization. Do not rewrite or re-label v14-real-002 as success.

## Evidence bind

See `bind.json` (content digests) + `manifest.json`.
