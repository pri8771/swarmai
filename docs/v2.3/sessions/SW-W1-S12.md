# SW-W1-S12 handoff
- Branch: `cursor/sw-w1-s12-460c`   Base SHA: `5d6fd1df11723fa84833dcf59d7fe239669685ff`   Head SHA (code): `ddab97ddf857fcdcf5de03b9bed88aa3ba404153`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S12.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- Console **Ops** tab (`apps/console/src/components/OpsPanel.tsx`): read-only scheduler queues + ops events; mock mode uses `MOCK_OPS` with a "controls disabled" note; live mode reads `/v1/ops/events` and `/v1/scheduler/queues` and never falls back to fixtures; a 404 on queues shows "Scheduler queues not available on this server".
- `WorkerControls.tsx`: drain/revoke POST `/v1/workers/{id}/drain|revoke` with the bearer token; success shows `wk → <drain_state>`; 404 shows "… not available on this server".
- `api/types.ts`, `api/client.ts`, `data/fixtures.ts` appended per prompt (existing helpers and `MOCK_SNAPSHOT` unchanged); `App.tsx` four edits (import, `'ops'` tab type, tab entry, panel block).
- `apps/console/src/ops.test.tsx` (5 new). No Python changes.
## Verification
Checks run by `/agent/wt/check.sh` on commit `ddab97ddf857fcdcf5de03b9bed88aa3ba404153` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 251 source files
alembic heads: a23opsplatform0001 (head) 
offline CI: 610 passed, 1 skipped in 37.46s
integration (Postgres): 85 passed in 21.80s
tree: 2e3af61cb6838a2bd89e7ba3d1b2e239ec5a8576 dirty=0
```
Console (`apps/console`): `npm ci` ok; `npm run lint` → 0 errors, 2 pre-existing warnings (`App.tsx` only-export-components, set-state-in-effect); `npm run test` → `Tests 26 passed (26)` (2 files; existing `src/console.test.tsx` unchanged); `npm run build` → built OK. `dist/` not committed.
## Acceptance
- [x] An **Ops** tab exists. Mock mode shows the `MOCK_OPS` events and queue and a "controls disabled" note.
- [x] Live mode reads `/v1/ops/events` and `/v1/scheduler/queues`; a 404 on queues shows "Scheduler queues not available on this server"; fixture rows never appear in live mode.
- [x] Drain and revoke POST to `/v1/workers/{id}/drain|revoke` with the bearer token; success shows `wk → <drain_state>`, and a 404 shows "… not available on this server".
- [x] The existing `src/console.test.tsx` passes unchanged; lint shows no errors.
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `npm run lint` (no errors), `npm run test`, `npm run build` pass.
- [x] No Python file changed.
- [x] Existing `src/console.test.tsx` still passes unchanged.
- [x] Mock mode renders the new UI; live mode never falls back to fixtures.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- `App.tsx` step 4: inserted the `ops` block with the file's own 6-space indentation (the prompt's block is indented as part of a markdown list).
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
