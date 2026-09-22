# CURSOR-V17-SINGLE status

- Session: `CURSOR-V17-SINGLE`
- Epoch: `fable-v17-20260922-01`
- Branch: `cursor/v17-single-session`
- Branch SHA: `1bbf316a0b370c29299f0b91205ffdf2d85bae67`
- Coordination SHA: `310f3344678361e2e336d9b32adf74a4fcc87b8c`
- Updated: `2026-09-22T01:29:15Z`
- Trigger: `scheduler`
- Worker engine: `fable`
- Status: **working**
- Current packet: `R30a`
- Current artifact: `ART-V17-INTEGRATION-MANIFEST`
- Last meaningful activity: `2026-09-22T01:27:13Z`
- Spend USD: `0.0`
- Blocker: REV-R27C (lead diff review before R27e/R28a); EXT-ACTIONS-BILLING; EXT-V14-LEAD-REVIEW; EXT-G13-*; EXT-G12-REMOTE-ROUTES; EXT-V15-SECOND-HOST

## Update

R27d impl_complete: pushed 1b9afc5 (feat) + 1bbf316 (bind). Approvals insert-only, monotonic revocation, project-filtered reads, legacy NULL rows non-operational. 6 tests; full suite 422 passed/2 skipped. R27 chain a-d done; REV-R27C hold gates R27e/R28a. Taking independent R30a (live fixture service).

## Next

R30a live local fixture service + markers; then R17a CP3 gaps; R02a defect-proof gate
