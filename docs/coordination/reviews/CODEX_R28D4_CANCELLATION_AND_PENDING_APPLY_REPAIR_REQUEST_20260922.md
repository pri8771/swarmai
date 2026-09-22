# R28d-4 cancellation and pending-apply repair — review request

Date: 2026-09-22

Author status: **READY_FOR_LEAD_REVIEW**

This is an independent implementation-review request. It is not a lead
acceptance, a replacement live run, or a V1.7 completion claim.

## Exact source and boundary

- Candidate: `codex/swarm-r28d3-async-gateway-20260922@86f8e0c90e399c683d68ba9628ef48af4723f33f`
- Cancellation repair parent: `6fdb324d7741fd92db463282e4e24a953ca922a9`
- Earlier async bridge repair: `e87c5233699bbc44c24ef3ec1872a8649546c669`
- Accepted R28d-2 base: `6dbf8c43463cbdbd8c87561af2abcdde59969765`

The candidate is limited to `MissionRuntime`/`RepoWorker` interruption
semantics, revocable local effect fencing, and preservation of an accepted
`pending_apply` worktree. It does not alter model routing, live assignment
limits, external account behavior, promotion authority, scheduler state, or
the unrelated `src/swarm/api/store.py` import-order baseline finding.

## Reproduced defects and narrow repairs

| Defect | Reproduction and cause | Candidate behavior |
| --- | --- | --- |
| Cancellation could remove a worktree while the synchronous `asyncio.to_thread` worker still ran. | Cancelling `MissionRuntime.run` entered cleanup before the worker returned; a late local-sandbox write could recreate the removed path and lose its receipt. A handle created before publication could also leak. | Runtime revokes the shared fence before signaling cancellation, drains the worker thread before cleanup, persists a terminal cancelled record, and retains completed receipt IDs. The worker snapshots a fence at task start and rejects effects after revocation. |
| Accepted `pending_apply` artifacts referenced a deleted worktree. | A normal accepted mission created `record.artifacts.pending_apply`, then the unconditional `finally` deleted the same worktree before callers could use `apply_worktree_changes`. | Only a normal accepted, non-cancelled, error-free mission with an actual `pending_apply` artifact retains its isolated worktree. Failure, exception, and cancellation paths still attempt cleanup and record the outcome. Application remains explicit and requires `approved=True`. |

The pending-apply regression was first run against the pre-repair source and
failed because `handle.path.exists()` was false after a completed mission. The
candidate now proves that the primary checkout remains unchanged until the
explicit reviewed apply and that the retained worktree can then be explicitly
disposed with the existing worktree primitive.

## Engineering evidence on the candidate

| Check | Result |
| --- | --- |
| `uv run pytest -q` | `429 passed, 208 skipped` |
| `uv run mypy src/swarm` | clean, 174 source files |
| `uv run ruff check src/swarm/mission/runtime.py tests/mission/test_mission_runtime_async_worker_bridge.py` | clean |
| `uv run pytest tests/mission/test_mission_runtime_async_worker_bridge.py tests/mission/test_no_auto_promote.py -q` | `11 passed` |
| `git diff --check` before commit | clean |
| Full `uv run ruff check .` | one pre-existing unrelated `I001` import-order failure in `src/swarm/api/store.py`; not claimed green |

Independent implementation review found and then rechecked the cancellation
admission race. The final review recommendation is
**RECOMMEND_ACCEPT_FOR_LEAD_REVIEW — implementation only**. A separate
independent review of the pending-apply repair reached the same recommendation.
Neither review is a lead verdict or live evidence.

## Live evidence and release boundary

The one source-bound R28d `live_local` invocation remains the immutable failed
attempt from accepted base `6dbf8c43463cbdbd8c87561af2abcdde59969765`, recorded
at [`r28d-live-local-20260922-01`](https://github.com/pri8771/swarmai/tree/e91782593d61db36d110a3bdc85851b85bd5e6e7/docs/evidence/v17-recovery/R28d/r28d-live-local-20260922-01)
on `codex/swarm-r28d3-evidence-20260922@e91782593d61db36d110a3bdc85851b85bd5e6e7`.
It failed before a final mission record or action receipt. Its one-invocation
grant is consumed.

This candidate supplies no new model invocation, live/persistent
production-path receipt, host proof, or live acceptance. It does not authorize another live run. If the lead accepts this
candidate for engineering, the smallest next action is a new exact-SHA
successor assignment that explicitly authorizes any replacement R28d
`live_local` invocation; otherwise the repair remains review-pending.

No parent R28d completion, V1.7 live checkpoint, merge, deployment, scheduler
change, or Fable handoff is asserted.
