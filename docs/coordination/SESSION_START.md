# SwarmAI session start — delivery mode

Repository: `pri8771/swarmai`.
Coordination: `coordination/swarm-control`.
Application source: current `origin/cursor/v17-single-session`.
ChatGPT is lead/reviewer. Fable is the worker for the newly requested delivery run.
The old Cursor process must relinquish ownership before Fable takes over; this document does not prove that local handoff occurred.

## Read once

1. `docs/coordination/FABLE_DELIVERY_CONTRACT.md` — active execution assignment through V3.0, priority real V1.7 closure.
2. `docs/coordination/EXECUTION_CONTROL.json` — additive dependency/gate corrections over existing queues.
3. Current `status/CURSOR-V17-SINGLE.md`, latest heartbeat record in `heartbeats/CURSOR-V17-SINGLE.json`, and latest relevant lead review.
4. Only the selected packet card and the interface/source files it consumes. Use `DOC_ROUTER.md` for on-demand references.

The earlier `FABLE_51_PLANNING_PROMPT.md` was for the completed planning pass. Do not follow its planning-only instruction for this newly authorized delivery run.

## Do not mix source and coordination

Fetch without resetting dirty work. Read coordination via `git show` or a separate coordination worktree. Do NOT merge the coordination/planning branch's stale application snapshot into current implementation.
Maintain one implementation owner and one five-minute local heartbeat producer. The historical CURSOR-V17-SINGLE stream may be reused with an explicit Fable takeover receipt and new epoch; do not create an overlapping stream.
A fresh daemon tick is not evidence of active coding. Inspect last meaningful activity and the actual worker/long-job process.

## Select work

Existing packet graphs remain canonical:
- V1.7: `V17_RECOVERY_PACKET_QUEUE.json`.
- V1.8–V2.3: `V17_TO_V23_PACKET_QUEUE.json`.
- V3: `FUTURE_EXECUTION_GRAPH_V18_TO_V30.json` → `v30_packets`.

From a coordination worktree:

```sh
python3 docs/coordination/tools/validate_plan.py --json
python3 docs/coordination/tools/execution_guard.py --phase v17 --json
python3 -m unittest discover -s docs/coordination/tools -p test_execution_guard.py -v
```

The original validator checks structural coverage. The execution guard additionally applies lead dependencies, holds and live prerequisites; neither grants permissions or accepts artifacts. Read `EXECUTION_CONTROL.json` and actual packet evidence if the outputs differ.

Resume genuinely active work first. Otherwise select one dependency-ready packet. A `preflight_only` result permits a read-only prerequisite check, not mutation. Do not mark evidence_only or review_pending as a passed live checkpoint. Independent review and lead-owned decisions may be prepared as evidence bundles but cannot be decided by the worker.

## Delivery order

Repair CI/heartbeat churn and durable action correctness first. Finish actual mission/worker/knowledge/action wiring, then CP1/CP3/CP4/CP5, the real GitHub R33c checkpoint and integrated CP6. Continue through V1.8/V1.9/V2.0/V2.3/V3.0 as their hard dependencies and review/freeze gates become satisfied; do not ask routine version-start questions.

Do not wait on an unrelated external blocker while an independent packet is executable. Preserve all failed evidence, exact tested source identities and full diffs before cleanup. Keep no-main-merge, no-public-release, no-extra-spend, no-secret-in-Git and no-self-acceptance boundaries.

## Status authority

`ARTIFACT_REGISTRY.json` controls artifact acceptance; fresh source, executed commands and receipts support claims. Queue statuses are engineering progress, not acceptance. Old branch labels or memories cannot establish current version truth.
Relevant memory/history explains intent only. Claude may not have ChatGPT conversation access; use repo memory/decisions when it does not.

Return one pushed candidate and a concise checkpoint/evidence/blocker report, not another broad roadmap. See `FABLE_DELIVERY_CONTRACT.md` for exact finish conditions.
