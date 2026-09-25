# V1.9 autonomous pursuit evidence

**Date:** 2026-09-25  
**Branch:** `cursor/v19-pursuit-7ae9`  
**Base:** Lane C tip `origin/cursor/v18-goals-lifecycle-614f` @ `2ea1e655` (rebased; Goal schema owned by Lane C)  
**Hostname:** `swarm.splitsignal.ai`  
**Spend:** none (RecordingExecutor / fake envelopes only)

## Delivered

| Item | Status |
|---|---|
| `swarm.pursuit` package (loop, frontier, schedule, stagnation, learning, policy) | done |
| Goal integration | **Lane C schema only** — `record_mission_outcome`, `record_progress`, `apply_strategy` |
| HTTP: tick / status / lesson propose·evaluate·adopt·rollback | done |
| Deterministic pytest suite | pass |
| Rebase onto PR #46 Goal lifecycle | done |

## Commands

```sh
python3 -m pytest tests/pursuit/test_v19_pursuit_loop.py tests/mission/test_v17_protected_verify.py -q
```

## Not claimed

- Operator acceptance of V1.9
- Live model-backed pursuit cycles
- Persistent pursuit scheduler across process restart (in-memory engine state; Goal progress is durable)
- V2.0 UI/SDK wiring (Lane E)
