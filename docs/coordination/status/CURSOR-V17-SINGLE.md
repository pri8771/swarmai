# CURSOR-V17-SINGLE status

- Session: `CURSOR-V17-SINGLE`
- Epoch: `fable-v17-20260922-01`
- Branch: `cursor/v17-single-session`
- Branch SHA: `939ab596c578b083b11aa465ae6ae894d81c2905`
- Coordination SHA: `817821d0bab6c68ae1b92671b115f8be98590ebc`
- Updated: `2026-09-22T00:37:53Z`
- Trigger: `manual`
- Worker engine: `fable`
- Status: **working**
- Current packet: `R27b`
- Current artifact: `ART-V17-APPROVAL-BINDING`
- Last meaningful activity: `2026-09-22T00:37:52Z`
- Spend USD: `0.0`
- Blocker: EXT-ACTIONS-BILLING (apply coordination ci patch first); EXT-V14-LEAD-REVIEW; EXT-G13-*; EXT-G12-REMOTE-ROUTES; EXT-V15-SECOND-HOST

## Update

R27a impl_complete: pushed 0505c24 (feat) + 939ab59 (receipt bind). action_receipts migration a17effect004b0001, insert-only receipts, replay returns original receipt. 6 integration tests + full suite 400 passed/2 skipped on real Postgres. Starting R27b atomic reserve/CAS.

## Next

R27b atomic reserve + compare-and-swap execute
