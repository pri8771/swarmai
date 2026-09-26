**Goal.** Make scheduler state durable: a PostgreSQL implementation of the `SchedulingStore` protocol (in `src/swarm/contracts/v23.py`) that behaves exactly like `InMemorySchedulingStore` (`src/swarm/scheduling/memory_store.py`, from SW-W0-S2). Tables `v23_project_queue_state`, `v23_mission_queue_state`, `v23_scheduler_receipts` and `v23_dispatch_intents` already exist (migration `a23opsplatform0001`).

**Versioning rule (must match memory store):** `expected_version=None` inserts (stored version 1) and raises `StaleVersionError` if the key exists. Otherwise the stored version must equal `expected_version`, and the new stored version is `expected_version + 1`. Updates lock the row (`SELECT … FOR UPDATE`) before comparing. DB unique-constraint violations become `StaleVersionError`.

The code below was compiled and run against Postgres 16 on `dev + SW-W0-S2` (9 passed, including a 4-thread race with exactly one winner). Paste it **exactly**.

### Step 1 — `src/swarm/scheduling/store.py` (create, exactly)
```python
{{FILE:src/swarm/scheduling/store.py}}
```

### Step 2 — `tests/integration/db/test_v23_store_sql.py` (create, exactly)
Each behavior test runs against **both** stores (parametrized), which proves they are equivalent.
```python
{{FILE:tests/integration/db/test_v23_store_sql.py}}
```

### Step 3 — run
```bash
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s2 OWNER swarm;" || true
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s2 uv run pytest tests/integration/db/test_v23_store_sql.py -q -m integration   # 9 passed
```
This session has no offline test, so the integration run is **required**. If Postgres cannot run at all, STOP (S3, section 10); PRs stay draft.

### Section-5 acceptance
- [ ] 9 integration tests pass (4 behaviors × 2 stores + 1 race test).
- [ ] `SqlSchedulingStore` satisfies the `SchedulingStore` protocol (mypy clean).
- [ ] No change to `models.py` or migrations.
