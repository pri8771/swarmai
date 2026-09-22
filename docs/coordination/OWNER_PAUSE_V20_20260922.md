# Owner pause and target reset — 2026-09-22T17:32Z

Latest direct owner instruction: "Okay, take a break. tell me where you are, what youve done, and where we need to be. Lets reset, and set the target to 2.0 across the board. update the repo, with anything important, and give a prompt for Claude."

**Current target: V2.0 for Jobs Automation, SwarmAI and Social Bots. Current work state: PAUSED_BY_OWNER.** This supersedes the earlier V2.3 floor/V2.7 target and all older per-project ceilings. V2.3/V2.7 work and proposals are deferred. Existing accepted source/evidence remains valid within its actual scope; no version acceptance is granted by this reset.

Codex stopped implementation and test execution on receipt. Only checkpointing existing work, native records, completed review submissions and the requested Claude prompt continued. No automatic Claude/Fable dispatch. Resume implementation only when the owner resumes it or explicitly starts the continuation prompt. Existing worker/heartbeat/scheduler ownership is preserved; no timers were changed.

All live/account/model/mailbox/browser/application/public/scheduler/spend/deploy/main-merge grants remain closed unless separately and explicitly granted. Earlier consolidated request is still pending and should now be narrowed to the V2.0 critical path. Keep repositories, queues, credentials, runtime, budgets and evidence separate. ChatGPT native leads retain acceptance; never self-accept.

## Swarm checkpoint and V2.0 path

Admission repair fb58a751d40f1828990d7a0d687ad30de6eb6103, tree4fd0b56f909c8026e4893540d587d93d5180c73b, is clean and pushed in draft PR27. Results:628 PostgreSQL passed/13 live-UI skips;431 offline passed/210 skips;23 focused PostgreSQL; cleanup0; mypy174 clean; changed-file Ruff clean. Full Ruff retains inherited api/store.py I001. Independent recommendation exists; formal verdict was pending at pause. Native packet CODEX_ASTRA_ADMISSION_REPAIR_20260922.md atd40d571. Hosted CI cannot start runners due billing; not green.

R30b diagnostic was accepted. Contracte736ab7 and explicit P0 assignment9c912f4 release the shared prerequisite only. **P0 is UNCOMMITTED, UNREVIEWED and INCOMPLETE at owner pause.** Worktree /tmp/swarm-astra-r30b-prerequisite-20260922, branchcodex/swarm-r30b-prerequisite-20260922, base accepted6dbf8c43463cbdbd8c87561af2abcdde59969765. Modified production files: contracts/actions.py and tools/v17_gateway.py. Two new tests cover stale hashes and durable execution-attempt context.

Corrected new offline tests:6 failures on the exact accepted baseline,6 passes on WIP. Initial fixture mistakes (missing StaticFenceProvider arguments and assertions against a nonexistent row idempotency field) were corrected; raw failures remain. **The PostgreSQL restart/attempt test is written but NOT RUN. No full suite, mypy, final Ruff, independent review, source commit/push or PR has been completed for P0.** This separate branch does not include admission repairfb58a751. Do not carry acceptance or checks between the two branches.

Recovery source copies, tracked patch, logs and hashes: evidence/CODEX-R30B-P0-PAUSED-20260922. Prefer resuming the existing dirty worktree after comparing hashes. Do not blindly apply the snapshot or alter the original worktree during the pause.

On resume, finish P0 verification and review within its assignment. Product HttpApiAdapter remains held until prerequisite acceptance; all live grants stay closed. V2.0 requires accepted lower-version missions, workers, knowledge, tools, recovery and extensions on one CandidateManifest; migrations/install/upgrade/rollback, security/performance and genuine elapsed reliability evidence; independent release review. Read MASTER_PLAN_V17_TO_V30_20260921.md (V2.0), FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md and docs/artifacts/future/ART-V20-ACCEPTANCE.md. V2.3/V2.7 are deferred.
