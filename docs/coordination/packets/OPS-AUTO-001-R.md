# OPS-AUTO-001-R — repair autonomous worker source baseline

Artifact: `ART-OPS-AUTONOMOUS-WORKERS`
Owner: Cursor Session A / HOST-MAC-DEV
Complexity: SP1
Intended artifact transition: `drafting -> drafting` with the current source/CI blocker removed so host execution proof can begin. This packet alone does **not** verify the autonomous-worker artifact.

## Context

The first repo-driven autonomous-worker source landed on both active worker branches, but exact-tip CI is red. On `cursor/v2-runtime-lane@1e4b560a2cd1e4285222452a6839a5a5cc5b4c60`, Actions run `35558067148` fails at Ruff with 32 findings in the new coordination scripts. The console job is green; later offline checks were skipped. The same shared source causes `cursor/v2-product-lane@6b0e1277051ae90fe1d56825d3e771b042380755` run `35558073323` to fail at Ruff.

Observed classes include E501 line-length findings in `scripts/coordination/autonomous_worker.py` and F841 unused `last_sent` in `scripts/coordination/heartbeat.py`.

No repo-assigned autonomous packet self-launch has been proven yet. Scheduler heartbeats are separate liveness evidence and do not satisfy this artifact.

## Work

1. Repair the Ruff findings in `scripts/coordination/autonomous_worker.py` and `scripts/coordination/heartbeat.py` without changing the safety semantics below.
2. Add/extend focused deterministic tests for the runner where practical, especially:
   - only one packet selected per invocation;
   - completed `(assignment_id,generation,item)` is not rerun;
   - a started-but-not-completed item waits for a new generation;
   - dirty/wrong branch fails closed;
   - no remote branch advancement is a blocked result;
   - assignment host/session/branch mismatch fails closed.
3. Preserve: no force push, no destructive reset/clean/stash, no secrets in Git/logs, one bounded agent invocation, no self-acceptance, and explicit generation change for retry after blocked/failed execution.
4. Run at minimum:
   - `uv run ruff check scripts/coordination`
   - focused coordination tests added/affected
   - `uv run ruff check .`
   - `uv run mypy src/swarm`
   - relevant offline pytest
5. Commit/push only Session A's repair. Do not merge main or integrate unreviewed application work.

## Required evidence

Return/push:
- exact source SHA;
- exact test commands and exit results;
- GitHub Actions run for the repaired exact tip;
- changed-path list;
- statement confirming no autonomous packet was counted as successfully self-launched unless a real daemon invocation produced `autonomous_start`/review evidence and a remote source change.

## Acceptance for this packet

Lead can accept this SP1 packet when the source is lint-clean, the safety behavior is preserved by source/tests, and exact-tip CI no longer fails because of the autonomous-worker implementation. Parent `ART-OPS-AUTONOMOUS-WORKERS` remains `drafting` until both A and B each independently self-launch one repo-assigned packet and push attributable evidence without a human prompting the Cursor conversation.
