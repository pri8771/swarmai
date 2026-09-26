**Goal.** Make reservations transactional and fail-closed (ART-V23 "DispatchIntent"). Before a task is dispatched, the scheduler reserves **every** required component (provider route, worker, tool units, budget). If any reservation fails, everything already reserved is released and the intent ends `COMPENSATED`. Intents are idempotent per `attempt_id`, have a TTL, and expired `PREPARED`/`RESERVED` intents are released on restart. `DISPATCHED` intents are never auto-released.

The service does not know how to reserve capacity. It calls the injected `reserve(intent, component) -> reservation_id` and `release(intent, component)` functions, which SW-W2-S1 wires to real capacity. It persists through any `SchedulingStore` (the in-memory store from SW-W0-S2 in tests; the SQL store in production).

The code below was compiled and run against `dev + SW-W0-S2` (7 passed; ruff and mypy clean). Paste it **exactly**.

### Step 1 — `src/swarm/scheduling/dispatch_intent.py` (create, exactly)
```python
{{FILE:src/swarm/scheduling/dispatch_intent.py}}
```

### Step 2 — `tests/controller/test_v23_dispatch_intent.py` (create, exactly)
```python
{{FILE:tests/controller/test_v23_dispatch_intent.py}}
```

### Step 3 — run
```bash
uv run pytest tests/controller/test_v23_dispatch_intent.py -q     # 7 passed
```

### Section-5 acceptance
- [ ] Partial reservation failure releases every earlier reservation (pathological case: "partial provider reservation succeeds but worker reservation fails").
- [ ] Crash after reserve, before dispatch: `recover_expired` releases exactly once and never touches `DISPATCHED` (pathological case: "scheduler crashes after reservations but before dispatch").
- [ ] A duplicate `prepare` for the same attempt does not reserve again (pathological case: duplicate ticks).
- [ ] 7 tests pass.
