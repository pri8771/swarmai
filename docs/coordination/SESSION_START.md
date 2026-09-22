# SwarmAI session start — V1.7 LIVE ONLY

## Active scope

Repository: `pri8771/swarmai`.
Instructions: `coordination/swarm-control`.
Application source: current `origin/cursor/v17-single-session`.
ChatGPT is lead/reviewer. Fable is the single implementation worker after a verified local handoff.

Latest owner instruction: get V1.7 live, and nothing beyond it.
Effective authorization is `EXECUTION_CONTROL.json`: goal_version=1.7, allowed_phases=[v17]. Earlier V3 scope statements in historical STATE/registry metadata, prompts or plans are superseded for execution authorization, not evidence truth.
V1.8-V3 implementation AND future planning are parked. Do not elaborate those plans during this run. Do not automatically continue after V1.7.

## Minimal startup

1. Read `FABLE_DELIVERY_CONTRACT.md` and `EXECUTION_CONTROL.json` once.
2. Inspect latest `status/CURSOR-V17-SINGLE.md` and the latest record in `heartbeats/CURSOR-V17-SINGLE.json`; compare source SHA and meaningful activity, not just timer publication time.
3. Read latest relevant independent lead review and select one genuinely ready packet from `V17_RECOVERY_PACKET_QUEUE.json`.
4. Read ONLY its spec and consumed interfaces/source. DOC_ROUTER is a lookup index, not authorization to run future phases.

The old `FABLE_51_PLANNING_PROMPT.md` and future planning branch are historical assignments, not this run's task.

Use a separate coordination worktree or `git show`; do not reset dirty implementation work or merge the coordination branch's stale application snapshot.

## Scope-aware selection

From the coordination worktree:
```sh
python3 docs/coordination/tools/execution_guard.py --phase v17 --json
python3 -m unittest discover -s docs/coordination/tools -p 'test_*guard.py' -v
python3 -m unittest discover -s docs/coordination/tools -p test_v17_scope.py -v
```
The guard rejects v23/v30 under this scope, even if all V1.7 packets become complete. It does not need future queue files in V1.7-only mode. Do not edit the scope control to unlock future work.
`preflight_only` permits a read-only prerequisite probe, not a mutation. Structural validation cannot override scope, independent review holds or missing live prerequisites.

## Work and proof

One implementation owner and one local five-minute heartbeat producer. Retain the existing stream name with an explicit Fable takeover/epoch record rather than create a duplicate. Verify the previous process has relinquished this repo. A stopped model is not working merely because a timer keeps publishing.

Priority: CI/heartbeat hygiene -> durable effects/approval safety -> actual worker/knowledge/tool wiring -> genuine CP1/CP3/CP4/CP5 -> real external R33c -> integrated CP6. Complete required lower-version prerequisites as dictated by their contracts; no silent waiver.

Repair one small artifact concern, test, push, preserve evidence and continue the next ready V1.7 packet. Independent account/host/review/time blockers should not idle unrelated in-scope work. Do not invent evidence or bypass a review hold.

## Finish line

A running private/local candidate the owner can access through the documented environment; exact pushed SHA; real mission and recovery/knowledge/action receipts; actual external GitHub checkpoint through SwarmAI; test/checkpoint matrix and independently reviewable evidence. Provide actual URL/port, start/restart/stop commands, log/process details, and honest reachability limits. A health endpoint or fixture alone is not working V1.7.

Return READY_FOR_LEAD_REVIEW, or a precise BLOCKED_FRONTIER if required work cannot proceed. Never label a missing gate passed. Keep the application running safely where authorized; stop or accurately mark the implementation heartbeat when the model session ends. STOP at V1.7. No V1.8 tasks or new roadmap.

For a new ChatGPT lead conversation, use `V17_LEAD_CHAT_START.md`. For Fable, use `FABLE_DELIVERY_START.md`.
