> **Latest owner assignment — 2026-09-22:** GPT-6 Sol in a new Codex task is the next SwarmAI implementation owner; target accepted LIVE V1.7. Read `docs/coordination/OWNER_RACE_V17_20260922.md` and `docs/coordination/GPT6_SOL_SWARM_V17_RACE_20260922.md` first. State: ASSIGNED_WAITING_FOR_WORKER, not launched. This supersedes older worker/pause routing below only; existing evidence, review holds and action grants are unchanged. No new scheduler or watcher.

# SwarmAI delivery contract — V1.7 LIVE ONLY

Status: ACTIVE OWNER SCOPE: OWNER_V17_LIVE_ONLY.
Latest instruction: "Lets focus on getting to 1.7 live and thats it."
This supersedes all earlier continue-through-V3 launch instructions and historical scope fields. It narrows work, not evidence requirements.
ChatGPT = engineering/product lead and independent reviewer. Fable = implementation worker. Operator = final authority.

## 1. One goal and a hard stop

Deliver a genuinely running, private/local V1.7 candidate with source-bound operational and real-world checkpoint evidence. Repair required lower-version prerequisites as necessary. Do not implement, redesign, expand roadmaps or select tasks for V1.8, V1.9, V2.x or V3.0. Existing future plans remain parked, not deleted.

After the V1.7 live handoff/review package, STOP implementation. Successful V1.7 does not authorize another version. Continue only after a new explicit owner directive.

A missing prerequisite is still a blocker. Do not hide an unmet lower-version gate by declaring a narrower demo to be V1.7. Local operational proof, real-world checkpoint proof, independent verification and formal artifact acceptance are separate claims.

## 2. Correct source and efficient startup

Repository: `pri8771/swarmai`.
Application branch: current `origin/cursor/v17-single-session`.
Coordination: `coordination/swarm-control`.
Last fetched application snapshot during this scope change: `f2b8d5f7dfd65530e73c63438c229b9fa428f922`; re-fetch, never reset to this historical SHA.

Fetch without losing dirty work or another session's changes. Read root CLAUDE.md, SESSION_START.md, this contract, EXECUTION_CONTROL.json, current status/heartbeat and latest relevant lead review. Then read ONLY the selected packet card and required source/interfaces. Access memory/history only when genuinely available; otherwise use repo memory/decisions. Do not claim Claude can retrieve ChatGPT's private conversations.

The planning/coordination branches contain older application snapshots. Never merge their application trees into current implementation. Use `git show` or a separate coordination worktree for instructions. Do not open all future roadmaps at startup.

Existing `V17_RECOVERY_PACKET_QUEUE.json` remains the queue; do not create another master plan. EXECUTION_CONTROL adds required dependencies and restricts selection to `allowed_phases=["v17"]`.

From a coordination worktree:
```sh
python3 docs/coordination/tools/execution_guard.py --phase v17 --json
python3 -m unittest discover -s docs/coordination/tools -p 'test_*guard.py' -v
python3 -m unittest discover -s docs/coordination/tools -p test_v17_scope.py -v
```
The structural validator remains available for a targeted consistency check; its old ready-set output does not override scope, review or live execution gates. No tool output grants external permission.

## 3. One worker and one truthful heartbeat

Inspect actual local implementation processes before takeover. Reuse an already active Fable session; otherwise obtain a clean Cursor-to-Fable handoff. Do not kill unrelated processes, touch other projects, or race an existing writer.

Reuse the historical stream `heartbeats/CURSOR-V17-SINGLE.json` and `status/CURSOR-V17-SINGLE.md` for compatibility. Record actual worker engine, session epoch and takeover source SHA. Preserve history. Do not install another producer just to rename the stream.

Exactly one local five-minute heartbeat producer while the worker session is active. It must report packet, artifact, source SHA, current command/test activity, blocker and next step. Keep publication time separate from last meaningful activity. A timer may not turn an idle/blocked/stopped worker into working. Verify long-running tests by their real process/logs. A heartbeat does not wake an inactive model or prove completion.

First repair heartbeat-only CI churn under OPS-CI-01. Keep CI on code/security/workflow changes. Do not raise billing limits or spam Actions reruns; locally executed checks and hosted CI are distinct evidence.

## 4. Small artifact packets, not another planning pass

Use the existing dependency-ready micro-packets. Initial priority after reconciling current evidence: OPS-CI-01 -> R27a -> R27b -> R27c -> R27d. Observe independent review holds before R27e/R28a. Useful independent work while reviews wait includes R30a, R17a and R02a.

For each packet:
1. Inspect existing code. Re-verification of earlier code is not a new feature.
2. Record the exact required behavior, allowed surfaces, dependencies and relevant regression.
3. Implement one bounded concern, usually 1-3 production files plus focused tests. Split a genuinely broader change into named child packets; do not hide work to meet a line limit.
4. For defect repair, prove a relevant regression fails on old source and passes on the fix. Do not seed a fake defect or supply a held-out answer.
5. Run focused tests, relevant real PostgreSQL/process integration and configured lint/type checks. Distinguish passed, failed, skipped, not-run and infrastructure-blocked.
6. Commit/push source before counted live evidence. Preserve full diff, commands, outputs and receipts BEFORE cleaning the worktree. Record tested source SHA separately from evidence-packaging SHA.
7. Update progress and heartbeat; continue the next ready V1.7 packet. Two repeated attempts with no new diagnostic evidence require a small diagnosis/repair packet, not a third blind retry or relaxed success criteria.

Do not author a lead review, self-set verified/accepted, overwrite failures, or expand permissions. Proposed implementation-detail splits must preserve contracts and review holds.

## 5. What must actually work

The same operational product path must connect the broker, durable worker leases/results, scoped knowledge and the durable action gateway. Standalone classes and test-only entrypoints do not count.

| Checkpoint | Required proof |
|---|---|
| CP0 | Exact tested-source health; configured test/lint/type results and hosted-CI status reported separately. |
| CP1 | Real unfamiliar task; real brokered inference; a defensible defect/fix, focused red-to-green proof, isolated diff and independent semantic review; no primary-checkout auto-apply. |
| CP2 | Actual qualification/provider prerequisite evidence under existing frozen rules. Missing sealed material, entitlement or required host verification stays explicit. |
| CP3 | Durable worker on a real operational mission; actual separate processes; kill/expiry/reassignment; cancellation rejection; genuinely concurrent duplicate-result attempts; one accepted result. Required physical multi-host evidence is not replaced by aliases. |
| CP4 | Actual mission context uses permission-first retrieval; two-project content/existence isolation; reuse, supersession/deletion including after restart; source-bound retrieval receipts and honestly labeled token accounting. No invented quality gain. |
| CP5 | Local, API and session integration semantics through the same durable gateway; negative tests, recovery, replay and unknown-outcome reconciliation. Local fixtures prove mechanics only. |
| CP5-REALWORLD / R33c | Reversible real external GitHub issue/comment/close test THROUGH SwarmAI, observed after mutation, with stable effect keys and no duplicate mutation on replay. |
| CP6 | Exact-tip integrated mission showing all receipt families on the real path; cancellation/restart tests; user-accessible private/local running candidate; complete checkpoint and open-gate matrix. |

R34a requires R17c actual separate-process/API worker wiring. R34b also requires R33c, R17c and R27d. Do not skip approval immutability/revocation, real external proof, or worker integration because a parent is called evidence_only.

An internal effect key is not universal exactly-once delivery to every external service. After an ambiguous send, persist UNKNOWN and reconcile rather than resend under a new key. Committed begin_execution is the authorization admission point: cancellation before it denies admission; later cancellation may race an already-admitted remote action and requires honest reconciliation. A cookie HTTP test is not proof of browser/UI automation; exercise an actual browser when making a browser support claim. Do not bypass prohibited SSO/MFA/CAPTCHA flows.

## 6. Real service, identity and access

No new account is needed for the preferred GitHub checkpoint. Probe the actual host's existing `gh` authentication and private-repo access read-only. ChatGPT connector access does not prove local `gh` authentication.

Use one uniquely named `[SwarmAI LIVE TEST] <run-id>` issue in private `pri8771/swarmai`; create, observe, comment once, close and replay through SwarmAI's approved durable action boundary. Cleanup is also a receipt-backed action. Direct connector/manual `gh` mutations outside SwarmAI are not product proof. No tokens/cookies in prompts, logs or Git.

The operator's earlier permission to use an existing suitable account or necessary unsubscriber Google Cloud email alias remains conditional on a genuine V1.7 identity test. Verify the configured mechanism; do not invent an alias service, perform bulk/public actions, or create accounts merely for a checklist. Request only the exact unavailable login/MFA/consent step.

"Live" means running in the existing authorized local/private environment, not public release. At handoff give the real application URL/port, exact start/restart/stop commands, tested SHA, process/service identity and sanitized log location. Confirm reachability from the execution host and state honestly whether owner-side reachability was tested. Do not promise a remotely usable localhost URL. Do not expose a new public listener, create infrastructure or incur spend.

## 7. Reviews and blockers without idle work

Preserve existing safety-critical review holds. Package exact diffs, regressions, source identities and decision requests for ChatGPT. A worker may prepare an audit bundle but not decide its own independent review.

For an external/review/time blocker record: affected packet/checkpoint, actual probe/error, required human/lead action, descendant impact and next independent V1.7 packet. Missing credentials block the real call, not writing its adapter/tests. Review holds block protected dependants, not unrelated tasks. Continue all genuinely executable in-scope work.

Do not shorten or backfill required wall-clock evidence, waive sealed-reference requirements, or mark blocked tests as passed. Narrowing to V1.7 does not remove its canonical lower gates. If all in-scope executable work is exhausted, report BLOCKED_FRONTIER with exact needs; do not continue into V1.8 or invent completion.

No main merge, public tag/release/deployment, destructive production operation, paid fallback or additional spend. Keep SWARM_ALLOW_PAID=false.

## 8. Final handoff, then STOP

Return:
- implementation branch and exact pushed source SHA;
- running private/local application URL, launch/restart/stop commands and reachability evidence;
- CP0-CP6 and CP5-REALWORLD matrix: result, evidence path, tested SHA, independent-review status and open gates;
- meaningful source changes versus re-verification-only work;
- actual test counts, failures, skips and not-run checks;
- remaining prerequisite/review/account/host/time blockers and their affected claims;
- heartbeat owner/state and last meaningful activity;
- READY_FOR_LEAD_REVIEW, or BLOCKED_FRONTIER if required work cannot proceed.

Leave the product running where safe and authorized; stop the implementation heartbeat or mark it stopped when the model session ends. Do not imply continuing work from a timer alone. No future-version tasks or new roadmap. A V1.7 success report is not permission to begin V1.8.
