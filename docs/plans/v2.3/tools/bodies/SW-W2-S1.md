**Goal.** Implement ART-V23-MULTIMISSION_SCHEDULER end to end.
- Today `controller/resource_allocator.py` is a "V3.0" shim that reserves directly without a durable fair scheduler.
- This session adds `SchedulerService`, the **single dispatch authority**, composing the Wave-1 building blocks:
  - `wdrr.select_next` / `apply_selection` (SW-W1-S1).
  - `SchedulingStore`, in-memory (SW-W0-S2) or SQL (SW-W1-S2).
  - `DispatchIntentService` (SW-W1-S3).
  - `SchedulerEpochService` (SW-W1-S4).
  - `SiteAuthorityService` (existing `swarm.recovery.authority`).
  - `OpsEventLog` (SW-W1-S8).
- It proves the **11 required pathological cases** and the restart case.

**Semantics** (keep them; later sessions rely on them):
- `schedule_once(tasks)` makes exactly one decision. A process that does not hold the scheduler epoch gets `DENY / stale_scheduler_epoch` and writes nothing.
- Tasks whose `attempt_id` already has an intent are dropped, so duplicates can never double-reserve.
- A failed reservation gives `DEFER / reservation_failed`, compensates every reserved component, and changes **no** credit.
- `running` counters always equal the number of non-terminal intents; `recover()` expires stale intents, clamps positive credit, and recounts.
- `finish(intent_id)` releases reservations. It returns `accepted=False` with `stale_generation`, `stale_site_epoch` or `stale_scheduler_epoch` when the result is fenced.
- `ResourceAllocator(..., scheduler=svc)` routes through the service; without `scheduler` the legacy path is byte-for-byte unchanged, so `tests/controller/test_v23_v20.py` still passes.

The code below was compiled and run against `dev @ 8e1c0fde` plus every Wave-1 dependency. `tests/controller` gives 73 passed (17 new), the restart integration test gives 1 passed, and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/scheduling/service.py` (create, exactly)
```python
{{FILE:src/swarm/scheduling/service.py}}
```

### Step 2 — `src/swarm/controller/resource_allocator.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/controller/resource_allocator.py}}
```

### Step 3 — `tests/controller/v23_harness.py` (create, exactly; shared helper, not a test module)
```python
{{FILE:tests/controller/v23_harness.py}}
```

### Step 4 — `tests/controller/test_v23_service.py` (create, exactly)
```python
{{FILE:tests/controller/test_v23_service.py}}
```

### Step 5 — `tests/controller/test_v23_pathological.py` (create, exactly)
```python
{{FILE:tests/controller/test_v23_pathological.py}}
```

### Step 6 — `tests/integration/db/test_v23_service_restart_sql.py` (create, exactly)
```python
{{FILE:tests/integration/db/test_v23_service_restart_sql.py}}
```

### Step 7 — run
```bash
uv run pytest tests/controller/test_v23_service.py tests/controller/test_v23_pathological.py -q   # 17 passed
uv run pytest tests/controller -q
```
Ruff sorts `from tests.controller.v23_harness import …` **before** the `swarm` imports, because `tests/controller` has no `__init__.py`. Keep that order; run `uv run ruff check --fix tests/controller` if you retyped it.

If a dependency's function signature differs from what `service.py` calls, the base has changed shape: STOP (S4, section 10). The calls in question are `DispatchIntentService(store, reserve=, release=, clock=, ttl_seconds=)`, `select_next(..., now=, config=, resource_available=)`, `apply_selection(..., sequence=)` and `SchedulerEpochService.acquire/renew/require_current/current`.

### Section-5 acceptance
- [ ] All 11 ART pathological cases pass (`test_01` … `test_11`), each named after its ART bullet.
- [ ] With equal weights the share is within ±15% after 200 decisions; with weights 3:1 the share is within ±15% of 75% and the light project is never starved.
- [ ] Every decision (admit, defer, idle, or deny for a stale site) has exactly one receipt with a monotonic `sequence`; fenced non-holders write none.
- [ ] Restart on PostgreSQL preserves credit (positive side clamped), expires the crashed intent, releases its reservation, and the new holder gets epoch 2.
- [ ] The legacy `ResourceAllocator` path is unchanged; with `scheduler=` it produces an `admit` receipt.
