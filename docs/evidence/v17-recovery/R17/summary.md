# R17 — CP3 separate-process recovery

## Result

Added `scripts/r17_cp3_separate_process_recovery.py` and ran live local CP3:

- register + claim in victim OS process
- SIGKILL victim
- expire/reassign
- survivor process submits valid result
- stale accept rejected (`lease_not_current:expired`)
- exactly one accepted result; competing stale accept rejected (`result_terminal:rejected`)

Harness pytest also green (simulated single-process suite).

`live_multi_host_evidence=UNKNOWN` — R18 still needs a second physical host.

No invent-accept of `ART-V15-RECOVERY-EVIDENCE`.
