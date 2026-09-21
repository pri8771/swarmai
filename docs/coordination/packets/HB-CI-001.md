# HB-CI-001 — restore green CI after heartbeat cadence fix

- Artifact: `ART-OPS-HEARTBEAT`
- Primary worker: Cursor A / HOST-MAC-DEV / `cursor/v2-runtime-lane`
- Follow-on consumer: Cursor B / HOST-WIN-DEV / `cursor/v2-product-lane`
- Story points: SP1
- Priority: before new source packets on either lane because both current lane tips are red for the same coordination-only lint defect.
- Intended artifact transition: remain `drafting`; this packet only restores the heartbeat client's test/CI integrity.

## Reproduced failure

Current Session-A tip `24bdebc8ac34ddc43b584abb6cadaea22ee88d94`, Actions run `35555814857`, fails the offline job at:

```text
F841 Local variable `last_sent` is assigned to but never used
scripts/coordination/heartbeat.py:169
```

Session-B tip `4bf2523053b836dfa60395c3e6df7c5539f760e3` is derived from the same heartbeat-client change and its exact-tip Actions run `35555818627` is also red.

## Required repair

1. In Session A, remove the dead `last_sent` assignment or use it only if semantically required; do not reintroduce manual-heartbeat timing into scheduler cadence logic.
2. Preserve the intended fix: scheduler publication must be governed by `last_scheduler_sent_epoch`; manual/forced packet heartbeats may not reset/suppress the scheduler's 15-minute proof clock.
3. Run at minimum:
   - `uv run ruff check scripts/coordination/heartbeat.py`
   - any existing heartbeat unit/regression tests;
   - full relevant lane CI.
4. Push one coordination-only repair commit from A and return exact SHA/CI.
5. Session B then imports that exact reviewed coordination-only repair (or the equivalent commit with identical blob) and reruns its exact-tip CI; do not independently diverge the shared heartbeat client.
6. Reinstall the corrected scheduler on both hosts after pulling the repaired script. Actual scheduler-triggered heartbeat timestamps, not CI, determine heartbeat proof.

## Acceptance

- A exact-tip offline/console CI green after repair;
- B exact-tip offline/console CI green after importing the same heartbeat fix;
- heartbeat script still isolates scheduler cadence from manual updates;
- no claim that scheduler heartbeats occurred merely because the script/CI passes.

This packet does not satisfy `ART-V10-WORKER-HEARTBEAT`, does not graduate heartbeat cadence, and does not alter V1.4/V2 source acceptance.
