# R28d live-local run `r28d-live-local-20260922-01`

Status: **REWORK_FOUND**

Classification: `live_local` failure record; this is not checkpoint evidence.
Assignment consumed: `CODEX_R28D_LIVE_LOCAL_20260922.md` released exactly one
mission from source `6dbf8c43463cbdbd8c87561af2abcdde59969765`.

## What ran

One real `MissionRuntime.run` invocation ran in the owner-authorized R730
one-shot environment. It used the existing local Ollama route and model
identified in `manifest.json`, with paid fallback disabled. No scheduler,
public action, credential change, external mutation, model download, or retry
was introduced.

The local model route was reached before the first worker write. The product
then raised `RuntimeError: sync_call_inside_running_loop`; see
[`trace.txt`](trace.txt). The crash happened before a finalized mission record
or cost ledger could be persisted.

## Result and evidence boundary

- `action_receipt_ids`: `[]`
- `ActionReceiptV17` count: `0`
- final `MissionRecord`: absent
- request count: `UNKNOWN` — the exception prevented final accounting
- recorded cost: `UNKNOWN` — the exception prevented final accounting
- no file-change or command-receipt coverage exists

Therefore this record does **not** satisfy R28d, ART-V17, CP1, or a live
checkpoint. It preserves the failed source/run rather than backfilling a
result from host logs or a manual effect.

## Causal map

1. `MissionRuntime.run` owns an asyncio event loop.
2. The released runtime synchronously called `RepoWorker.run_task` on that
   loop.
3. The worker's first write reached
   `ConsequentialToolGateway.execute_envelope_sync`.
4. The gateway correctly refused a synchronous call inside a running loop.
5. The exception also prevented the worker from returning its created
   worktree handle, so the normal runtime cleanup had no handle to remove.

The narrowly scoped repair is source
`codex/swarm-r28d3-async-gateway-20260922@e87c5233699bbc44c24ef3ec1872a8649546c669`.
It has no release to make another live invocation. Its separate request for
independent exact-SHA review is
[`CODEX_R28D3_ASYNC_RUNTIME_REPAIR_REQUEST_20260922.md`](../../../../coordination/reviews/CODEX_R28D3_ASYNC_RUNTIME_REPAIR_REQUEST_20260922.md).

## Cleanup

The failed runtime had created one child Git worktree. Its throwaway directory
and transient branch were removed after the failure; the primary source ended
clean. The repaired source adds an adverse regression for this lost-handle
cleanup path. A later cancellation/concurrency race remains a separate
follow-up, not a reason to treat this failed run as complete.
