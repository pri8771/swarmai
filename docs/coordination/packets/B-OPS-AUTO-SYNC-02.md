# B-OPS-AUTO-SYNC-02 — synchronize reviewed autonomous runner repair on Windows

Artifact: ART-OPS-AUTONOMOUS-WORKERS
Lane: B / HOST-WIN-DEV
Complexity: SP1

## Goal

Bring the Windows product lane's autonomous runner/heartbeat coordination source to the independently reviewed Mac repair semantics without losing Windows-specific heartbeat/status changes.

Reviewed Mac repair:
- implementation: 0d71520de72338b3ae38dca00258a07c134e2b2a
- CI-bearing descendant: 39bba630306729b64ad4679346b1eb900f44ccaf
- CI: 35609579398 success

## Requirements

1. Preserve current Windows heartbeat scheduler, 5-minute stress-test installer behavior and human-readable heartbeat status publishing.
2. Port the reviewed fail-closed runner semantics:
   - one packet per invocation;
   - completed assignment item not rerun;
   - started-but-incomplete waits for new generation;
   - host/session/branch mismatch fails closed;
   - dirty/wrong branch fails closed;
   - no remote branch advancement is blocked;
   - no force push/destructive reset/self-acceptance.
3. Port/retain focused coordination tests.
4. Run:
   - uv run ruff check scripts/coordination tests/coordination
   - uv run pytest tests/coordination -q
5. Push exact source/evidence. Do not self-accept parent artifact.

No main merge, public deploy, spend or force push.
