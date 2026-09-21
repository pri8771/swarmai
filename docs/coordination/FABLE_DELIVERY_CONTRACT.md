# SwarmAI delivery contract — one instruction, continuous artifact execution

Status: ACTIVE LEAD EXECUTION HANDOFF, 2026-09-21.
Owner direction: execute toward V3.0; nothing is called working without relevant real-life evidence.
This is an execution assignment, NOT another whole-project planning pass.
ChatGPT is engineering/product lead and independent reviewer. Fable is the worker.

## 1. Source, scope and authority

Repository: `pri8771/swarmai`.
Continue application source from the CURRENT `origin/cursor/v17-single-session`; the reviewed snapshot was `f2b8d5f7dfd65530e73c63438c229b9fa428f922`, not a pin to reset to.
Canonical instructions: `coordination/swarm-control`.
The coordination and `fable/v3-planning` branches contain older application snapshots: NEVER merge their application trees into the worker branch or run product tests against them as the delivery candidate.
Fetch both refs; inspect dirty work, current HEAD and recent diffs. Preserve unrelated changes; no destructive reset, automatic stash of another worker's work, or force push. Use a separate worktree when necessary.

Implementation goal remains V3.0. Priority is a genuinely integrated V1.7, then V1.8/V1.9/V2.0/V2.3/V3.0 in dependency order. No routine version-by-version permission question is necessary within that scope. Hard prerequisites, explicit review holds, frozen protocols, and release/spend limits still apply.

No main merge, public release/tag/deployment, paid fallback, destructive production operation or authority expansion. Keep `SWARM_ALLOW_PAID=false`. Existing account access is not permission for unrelated public posting, applications, purchases or bulk activity.

## 2. Bootstrap once; preserve one implementation owner

Check actual local Cursor/Fable processes, local scheduler configuration and the current repository heartbeat. A fresh heartbeat timestamp alone does not prove a worker is running.
Stop/relinquish ONLY the obsolete SwarmAI implementation session and its explicitly identified producer when taking ownership. Do not terminate other projects or all Claude/Cursor processes. If another worker still owns this repository, perform a clean handoff first; do not race it.
Reuse the existing single stream `heartbeats/CURSOR-V17-SINGLE.json` / `status/CURSOR-V17-SINGLE.md` for compatibility. Its name is historical. Record `worker_engine`, a new session epoch, takeover source SHA and previous owner in a handoff receipt; do not erase history. Do not install a second producer merely to rename it.

Run one local five-minute producer only while this implementation session is active. Separate:
- heartbeat publication time;
- last real implementation/test activity time;
- process identity / long-running test identity;
- current packet and branch SHA.
A timer must not advance the real-activity timestamp. If the process is stopped/blocked, report that state instead of repeating working. A long test is progress only when its process/log/output is actually inspected. No promise that a heartbeat daemon wakes an inactive model session.

First land `OPS-CI-01` narrowly: prevent heartbeat-only commits from triggering application CI, preserve CI on code/security/workflow changes, and do not conceal required checks. Use one logical heartbeat update, not three independent CI-triggering pushes. Test path selection locally. Do not raise billing limits, enable spend or repeatedly rerun unavailable Actions.

## 3. Read the minimum necessary

Read this file, `EXECUTION_CONTROL.json`, the latest relevant lead review and current heartbeat/status once. Recover intent from memory/history only when actually accessible; otherwise use `PROJECT_MEMORY.md` and repo decisions. Never claim access to ChatGPT's private conversations from Claude.
Then read only the active packet's spec, required interface contracts and changed source. Use git diff/search; avoid rereading the full registry and V3 corpus at every packet.

Existing queues remain the ONLY task graphs:
- V1.7: `V17_RECOVERY_PACKET_QUEUE.json`;
- V1.8–V2.3: `V17_TO_V23_PACKET_QUEUE.json`;
- V3: `FUTURE_EXECUTION_GRAPH_V18_TO_V30.json`, `v30_packets` (coarse groups are not duplicate work).
`EXECUTION_CONTROL.json` adds prerequisites to those queues; it never fabricates completion.

From a coordination-only worktree, run:
`python3 docs/coordination/tools/validate_plan.py --json`
`python3 docs/coordination/tools/execution_guard.py --phase v17 --json`
`python3 -m unittest discover -s docs/coordination/tools -p test_execution_guard.py -v`
Use `--phase v23` or `--phase v30` only after verifying the corresponding source handoff and authorization conditions. Structural validation is NOT execution authorization. `preflight_only` means read-only prerequisite probes first, not permission to mutate.

If a tooling mismatch appears, repair that precise validator/schema mismatch with a regression; do not disable the guard or redesign the entire roadmap.

## 4. Execute, do not re-plan

Use one packet at a time. Verify existing source before reimplementing; a recheck of old code is useful evidence, not a newly delivered feature.
For each packet:
1. Record the artifact, precise failure/requirement, consumed interfaces, allowed surfaces and test oracle.
2. Reproduce the defect or verify the missing behavior. For a bug fix, keep a focused test failing on the old source and passing on the patch; do not create an artificial defect just to get red/green.
3. Implement the smallest change, usually 1–3 production files plus focused tests. A cross-cutting transaction may need more files; split named child packets rather than pad or hide work to meet a line limit.
4. Run focused tests, relevant integration tests, configured Ruff/mypy and affected broader tests. Distinguish PASS, FAIL, SKIPPED, NOT RUN and infrastructure failure.
5. Commit/push source before counted live evidence. Package full diffs, commands, exit codes, logs and receipts BEFORE pruning the worktree. Preserve the tested source SHA and a separate evidence-packaging SHA; documentation commits do not retroactively change which code was tested.
6. Update packet progress with source/evidence references and heartbeat. Never set registry verified/accepted or write a lead approval for your own work.
7. Re-read changed coordination only; take the next genuinely ready packet immediately.

Two attempts with the same failure signature without new diagnostic evidence trigger a SMALL repair packet, not a third blind retry or a new easier acceptance criterion. Historical failed missions remain failed. A meaningful material diff is necessary but not sufficient: it must fix the actual behavior and satisfy a relevant test.

Initial priority, subject to current evidence: `OPS-CI-01`, `R27a`, `R27b`, `R27c`, `R27d`; then `R27e` and the R28 chain after their specified review holds. Independent `R30a`, `R17a`, `R02a` can advance while a hold is pending. Do not wait on an unrelated account to write durable receipts or local test infrastructure.

## 5. Close the operational wiring, not just the libraries

V1.5: operational CLI/API missions must use durable claim, lease, cancellation and result acceptance; a standalone worker-service class is not enough. Exercise a real separate worker process, kill/reassign and concurrent duplicate result attempts.
V1.6: the actual mission prompt/context must use permission-first knowledge retrieval. Verify project isolation, lifecycle after restart, supersession/tombstone behavior, and retrieval receipts. Token estimates must be labeled estimates and compared under the same frozen method. Do not invent a task-quality gain.
V1.7: actual file writes, subprocess/API actions and session operations must traverse the durable action boundary. No in-memory operational fallback. Request input must not invent actor identity, approval, risk classification, lease generation or policy authority.

Lead dependency corrections are machine-readable in EXECUTION_CONTROL:
- R27d approval revocation/immutability is required before R27e/R28a advance.
- R34a requires R17c separate-process/API worker wiring, not only the earlier runtime library.
- R34b requires R33c real external proof, R17c and R27d in addition to its existing dependencies.
These prerequisites cannot be waived by labeling a parent packet evidence_only or review_pending.

## 6. Exact semantics to avoid impossible or misleading claims

An internal unique effect key is NOT universal exactly-once delivery to arbitrary external services. Prove one accepted internal effect and the documented external replay/reconciliation behavior. After an ambiguous send, persist UNKNOWN and reconcile; do not mint a new key and resend.

Define the authorization linearization point as the committed `begin_execution` transaction. Cancellation committed before that point must deny admission. Cancellation after admission may race an already-authorized network action; record/reconcile that in-flight action. Do not promise that a local database transaction can retract an already-sent remote side effect. Test both orderings and preserve the actual external observation.

A cookie-based HTTP session test is not proof of browser automation. Label its scope honestly. If the support matrix says browser/UI recovery works, run an actual browser on the declared workflow and preserve destination/login/no-auto-submit evidence. Do not automate prohibited Google SSO flows or bypass MFA/CAPTCHA.

## 7. Real-life checkpoints and accounts

Follow `REAL_WORLD_ACCEPTANCE_POLICY.md`. Separate unit, real-Postgres integration, live-local fixtures, real-world product execution, independent review and formal acceptance.

Required V1.7 output is CP1 + CP3 + CP4 + CP5 + CP5-REALWORLD + CP6, with CP2/other canonical lower gates reported accurately. Every required component must be ON the same operational path at CP6. Do not silently omit an unmet lower milestone.

R33c uses the existing GitHub identity ONLY after a read-only local `gh` authentication/repository probe. ChatGPT's GitHub connector does not prove the host's `gh` is signed in.
Through SwarmAI's own durable gateway, create one `[SwarmAI LIVE TEST] <run-id>` private-repo issue, observe it, comment once, close it, and prove replay produces no duplicate issue/comment. Use exact bounded approvals, stable effect keys and sanitized readback receipts. Direct manual `gh`/ChatGPT connector writes bypassing SwarmAI DO NOT count as product proof. Preserve and report any incomplete cleanup.

The owner permits an existing suitable test account or, when genuinely necessary, an account/email through the unsubscriber Google Cloud alias arrangement. First verify the actual configured mechanism without exposing secrets; do not invent an alias API, create accounts merely to decorate evidence, or make paid/bulk/public actions. Escalate only the exact unavailable consent/MFA/credential step. No new account is required for the preferred GitHub checkpoint.

For V1.8–V3 retain the real deployment recovery, fresh install, frozen reliability campaign, physically distinct fleet nodes, and real elapsed objective plus external action requirements. Simulated time and two aliases on one host do not satisfy them.

## 8. Blockers and independent review

Source authorization through V3.0 does not remove gate requirements. Existing safety-critical review holds and proposed-packet freeze points remain. Prepare exact diffs, regressions and evidence for ChatGPT; never self-author its review. An audit packet may be prepared as a worker evidence bundle, but its decision remains lead-owned.

For each blocker record: packet, condition, read-only probe performed, exact error, affected descendants, minimum human/lead action, whether retries are safe, and next independent packet. Never print secrets.
A missing credential blocks the live call, not writing its adapter/tests. A review hold blocks protected dependent integration, not unrelated work. A wall-clock campaign may run on a frozen candidate while non-conflicting work proceeds in the same worker session, but changed covered source invalidates affected evidence.

Do not shorten a 24-hour requirement, claim a future review occurred, or poll imaginary lead services. If all genuinely ready work is exhausted, stop with a precise blocked-frontier/review handoff instead of a false completion statement. If the model session ends or compacts, persist the current packet/commands/working tree/next step in repo state; never imply a stopped model is continuing merely because a timer runs.

## 9. Deliverable for this round

One pushed implementation candidate, not another portfolio of roadmaps.
Return only:
- implementation branch + exact source SHA;
- highest IMPLEMENTED / WIRED / LIVE-LOCAL / REAL-WORLD / INDEPENDENTLY VERIFIED milestone, separately;
- a checkpoint matrix with exact evidence paths, tested SHA, actual outcome, and unresolved gates;
- material source changes versus re-verification-only work;
- full test results with skips/not-run separated;
- remaining review/credential/host/time blockers and their affected packets;
- active/stopped heartbeat owner and last meaningful activity;
- READY_FOR_LEAD_REVIEW (or BLOCKED_FRONTIER if no executable work remains).

No claim that V3.0 is accepted unless the canonical registry and real evidence support every mandatory gate. One launch prompt is not a guarantee that missing credentials, independent review or elapsed-time requirements disappear.
