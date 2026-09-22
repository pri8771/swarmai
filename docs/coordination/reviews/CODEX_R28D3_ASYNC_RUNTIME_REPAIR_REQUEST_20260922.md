# R28d-3 async runtime repair — review request

Date: 2026-09-22

Author status: **READY_FOR_LEAD_REVIEW**
This is a request for independent review, not a lead review or acceptance.

## Exact source

- Repair branch:
  `codex/swarm-r28d3-async-gateway-20260922@e87c5233699bbc44c24ef3ec1872a8649546c669`
- Base accepted R28d-2 source:
  `6dbf8c43463cbdbd8c87561af2abcdde59969765`
- Scope: async runtime-to-worker bridge, lost-worktree cleanup fallback, and
  focused regressions only.
- Unrelated `src/swarm/api/store.py` import ordering is intentionally excluded.

## Reproduced product failure

The one source-bound R28d `live_local` invocation was made from the accepted
base and failed with `RuntimeError: sync_call_inside_running_loop` before a
final mission record or action receipt. The immutable failure bundle is
[`r28d-live-local-20260922-01`](../../evidence/v17-recovery/R28d/r28d-live-local-20260922-01/).

It also exposed a cleanup defect: a worktree created inside the synchronous
worker was unavailable to `MissionRuntime` if the worker threw before returning
its normal `(result, handle)` tuple.

## Repair and requirement map

| Requirement | Evidence on `e87c523` |
|---|---|
| Preserve `execute_envelope_sync` fail-closed loop guard | Runtime calls the serial sync worker via `await asyncio.to_thread(...)`; gateway code is unchanged. |
| Exercise an async operational runtime path through the real sync gateway | `test_runtime_runs_gateway_backed_sync_worker_off_loop` writes four real local-sandbox effects and asserts four receipt IDs. |
| Remove a worktree created before a worker throw | `RepoWorker` retains its active handle before adapter binding; runtime finally removes the returned or retained handle. |
| Prove cleanup on the lost-return path without a model substitute | `test_runtime_removes_worktree_when_gateway_binding_raises` uses a real temporary Git repository and `RepoWorker`, injects the bind failure, and proves the disposable path and branch are gone. |
| Keep work isolated and never auto-promote | No apply/promotion path changed. |

## Regression evidence

The new two-test regression was copied unchanged onto the exact old source in
a disposable worktree:

- old source `6dbf8c4`: **2 failed** — the bridge test observed the running
  event loop and the cleanup test observed the leaked worktree;
- repair `e87c523`: focused gateway/runtime checks **12 passed**;
- repair `e87c523`: full offline suite **423 passed, 208 skipped**;
- repair `e87c523`: `uv run mypy src/swarm` **clean (174 files)**;
- repair `e87c523`: changed-file Ruff and `git diff --check` **clean**.

`uv run ruff check .` remains **one failure** in the base's unrelated
`src/swarm/api/store.py` import order. It is not claimed green and is not part
of this repair.

## Review boundary and next action

The original R28d assignment explicitly allowed **one** invocation and it has
been consumed by the failed run. This repair does not authorize a retry.

If an independent lead accepts this exact source, the lead must issue a new
exact-SHA successor assignment before any further `live_local` mission. No
parent R28d completion, V1.7 checkpoint, deployment, scheduler change, or
Fable handoff is asserted here.

## Recorded follow-up, outside this repair

`asyncio.to_thread` cannot stop a worker already running in its thread. A
future cancellation path could race runtime cleanup against that worker. No
current `MissionRuntime.run` cancellation path was found in this audit, so it
is recorded for later cancellation/concurrency work rather than broaden this
failure repair.
