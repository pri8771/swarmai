# Codex assignment — V1.7 isolated composition tip

Owner target: V1.7 only.
Integrator: Codex.
Authority: docs/coordination/V17_BLOCKER_CLEARANCE_DISPOSITION_20260922.md

Create one isolated composition branch/worktree. Do not touch main.

Exact order:
1. base fb58a751d40f1828990d7a0d687ad30de6eb6103;
2. semantically apply accepted P0 11bd4b5276458b2b7adc11528f117e919524f035;
3. apply accepted lint 349c732c335d83eaa431d30ea7f2b52b8d4431a3;
4. add the released make_approval payload-integrity follow-up;
5. semantically port accepted R02c 1c9ff44ec787508fb874f5ac7fde849f89bdfe42.

R02c worker.py overlap requires semantic review, not blind cherry-pick. Preserve the current worker architecture and add only: wrong-file EDIT rejection before write; exact-match behavior; exact indentation/no-fence prompt guidance; no fuzzy match/reindent/known-answer behavior.

make_approval follow-up: after context authorization and before ensure_hashes/grant/store, run the same canonical payload-integrity check. Add negatives for stale payload/destination hash creating no approval; empty hash and valid custom effect key remain valid.

Verification on the exact composition SHA:
- focused P0 + R28d admission + R02c + approval-integrity tests;
- full offline;
- full owned PostgreSQL with cleanup/public-table report;
- Ruff + format check;
- mypy;
- public Actions status if triggered, but PG is still mandatory locally/owned.

Do not merge main. Do not run model/provider/session/network/live/public actions. Do not create a watcher/timer. Return READY_FOR_LEAD_REVIEW with exact SHA/tree/base, semantic-conflict notes and evidence.
