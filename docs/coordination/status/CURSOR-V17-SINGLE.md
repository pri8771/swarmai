# CURSOR-V17-SINGLE status

- Session: `CURSOR-V17-SINGLE`
- Epoch: `fable-v17-20260922-01`
- Branch: `cursor/v17-single-session`
- Branch SHA: `c25182dfa5b03f3b9a4409282b6ea465484fe79f`
- Coordination SHA: `a780d588818ed52c91dac03a3a95b24dc4e8e8b5`
- Updated: `2026-09-22T01:33:04Z`
- Trigger: `manual`
- Worker engine: `fable`
- Status: **working**
- Current packet: `R02a`
- Current artifact: `ART-V14-REAL-E2E`
- Last meaningful activity: `2026-09-22T01:33:03Z`
- Spend USD: `0.0`
- Blocker: REV-R27C (lead diff review before R27e/R28a); EXT-ACTIONS-BILLING; EXT-V14-LEAD-REVIEW; EXT-G13-*; EXT-G12-REMOTE-ROUTES; EXT-V15-SECOND-HOST

## Update

R17a live_checkpointed: CP3 run cp3-20260922T013226Z on e5bd635 — 9/9 requirements incl. cancellation_generation_stale fence and 20/20 concurrent duplicate-accept iterations across spawned processes; evidence commit c25182d. Finding: cancel_active_lease does not bump durable mission generation (follow-up packet). Next: R02a red->green defect-proof gate.

## Next

R02a prove_defect gate; then R30a fixture; REV-R27C still gates R27e/R28a
